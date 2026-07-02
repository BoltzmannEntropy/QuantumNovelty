"""quantum_scout skill.

SS-like novelty scouting for QuantumNovelty across quantum-computing subjects,
not only VQE/Pareto ansatz discovery. This skill composes existing QN building
blocks instead of reimplementing them:

- literature_surfacer for live literature and baseline catalogs
- quantum_kb for run-local source indexing and exact quote substantiation
- common LLM wrapper for optional idea synthesis
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))

from llm import call_llm, write_backend_marker  # noqa: E402
from quantum_kb import (  # noqa: E402
    build_index,
    create_kb,
    ingest_documents,
    parse_kb_ids,
    search_kbs,
    slugify,
    substantiate_claims,
    write_search_outputs,
    write_substantiation_outputs,
)


IDEA_PROMPT = """# quantum_scout - idea synthesis

You are scouting quantum-computing research ideas across the full field:
algorithms, complexity, simulation, error correction, fault tolerance,
hardware, control, compilers, verification, quantum ML, sensing, networking,
cryptography, benchmarking, and quantum-inspired methods. Do not assume the
topic is about VQE, chemistry, ansatz design, or Pareto fronts unless the topic
explicitly says so.

Produce recommended novel research avenues that are specific enough to test,
audit, and compare against recent literature.

## Topic
{topic}

## Literature synthesis
{literature}

## Retrieved source quotes
{quotes}

Return exactly {n} ideas as one fenced JSON block:

```json
{{
  "ideas": [
    {{
      "title": "short idea title",
      "hypothesis": "one falsifiable hypothesis",
      "novelty_claim": "what would be new relative to the literature",
      "risk": "main prior-art or feasibility risk",
      "test": "minimal empirical/theoretical test",
      "why_recommended": "why this avenue should be prioritized",
      "venue_fit": "likely venue/community fit"
    }}
  ]
}}
```

Do not invent citations. If quote evidence is thin, say so in the risk field.
Prefer avenues that can be substantiated, falsified, and scoped into a paper.
"""


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _copy_if_present(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _run_literature(args: argparse.Namespace, outdir: Path) -> dict[str, Any]:
    lit_dir = outdir / "global_literature"
    lit_dir.mkdir(parents=True, exist_ok=True)
    if args.no_live_literature:
        payload = {
            "topic": args.topic,
            "n_total": 0,
            "n_deduped": 0,
            "per_source_status": {"offline": "skipped by --no-live-literature"},
            "cards": [],
        }
        _write_json(lit_dir / "candidates.json", payload)
        _write_json(lit_dir / "baseline_catalog.json", {"rows": []})
        (lit_dir / "synthesis.md").write_text(
            "# Literature Surface\n\n"
            "Live literature retrieval was skipped by `--no-live-literature`.\n",
            encoding="utf-8",
        )
        return payload

    cmd = [
        "bash",
        str(ROOT / "skills" / "literature_surfacer" / "run.sh"),
        "--topic",
        args.topic,
        "--outdir",
        str(lit_dir),
        "--llm",
        args.llm,
        "--n",
        str(args.literature_n),
        "--sources",
        args.sources,
    ]
    if args.hamiltonian_id:
        cmd.extend(["--hamiltonian-id", args.hamiltonian_id])
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
    (lit_dir / "_literature_stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (lit_dir / "_literature_stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        payload = {
            "topic": args.topic,
            "n_total": 0,
            "n_deduped": 0,
            "per_source_status": {"literature_surfacer": f"failed rc={proc.returncode}"},
            "cards": [],
        }
        _write_json(lit_dir / "candidates.json", payload)
        _write_json(lit_dir / "baseline_catalog.json", {"rows": []})
        (lit_dir / "synthesis.md").write_text(
            "# Literature Surface Failed\n\n"
            f"`literature_surfacer` exited with rc={proc.returncode}. "
            "See `_literature_stderr.txt`.\n",
            encoding="utf-8",
        )
        return payload
    return _read_json(lit_dir / "candidates.json", {"cards": [], "per_source_status": {}})


def _safe_arxiv_id(value: str) -> str:
    value = value.strip().replace("/", "_")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unknown"


def _arxiv_search(query: str, max_results: int) -> list[dict[str, str]]:
    qs = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
        }
    )
    req = urllib.request.Request(
        f"https://export.arxiv.org/api/query?{qs}",
        headers={"User-Agent": "QuantumNovelty/0.1 quantum_scout"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return []
    entries = re.findall(r"<entry>(.*?)</entry>", raw, re.DOTALL)
    out: list[dict[str, str]] = []
    for entry in entries:
        title = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        summary = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        published = re.search(r"<published>(.*?)</published>", entry)
        arxiv_id = re.search(r"<id>https?://arxiv\.org/abs/(.*?)(?:v\d+)?</id>", entry)
        authors = re.findall(r"<author><name>(.*?)</name>", entry)
        if not arxiv_id:
            continue
        aid = arxiv_id.group(1).strip()
        out.append(
            {
                "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else aid,
                "authors": "; ".join(a.strip() for a in authors if a.strip()),
                "year": published.group(1)[:4] if published else "",
                "abstract": re.sub(r"\s+", " ", summary.group(1)).strip() if summary else "",
                "arxiv_id": aid,
                "url": f"https://arxiv.org/abs/{aid}",
                "pdf_url": f"https://arxiv.org/pdf/{aid}.pdf",
                "source": "arxiv_corpus",
            }
        )
    return out


def _download_arxiv_corpus(args: argparse.Namespace, outdir: Path) -> tuple[list[Path], dict[str, Any]]:
    corpus = outdir / "arxiv_corpus"
    pdf_dir = corpus / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    status: dict[str, Any] = {
        "enabled": not args.no_arxiv_corpus and not args.no_live_literature,
        "requested": args.arxiv_max_downloads,
        "downloaded": 0,
        "papers": [],
        "errors": [],
    }
    if args.no_live_literature:
        status["reason"] = "skipped by --no-live-literature"
        _write_json(corpus / "status.json", status)
        _write_json(corpus / "references.json", [])
        return [], status
    if args.no_arxiv_corpus or args.arxiv_max_downloads <= 0:
        status["reason"] = "disabled"
        _write_json(corpus / "status.json", status)
        _write_json(corpus / "references.json", [])
        return [], status

    refs = _arxiv_search(args.topic, max(args.arxiv_max_downloads, 1))
    downloaded: list[Path] = []
    for ref in refs[: args.arxiv_max_downloads]:
        aid = ref["arxiv_id"]
        dest = pdf_dir / f"{_safe_arxiv_id(aid)}.pdf"
        try:
            req = urllib.request.Request(
                ref["pdf_url"],
                headers={"User-Agent": "QuantumNovelty/0.1 quantum_scout"},
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                dest.write_bytes(resp.read())
            ref["pdf_path"] = str(dest)
            downloaded.append(dest)
            status["downloaded"] += 1
            time.sleep(0.25)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            status["errors"].append({"arxiv_id": aid, "error": str(exc)})
    status["papers"] = refs
    _write_json(corpus / "references.json", refs)
    _write_json(corpus / "status.json", status)
    return downloaded, status


def _build_source_kb(
    args: argparse.Namespace,
    outdir: Path,
    extra_sources: list[Path],
) -> tuple[list[str], Path, dict[str, Any]]:
    kb_root = Path(args.kb_root).expanduser().resolve() if args.kb_root else outdir / "quantum-kb"
    existing_ids = parse_kb_ids(args.kb, kb_root=kb_root) if args.kb else []
    sources = list(args.source_file) + list(extra_sources)
    status: dict[str, Any] = {
        "kb_root": str(kb_root),
        "existing_kb_ids": existing_ids,
        "source_files": [str(p) for p in sources],
        "created_kb_id": None,
        "ingest": [],
        "index": None,
        "errors": [],
    }
    kb_ids = list(existing_ids)
    if sources:
        kb_id = "scout_sources"
        try:
            create_kb(
                kb_id,
                "Scout Sources",
                "Run-local source KB for quantum_scout quote substantiation.",
                kb_root=kb_root,
                make_default=False,
            )
        except ValueError:
            pass
        status["created_kb_id"] = kb_id
        for src in sources:
            try:
                status["ingest"].append(
                    ingest_documents(kb_id, src, kb_root=kb_root, refresh=True)
                )
            except Exception as exc:  # keep scout resilient to one bad source
                status["errors"].append({"source": str(src), "error": str(exc)})
        try:
            status["index"] = build_index(kb_id, kb_root=kb_root, purge=True)
            if kb_id not in kb_ids:
                kb_ids.append(kb_id)
        except Exception as exc:
            status["errors"].append({"stage": "index", "error": str(exc)})

    source_kb_dir = outdir / "source_kb"
    source_kb_dir.mkdir(parents=True, exist_ok=True)
    _write_json(source_kb_dir / "status.json", status)
    return kb_ids, kb_root, status


def _search_quote_context(
    topic: str,
    kb_ids: list[str],
    kb_root: Path,
    outdir: Path,
    max_results: int,
) -> tuple[str, dict[str, str] | None]:
    if not kb_ids:
        return "_No KB was provided or built for this scout run._", None
    results = search_kbs(
        topic,
        kb_ids,
        kb_root=kb_root,
        max_results=max_results,
        max_words=90,
        max_per_source=3,
    )
    paths = write_search_outputs(
        results,
        query=topic,
        kb_ids=kb_ids,
        kb_root=kb_root,
        outdir=outdir / "source_kb",
    )
    if not results:
        return "_No source quote matched the topic above threshold._", paths
    lines = []
    for result in results:
        lines.append(f'- "{result.quote}" ({result.citation_short})')
    return "\n".join(lines), paths


def _topic_profile(topic: str) -> dict[str, str]:
    lower = topic.lower()
    profiles = [
        (
            ("error correction", "qec", "surface code", "decoder", "fault tolerance", "fault-tolerant"),
            {
                "area": "quantum error correction and fault tolerance",
                "object": "decoder, syndrome, and noise-model assumptions",
                "baseline": "known decoder thresholds, circuit-level noise models, and resource estimates",
                "venue": "Quantum, PRX Quantum, npj Quantum Information, fault-tolerance workshops",
            },
        ),
        (
            ("superconduct", "qubit", "calibration", "control", "chip", "hardware", "transmon"),
            {
                "area": "quantum hardware and control",
                "object": "device-calibration, control-stack, and fabrication constraints",
                "baseline": "manual calibration, Bayesian optimization, model-based control, and hardware drift baselines",
                "venue": "PRX Quantum, npj Quantum Information, Quantum Science and Technology",
            },
        ),
        (
            ("qml", "quantum machine learning", "kernel", "classification", "learning", "neural"),
            {
                "area": "quantum machine learning",
                "object": "data-regime, trainability, kernel, and generalization assumptions",
                "baseline": "classical ML, quantum kernel, variational QML, and ablation baselines",
                "venue": "Quantum Machine Intelligence, NeurIPS/ICML workshops, PRX Quantum",
            },
        ),
        (
            ("compile", "compiler", "transpile", "routing", "mapping", "circuit optimization"),
            {
                "area": "quantum compilation and verification",
                "object": "routing, equivalence, noise-aware optimization, and compilation guarantees",
                "baseline": "Qiskit/tket/Cirq transpilation, ZX simplification, and hardware-aware mapping",
                "venue": "ACM TQC, QCE, Quantum, compiler workshops",
            },
        ),
        (
            ("simulation", "hamiltonian", "trotter", "qubitization", "qsp", "lcu", "qdrift"),
            {
                "area": "quantum simulation algorithms",
                "object": "resource estimates, error budgets, oracle assumptions, and model regimes",
                "baseline": "Trotter-Suzuki, qDRIFT, LCU/Taylor, qubitization, and QSP baselines",
                "venue": "PRX Quantum, Quantum, Physical Review A, npj Quantum Information",
            },
        ),
        (
            ("network", "internet", "repeater", "entanglement distribution", "qkd"),
            {
                "area": "quantum networks and cryptography",
                "object": "entanglement distribution, repeater protocols, trust assumptions, and key-rate regimes",
                "baseline": "standard QKD, repeater, routing, and finite-key analyses",
                "venue": "Quantum, npj Quantum Information, IEEE quantum communications venues",
            },
        ),
        (
            ("sensing", "metrology", "sensor", "magnetometry", "clock"),
            {
                "area": "quantum sensing and metrology",
                "object": "resource accounting, noise model, readout, and practical sensitivity claims",
                "baseline": "standard quantum limit, squeezed/entangled probes, and classical sensor baselines",
                "venue": "PRX Quantum, Physical Review Applied, Quantum Science and Technology",
            },
        ),
    ]
    for keys, profile in profiles:
        if any(key in lower for key in keys):
            return profile
    return {
        "area": "quantum computing",
        "object": "assumptions, resource claims, implementation constraints, and evidence gaps",
        "baseline": "best-known quantum and classical baselines in the retrieved literature",
        "venue": "Quantum, PRX Quantum, npj Quantum Information, QCE, or field-specific workshops",
    }


def _fallback_ideas(topic: str, cards: list[dict[str, Any]], n: int) -> list[dict[str, str]]:
    titles = [str(c.get("title", "")).strip() for c in cards if c.get("title")]
    seeds = titles[: max(1, min(len(titles), n))] or [topic]
    profile = _topic_profile(topic)
    templates = [
        (
            "Quote-grounded white-space map for {area}",
            "A quote-grounded literature map can identify which assumptions in {topic} are settled, weakly supported, or untested.",
            "The novelty is a reproducible white-space ledger for {object}, separating genuine open problems from rediscovery.",
            "The corpus may overrepresent easy-to-retrieve papers and miss recent workshop or hardware-specific work.",
            "Build a source KB, extract exact claim-level quotes, and mark each proposed avenue as supported, contradicted, or unsubstantiated.",
            "Prioritize first because it reduces hallucinated novelty before experiment or theory spend.",
        ),
        (
            "Regime-bound benchmark for {area}",
            "A regime-bound benchmark can reveal whether {topic} holds only under specific assumptions about {object}.",
            "The contribution would be a scoped benchmark that makes the hidden operating regime explicit against {baseline}.",
            "The idea is publishable only if the benchmark avoids cherry-picked regimes and includes negative cases.",
            "Define two favorable and two adversarial regimes, pre-register metrics, and compare against the strongest available baselines.",
            "Prioritize when the literature has many claims but weak apples-to-apples comparisons.",
        ),
        (
            "Failure-mode atlas for {area}",
            "The strongest new avenue in {topic} may be an honest map of where current methods fail.",
            "The novelty is a failure-mode atlas for {object} with concrete boundary conditions for when the approach should not be used.",
            "A negative result needs tight controls or it will read as an implementation artifact.",
            "Define failure regimes from the literature, reproduce at least one known baseline, and report null results as first-class outputs.",
            "Prioritize when positive claims look saturated but operational limits are underdocumented.",
        ),
        (
            "Assumption-swap test for {area}",
            "Swapping one dominant assumption in {topic} can expose whether the claimed advantage depends on an unrealistic model.",
            "The novelty is a controlled assumption-sensitivity study over {object}, not another unconstrained method proposal.",
            "The study may be too narrow unless the assumption is visibly load-bearing in recent papers.",
            "Run a paired analysis with the standard assumption and a more realistic alternative, then audit which conclusions survive.",
            "Prioritize when papers cite the same idealized assumption without quantifying its load-bearing role.",
        ),
    ]
    ideas: list[dict[str, str]] = []
    i = 0
    while len(ideas) < n:
        seed = seeds[i % len(seeds)]
        tpl = templates[i % len(templates)]
        fmt = {
            "seed": seed,
            "topic": topic,
            "area": profile["area"],
            "object": profile["object"],
            "baseline": profile["baseline"],
        }
        ideas.append(
            {
                "idea_id": f"QI{len(ideas) + 1:03d}",
                "recommendation_rank": len(ideas) + 1,
                "title": tpl[0].format(**fmt),
                "hypothesis": tpl[1].format(**fmt),
                "novelty_claim": tpl[2].format(**fmt),
                "risk": tpl[3].format(**fmt),
                "test": tpl[4].format(**fmt),
                "why_recommended": tpl[5].format(**fmt),
                "venue_fit": profile["venue"],
            }
        )
        i += 1
    return ideas


def _parse_ideas(text: str, topic: str, cards: list[dict[str, Any]], n: int) -> list[dict[str, str]]:
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    for block in blocks + [text]:
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue
        rows = payload.get("ideas") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            continue
        ideas = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            ideas.append(
                {
                    "idea_id": f"QI{len(ideas) + 1:03d}",
                    "recommendation_rank": len(ideas) + 1,
                    "title": str(row.get("title", "")).strip() or f"Quantum scout idea {len(ideas) + 1}",
                    "hypothesis": str(row.get("hypothesis", "")).strip(),
                    "novelty_claim": str(row.get("novelty_claim", "")).strip(),
                    "risk": str(row.get("risk", "")).strip(),
                    "test": str(row.get("test", "")).strip(),
                    "why_recommended": str(row.get("why_recommended", "")).strip(),
                    "venue_fit": str(row.get("venue_fit", "")).strip(),
                }
            )
            if len(ideas) >= n:
                break
        if ideas:
            return ideas
    return _fallback_ideas(topic, cards, n)


def _generate_ideas(
    args: argparse.Namespace,
    cards: list[dict[str, Any]],
    literature: str,
    quote_context: str,
    outdir: Path,
) -> list[dict[str, str]]:
    if args.no_llm:
        return _fallback_ideas(args.topic, cards, args.n)
    prompt = IDEA_PROMPT.format(
        topic=args.topic,
        literature=literature[:12000],
        quotes=quote_context[:8000],
        n=args.n,
    )
    try:
        result = call_llm(prompt, backend=args.llm, timeout=args.timeout)
    except RuntimeError as exc:
        (outdir / "_idea_synthesis_error.txt").write_text(str(exc), encoding="utf-8")
        return _fallback_ideas(args.topic, cards, args.n)
    (outdir / "_idea_synthesis_raw.md").write_text(result.text, encoding="utf-8")
    write_backend_marker(outdir, result)
    return _parse_ideas(result.text, args.topic, cards, args.n)


def _idea_claims(ideas: list[dict[str, str]]) -> list[str]:
    claims = []
    for idea in ideas:
        claim = idea.get("novelty_claim") or idea.get("hypothesis") or idea.get("title")
        claims.append(claim)
    return claims


def _write_claim_ledger(outdir: Path, ideas: list[dict[str, str]], dossier: dict[str, Any] | None) -> None:
    by_idx: dict[int, dict[str, Any]] = {}
    if dossier:
        for idx, claim in enumerate(dossier.get("claims", [])):
            by_idx[idx] = claim

    rows = []
    for idx, idea in enumerate(ideas):
        ev = by_idx.get(idx, {})
        rows.append(
            {
                "idea_id": idea["idea_id"],
                "title": idea["title"],
                "claim": idea.get("novelty_claim") or idea.get("hypothesis"),
                "recommendation_rank": idea.get("recommendation_rank", idx + 1),
                "status": ev.get("status", "not_checked"),
                "evidence_count": ev.get("evidence_count", 0),
                "why_recommended": idea.get("why_recommended", ""),
                "venue_fit": idea.get("venue_fit", ""),
                "risk": idea.get("risk", ""),
            }
        )
    _write_json(outdir / "claim_ledger.json", {"claims": rows})
    with (outdir / "claim_ledger.md").open("w", encoding="utf-8") as f:
        f.write("# Quantum Scout Claim Ledger\n\n")
        for row in rows:
            f.write(f"## {row['idea_id']} - {row['title']}\n\n")
            f.write(f"**Recommendation rank:** {row['recommendation_rank']}\n\n")
            f.write(f"**Claim:** {row['claim']}\n\n")
            f.write(f"**Status:** {row['status']} ({row['evidence_count']} quotes)\n\n")
            f.write(f"**Why recommended:** {row['why_recommended']}\n\n")
            f.write(f"**Venue fit:** {row['venue_fit']}\n\n")
            f.write(f"**Risk:** {row['risk']}\n\n")


def _references_from_cards(cards: list[dict[str, Any]], dossier: dict[str, Any] | None) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for card in cards:
        title = str(card.get("title", "")).strip()
        if not title:
            continue
        key = str(card.get("doi") or card.get("arxiv_id") or title).lower()
        if key in seen:
            continue
        seen.add(key)
        refs.append(
            {
                "title": title,
                "authors": "; ".join(str(a) for a in card.get("authors", [])[:6]),
                "year": str(card.get("year", "")),
                "venue": str(card.get("venue", "")),
                "doi": str(card.get("doi") or ""),
                "arxiv_id": str(card.get("arxiv_id") or ""),
                "url": str(card.get("url") or ""),
                "source": str(card.get("source", "")),
            }
        )
    if dossier:
        for claim in dossier.get("claims", []):
            for item in claim.get("evidence", []):
                citation = str(item.get("citation", "")).strip()
                if not citation or citation.lower() in seen:
                    continue
                seen.add(citation.lower())
                refs.append(
                    {
                        "title": str(item.get("title", "")),
                        "authors": str(item.get("author", "")),
                        "year": str(item.get("year", "")),
                        "venue": "Quantum KB",
                        "doi": "",
                        "arxiv_id": "",
                        "url": str(item.get("source_path", "")),
                        "source": "quantum_kb",
                        "citation": citation,
                    }
                )
    return refs


def _bib_key(ref: dict[str, str], idx: int) -> str:
    author = re.sub(r"[^A-Za-z0-9]+", "", (ref.get("authors") or "ref").split(";")[0]) or "ref"
    year = re.sub(r"[^0-9]+", "", ref.get("year", "")) or "nd"
    return f"{author[:18]}{year}_{idx}"


def _write_references(outdir: Path, refs: list[dict[str, str]]) -> None:
    _write_json(outdir / "scout_references.json", {"references": refs})
    with (outdir / "scout_references.bib").open("w", encoding="utf-8") as f:
        for idx, ref in enumerate(refs, 1):
            key = _bib_key(ref, idx)
            f.write(f"@misc{{{key},\n")
            f.write(f"  title = {{{ref.get('title', '')}}},\n")
            if ref.get("authors"):
                f.write(f"  author = {{{ref.get('authors', '')}}},\n")
            if ref.get("year"):
                f.write(f"  year = {{{ref.get('year', '')}}},\n")
            if ref.get("url"):
                f.write(f"  url = {{{ref.get('url', '')}}},\n")
            if ref.get("doi"):
                f.write(f"  doi = {{{ref.get('doi', '')}}},\n")
            if ref.get("arxiv_id"):
                f.write(f"  eprint = {{{ref.get('arxiv_id', '')}}},\n")
                f.write("  archivePrefix = {arXiv},\n")
            f.write("}\n\n")


def _write_report(
    outdir: Path,
    args: argparse.Namespace,
    ideas: list[dict[str, str]],
    lit_payload: dict[str, Any],
    dossier: dict[str, Any] | None,
    refs: list[dict[str, str]],
    pdf_kb_only: bool,
) -> None:
    payload = {
        "topic": args.topic,
        "pdf_kb_only": pdf_kb_only,
        "idea_count": len(ideas),
        "ideas": ideas,
        "literature": {
            "n_total": lit_payload.get("n_total", 0),
            "n_deduped": lit_payload.get("n_deduped", 0),
            "per_source_status": lit_payload.get("per_source_status", {}),
        },
        "claim_evidence": dossier,
        "reference_count": len(refs),
    }
    _write_json(outdir / "scout_report.json", payload)
    with (outdir / "scout_report.md").open("w", encoding="utf-8") as f:
        title = "Quantum PDF KB Scout" if pdf_kb_only else "Quantum Novelty Scout Report"
        f.write(f"# {title}\n\n")
        f.write(f"**Topic:** {args.topic}\n\n")
        f.write("## Literature Surface\n\n")
        f.write(f"- Total hits: {lit_payload.get('n_total', 0)}\n")
        f.write(f"- Deduped cards: {lit_payload.get('n_deduped', 0)}\n")
        for src, status in (lit_payload.get("per_source_status") or {}).items():
            f.write(f"- {src}: {status}\n")
        if pdf_kb_only:
            f.write("\n## Mode\n\nPDF/KB-only mode was requested; idea generation was skipped.\n\n")
        else:
            f.write("\n## Candidate Ideas\n\n")
            for idea in ideas:
                f.write(
                    f"### {idea['recommendation_rank']}. "
                    f"{idea['idea_id']} - {idea['title']}\n\n"
                )
                f.write(f"**Hypothesis:** {idea.get('hypothesis', '')}\n\n")
                f.write(f"**Novelty claim:** {idea.get('novelty_claim', '')}\n\n")
                f.write(f"**Why recommended:** {idea.get('why_recommended', '')}\n\n")
                f.write(f"**Venue fit:** {idea.get('venue_fit', '')}\n\n")
                f.write(f"**Risk:** {idea.get('risk', '')}\n\n")
                f.write(f"**Minimal test:** {idea.get('test', '')}\n\n")
        f.write("## Quote Substantiation\n\n")
        if not dossier:
            f.write("_No KB quote substantiation was run._\n\n")
        else:
            for claim in dossier.get("claims", []):
                f.write(f"### {claim['claim_id']} - {claim['status']}\n\n")
                f.write(f"{claim['claim']}\n\n")
                for item in claim.get("evidence", []):
                    f.write(f"> {item.get('quote', '')}\n\n")
                    f.write(f"Citation: {item.get('citation', '')}\n\n")
        f.write("## References\n\n")
        for ref in refs:
            citation = ref.get("citation")
            if citation:
                f.write(f"- {citation}\n")
            else:
                parts = [ref.get("authors", ""), ref.get("year", ""), ref.get("title", ""), ref.get("venue", "")]
                f.write("- " + ". ".join(p for p in parts if p) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--source-file", action="append", type=Path, default=[])
    ap.add_argument("--kb", default=None)
    ap.add_argument("--kb-root", default=None)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--literature-n", type=int, default=10)
    ap.add_argument("--sources", default="crossref,arxiv,semantic_scholar,serper")
    ap.add_argument("--hamiltonian-id", default=None)
    ap.add_argument("--quotes-per-claim", type=int, default=3)
    ap.add_argument("--quote-context-results", type=int, default=6)
    ap.add_argument("--arxiv-max-downloads", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--no-arxiv-corpus", action="store_true")
    ap.add_argument("--pdf-kb-only", action="store_true")
    ap.add_argument("--no-live-literature", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    lit_payload = _run_literature(args, args.outdir)
    cards = list(lit_payload.get("cards") or [])
    literature = (args.outdir / "global_literature" / "synthesis.md").read_text(
        encoding="utf-8", errors="ignore"
    )

    arxiv_pdfs, arxiv_status = _download_arxiv_corpus(args, args.outdir)
    kb_ids, kb_root, kb_status = _build_source_kb(args, args.outdir, arxiv_pdfs)
    quote_context, search_paths = _search_quote_context(
        args.topic,
        kb_ids,
        kb_root,
        args.outdir,
        args.quote_context_results,
    )

    ideas = [] if args.pdf_kb_only else _generate_ideas(
        args, cards, literature, quote_context, args.outdir
    )
    dossier = None
    substantiation_paths = None
    if kb_ids and not args.pdf_kb_only:
        dossier = substantiate_claims(
            _idea_claims(ideas),
            kb_ids,
            kb_root=kb_root,
            quotes_per_claim=args.quotes_per_claim,
        )
        substantiation_paths = write_substantiation_outputs(
            dossier,
            outdir=args.outdir / "substantiation",
        )

    arxiv_refs = [p for p in arxiv_status.get("papers", []) if isinstance(p, dict)]
    refs = _references_from_cards(cards + arxiv_refs, dossier)
    _write_references(args.outdir, refs)
    _write_claim_ledger(args.outdir, ideas, dossier)
    _write_report(args.outdir, args, ideas, lit_payload, dossier, refs, args.pdf_kb_only)

    manifest = {
        "topic": args.topic,
        "mode": "quantum_scout",
        "ss_parity_features": [
            "topic-driven scout entrypoint",
            "multi-source literature surface",
            "structured prior-art/baseline catalog",
            "bounded arXiv PDF acquisition",
            "broad quantum-subject avenue recommendation",
            "run-local source KB",
            "PDF/KB-only acquisition mode",
            "word-for-word quote substantiation",
            "references",
            "claim ledger",
            "manifest",
        ],
        "global_literature": str(args.outdir / "global_literature"),
        "source_kb": str(args.outdir / "source_kb"),
        "kb_root": str(kb_root),
        "kb_ids": kb_ids,
        "kb_status": kb_status,
        "arxiv_corpus": arxiv_status,
        "search_outputs": search_paths,
        "substantiation_outputs": substantiation_paths,
        "outputs": {
            "scout_report": str(args.outdir / "scout_report.md"),
            "scout_report_json": str(args.outdir / "scout_report.json"),
            "claim_ledger": str(args.outdir / "claim_ledger.md"),
            "references_json": str(args.outdir / "scout_references.json"),
            "references_bib": str(args.outdir / "scout_references.bib"),
            "arxiv_corpus": str(args.outdir / "arxiv_corpus"),
        },
    }
    _write_json(args.outdir / "scout_manifest.json", manifest)

    substantiated = 0
    partial = 0
    if dossier:
        for claim in dossier.get("claims", []):
            substantiated += claim.get("status") == "substantiated"
            partial += claim.get("status") == "partially_substantiated"
    _write_json(
        args.outdir / "scout_quality.json",
        {
            "idea_count": len(ideas),
            "reference_count": len(refs),
            "kb_ids": kb_ids,
            "claim_count": len(dossier.get("claims", [])) if dossier else 0,
            "substantiated_claims": substantiated,
            "partially_substantiated_claims": partial,
            "live_literature": not args.no_live_literature,
            "arxiv_downloaded": arxiv_status.get("downloaded", 0),
            "pdf_kb_only": args.pdf_kb_only,
            "llm_idea_synthesis": not args.no_llm,
        },
    )

    print(
        "quantum_scout: "
        f"ideas={len(ideas)} refs={len(refs)} "
        f"kb_ids={','.join(kb_ids) if kb_ids else 'none'} -> {args.outdir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
