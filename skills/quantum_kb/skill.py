"""quantum_kb skill driver.

Creates, indexes, and queries local quantum knowledge bases for RAG. No LLM,
network, server, or embedding model is required.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))

from quantum_kb import (  # noqa: E402
    append_perspective_appendices,
    bootstrap_quantum_core,
    build_index,
    build_deterministic_perspective,
    build_perspective_claim_audit,
    build_perspective_prompt,
    citations_from_quote_items,
    create_kb,
    get_quantum_kb_path,
    ingest_documents,
    list_kbs,
    load_kb,
    parse_kb_ids,
    render_perspective_quote_packet,
    search_kbs,
    select_perspective_quotes,
    slugify,
    substantiate_claims,
    verify_perspective_quote_fidelity,
    write_search_outputs,
    write_substantiation_outputs,
)
from llm import call_llm, write_backend_marker  # noqa: E402
from paper_io import load_paper_text  # noqa: E402


CLAIM_RE = re.compile(
    r"\b("
    r"we|this paper|our|the method|the algorithm|the framework|results|"
    r"experiments|evaluation|benchmark|simulation|approach"
    r")\b.*\b("
    r"show|shows|demonstrate|demonstrates|achieve|achieves|outperform|"
    r"outperforms|improve|improves|reduce|reduces|novel|new|first|"
    r"accurate|chemical accuracy|dominates|pareto|scales|advantage"
    r")\b",
    re.IGNORECASE,
)
NUMERIC_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:x|%|mha|ha|ev|qubits?|gates?|cnots?|shots?|seeds?)\b", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _write_operation(outdir: Path | None, payload: dict) -> None:
    if not outdir:
        return
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "operation.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _default_search_outdir(query: str) -> Path:
    return ROOT / "runs" / "quantum_kb_search" / slugify(query, max_len=60)


def _clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip("`*_# ")
    return text


def _extract_claims_from_paper(text: str, max_claims: int) -> list[str]:
    candidates: list[tuple[int, str]] = []
    for raw in SENTENCE_RE.split(text):
        sent = _clean_sentence(raw)
        if len(sent) < 40 or len(sent) > 450:
            continue
        score = 0
        if CLAIM_RE.search(sent):
            score += 3
        if NUMERIC_RE.search(sent):
            score += 2
        if any(term in sent.lower() for term in (
            "vqe", "ansatz", "hamiltonian", "qaoa", "surface code",
            "quantum error correction", "trotter", "qml",
        )):
            score += 1
        if score <= 0:
            continue
        candidates.append((score, sent))
    seen: set[str] = set()
    claims: list[str] = []
    for _, sent in sorted(candidates, key=lambda item: (-item[0], text.find(item[1]))):
        key = sent.lower()
        if key in seen:
            continue
        seen.add(key)
        claims.append(sent)
        if len(claims) >= max_claims:
            break
    return claims


def _read_claims_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
        if isinstance(payload, list):
            return [str(x) for x in payload]
        if isinstance(payload, dict):
            claims = payload.get("claims", [])
            if isinstance(claims, list):
                out = []
                for item in claims:
                    if isinstance(item, dict):
                        out.append(str(item.get("claim", item.get("text", ""))))
                    else:
                        out.append(str(item))
                return out
        raise ValueError(f"unsupported claims JSON shape: {path}")
    if path.suffix.lower() == ".jsonl":
        out = []
        for line in text.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(str(obj.get("claim", obj.get("text", ""))))
            else:
                out.append(str(obj))
        return out
    return [
        line.strip().lstrip("-*0123456789. ").strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _collect_review_claims(args: argparse.Namespace) -> tuple[list[str], str]:
    claims = list(args.claim or [])
    paper_text = ""
    if args.claims_file:
        claims.extend(_read_claims_file(args.claims_file))
    if args.paper:
        paper_text = load_paper_text(args.paper)
        if not claims:
            claims.extend(_extract_claims_from_paper(paper_text, args.max_claims))
    if args.question and not claims:
        claims.append(args.question)
    claims = [claim.strip() for claim in claims if claim and claim.strip()]
    return claims, paper_text


def _build_grounded_review_prompt(
    *,
    question: str,
    paper_text: str,
    dossier: dict,
) -> str:
    evidence_lines: list[str] = []
    for claim in dossier.get("claims", []):
        evidence_lines.append(f"{claim['claim_id']}: {claim['claim']}")
        if not claim.get("evidence"):
            evidence_lines.append("  - NO RETRIEVED QUOTE ABOVE THRESHOLD")
            continue
        for item in claim["evidence"]:
            evidence_lines.append(
                f"  - Quote: \"{item['quote']}\" ({item['citation_short']})"
            )
            evidence_lines.append(f"    Full citation: {item['citation']}")
            evidence_lines.append(
                f"    Source: {item['kb_id']} / {item['source_path']} / {item['chunk_id']}"
            )

    paper_block = ""
    if paper_text:
        paper_block = (
            "\n\n## Paper Under Review\n\n"
            "Use this only to understand what is being reviewed. Do not treat "
            "the paper's own assertions as external support.\n\n```\n"
            + paper_text[:120_000]
            + "\n```\n"
        )

    return (
        "# QuantumNovelty KB-Grounded Review\n\n"
        "You are writing an evidence-grounded quantum-computing review. "
        "Use only the retrieved word-for-word KB quotes below when "
        "substantiating or challenging claims. Every external-evidence "
        "sentence must cite the quote's inline citation. If the evidence is "
        "thin, say so explicitly. Do not invent citations, papers, page "
        "numbers, or quotations.\n\n"
        "## Review Question\n\n"
        f"{question or 'Assess the claims against the retrieved quantum KB evidence.'}\n\n"
        "## Required Output\n\n"
        "1. Verdict: substantiated / partially substantiated / unsupported.\n"
        "2. Claim-by-claim assessment with at least one quoted passage where available.\n"
        "3. Missing evidence and search gaps.\n"
        "4. Revision guidance: what the author should cite, qualify, or remove.\n\n"
        "## Retrieved Evidence\n\n"
        + "\n".join(evidence_lines)
        + paper_block
    )


def _deterministic_grounded_review(*, question: str, dossier: dict) -> str:
    counts = {
        "substantiated": 0,
        "partially_substantiated": 0,
        "unsubstantiated": 0,
    }
    for claim in dossier.get("claims", []):
        counts[claim.get("status", "unsubstantiated")] = (
            counts.get(claim.get("status", "unsubstantiated"), 0) + 1
        )
    if counts["unsubstantiated"] == 0 and counts["partially_substantiated"] == 0:
        verdict = "substantiated"
    elif counts["substantiated"] or counts["partially_substantiated"]:
        verdict = "partially substantiated"
    else:
        verdict = "unsupported"

    lines = [
        "# KB-Grounded Quantum Review",
        "",
        f"**Review question:** {question or 'Assess claims against the quantum KB.'}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Claim-by-Claim Evidence",
        "",
    ]
    for claim in dossier.get("claims", []):
        lines.append(f"### {claim['claim_id']} - {claim['status']}")
        lines.append("")
        lines.append(f"**Claim:** {claim['claim']}")
        lines.append("")
        evidence = claim.get("evidence", [])
        if not evidence:
            lines.append("No supporting KB quote met the retrieval threshold.")
            lines.append("")
            continue
        for item in evidence:
            lines.append(
                f"- \"{item['quote']}\" ({item['citation_short']})"
            )
            lines.append(f"  Citation: {item['citation']}")
            lines.append(
                f"  Source: `{item['kb_id']}:{item['source_path']}:{item['chunk_id']}`"
            )
        lines.append("")
    lines.extend([
        "## Review Guidance",
        "",
        "Use substantiated claims with the listed citations. Qualify partially "
        "substantiated claims, and remove or re-search unsupported claims before "
        "using them in a paper, review, or patent-facing argument.",
        "",
    ])
    return "\n".join(lines)


def cmd_list(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    rows = list_kbs(root)
    print(f"Quantum KB root: {root}")
    if not rows:
        print("No KBs registered. Run: quantum_kb/run.sh create --kb quantum_core")
        return 0
    print()
    print(f"{'kb_id':<24} {'status':<14} {'docs':>5} {'chunks':>7} name")
    print("-" * 80)
    for row in rows:
        print(
            f"{row.kb_id:<24} {row.status:<14} "
            f"{row.document_count:>5} {row.chunk_count:>7} {row.name}"
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    if args.kb:
        cfg = load_kb(args.kb, kb_root=root)
        payload = {
            "kb_id": cfg.kb_id,
            "name": cfg.name,
            "description": cfg.description,
            "status": cfg.status,
            "indexed_at": cfg.indexed_at,
            "documents_path": str(cfg.documents_path),
            "index_path": str(cfg.index_path),
            "manifest_path": str(cfg.manifest_path),
        }
    else:
        payload = {
            "kb_root": str(root),
            "knowledge_bases": [row.__dict__ for row in list_kbs(root)],
        }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    _write_operation(args.outdir, payload)
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    cfg = create_kb(
        args.kb,
        args.name,
        args.description or "",
        kb_root=root,
        make_default=args.default,
    )
    payload = {
        "created": True,
        "kb_root": str(root),
        "kb_id": cfg.kb_id,
        "documents_path": str(cfg.documents_path),
        "index_path": str(cfg.index_path),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    _write_operation(args.outdir, payload)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    payload = ingest_documents(args.kb, args.source, kb_root=root, refresh=args.refresh)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    _write_operation(args.outdir, payload)
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    payload = build_index(args.kb, kb_root=root, purge=args.purge)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    _write_operation(args.outdir, payload)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    kb_ids = parse_kb_ids(args.kb, kb_root=root)
    if not kb_ids:
        print(
            "ERROR: no KBs selected. Pass --kb or run bootstrap/create first.",
            file=sys.stderr,
        )
        return 2
    outdir = args.outdir or _default_search_outdir(args.query)
    results = search_kbs(
        args.query,
        kb_ids,
        kb_root=root,
        top_k=args.top_k,
        max_results=args.max_results,
        max_words=args.max_words,
        max_per_source=args.max_per_source,
        min_score=args.min_score,
    )
    paths = write_search_outputs(
        results,
        query=args.query,
        kb_ids=kb_ids,
        outdir=outdir,
        kb_root=root,
    )
    print(json.dumps({
        "query": args.query,
        "kb_ids": kb_ids,
        "result_count": len(results),
        "outdir": str(outdir),
        "artifacts": paths,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_substantiate(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    kb_ids = parse_kb_ids(args.kb, kb_root=root)
    if not kb_ids:
        print(
            "ERROR: no KBs selected. Pass --kb or run bootstrap/create first.",
            file=sys.stderr,
        )
        return 2
    claims = list(args.claim or [])
    if args.claims_file:
        claims.extend(_read_claims_file(args.claims_file))
    claims = [claim.strip() for claim in claims if claim and claim.strip()]
    if not claims:
        print("ERROR: pass --claim or --claims-file", file=sys.stderr)
        return 2
    outdir = args.outdir or (ROOT / "runs" / "quantum_kb_evidence" / slugify(claims[0]))
    dossier = substantiate_claims(
        claims,
        kb_ids,
        kb_root=root,
        quotes_per_claim=args.quotes_per_claim,
        top_k=args.top_k,
        max_words=args.max_words,
        min_score=args.min_score,
    )
    paths = write_substantiation_outputs(dossier, outdir=outdir)
    print(json.dumps({
        "claim_count": dossier["claim_count"],
        "kb_ids": kb_ids,
        "outdir": str(outdir),
        "artifacts": paths,
        "statuses": {
            item["claim_id"]: item["status"]
            for item in dossier.get("claims", [])
        },
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    kb_ids = parse_kb_ids(args.kb, kb_root=root)
    if not kb_ids:
        print(
            "ERROR: no KBs selected. Pass --kb or run bootstrap/create first.",
            file=sys.stderr,
        )
        return 2
    if args.paper and not args.paper.is_file():
        print(f"ERROR: --paper file does not exist: {args.paper}", file=sys.stderr)
        return 2
    claims, paper_text = _collect_review_claims(args)
    if not claims:
        print(
            "ERROR: no claims found. Pass --claim/--claims-file, --question, "
            "or a paper with extractable claims.",
            file=sys.stderr,
        )
        return 2

    outdir = args.outdir or (ROOT / "runs" / "quantum_kb_review" / slugify(claims[0]))
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "review_claims.json").write_text(
        json.dumps({"claims": claims}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    dossier = substantiate_claims(
        claims,
        kb_ids,
        kb_root=root,
        quotes_per_claim=args.quotes_per_claim,
        top_k=args.top_k,
        max_words=args.max_words,
        min_score=args.min_score,
    )
    evidence_paths = write_substantiation_outputs(dossier, outdir=outdir)
    prompt = _build_grounded_review_prompt(
        question=args.question or "",
        paper_text=paper_text,
        dossier=dossier,
    )
    prompt_path = outdir / "grounded_review_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    deterministic = _deterministic_grounded_review(
        question=args.question or "",
        dossier=dossier,
    )
    deterministic_path = outdir / "grounded_review_deterministic.md"
    deterministic_path.write_text(deterministic, encoding="utf-8")

    llm_path = outdir / "grounded_review.md"
    if args.no_llm:
        llm_path.write_text(deterministic, encoding="utf-8")
        print(json.dumps({
            "claim_count": dossier["claim_count"],
            "kb_ids": kb_ids,
            "outdir": str(outdir),
            "mode": "deterministic-no-llm",
            "artifacts": {
                **evidence_paths,
                "prompt": str(prompt_path),
                "grounded_review": str(llm_path),
                "deterministic_review": str(deterministic_path),
                "review_claims": str(outdir / "review_claims.json"),
            },
        }, indent=2, ensure_ascii=False))
        return 0

    try:
        result = call_llm(prompt, backend=args.llm, timeout=900)
    except RuntimeError as exc:
        llm_path.write_text(
            "# KB-Grounded Review FAILED\n\n"
            f"Backend `{args.llm}` did not return output:\n\n`{exc}`\n\n"
            "The evidence dossier and deterministic review were still written. "
            "Re-run with a working backend or `--no-llm` for deterministic output.\n",
            encoding="utf-8",
        )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    llm_path.write_text(result.text, encoding="utf-8")
    (outdir / "_llm_generation.log").write_text(
        f"--- command: quantum_kb review ---\n"
        f"--- backend_requested: {result.backend_requested} ---\n"
        f"--- backend_actually_used: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8",
    )
    write_backend_marker(outdir, result)
    print(json.dumps({
        "claim_count": dossier["claim_count"],
        "kb_ids": kb_ids,
        "outdir": str(outdir),
        "mode": "llm",
        "backend_actually_used": result.backend_actually_used,
        "artifacts": {
            **evidence_paths,
            "prompt": str(prompt_path),
            "grounded_review": str(llm_path),
            "deterministic_review": str(deterministic_path),
            "review_claims": str(outdir / "review_claims.json"),
        },
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_perspective(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    kb_ids = parse_kb_ids(args.kb, kb_root=root)
    if not kb_ids:
        print(
            "ERROR: no KBs selected. Pass --kb or run bootstrap/create first.",
            file=sys.stderr,
        )
        return 2
    if not args.question:
        print("ERROR: perspective requires --question", file=sys.stderr)
        return 2

    outdir = args.outdir or (
        ROOT / "runs" / "quantum_kb_perspective" / slugify(args.question)
    )
    outdir.mkdir(parents=True, exist_ok=True)

    quote_items = select_perspective_quotes(
        args.question,
        kb_ids,
        kb_root=root,
        quote_count=args.quote_count,
        top_k=args.top_k,
        max_words=args.max_words,
        min_score=args.min_score,
    )
    (outdir / "quote_candidates.json").write_text(
        json.dumps(
            {
                "question": args.question,
                "kb_ids": kb_ids,
                "quote_count": len(quote_items),
                "quotes": quote_items,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    quote_packet = render_perspective_quote_packet(quote_items)
    (outdir / "quotes_for_prompt.txt").write_text(quote_packet, encoding="utf-8")
    prompt = build_perspective_prompt(
        question=args.question,
        quote_items=quote_items,
    )
    prompt_path = outdir / "emma_perspective_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    deterministic = build_deterministic_perspective(
        question=args.question,
        quote_items=quote_items,
    )
    deterministic_path = outdir / "01_quantum_perspective_deterministic.md"
    deterministic_path.write_text(deterministic, encoding="utf-8")

    mode = "deterministic-no-llm"
    backend_actually_used = ""
    llm_error = ""
    draft = deterministic
    if not args.no_llm:
        mode = "llm"
        try:
            result = call_llm(prompt, backend=args.llm, timeout=900)
            draft = result.text
            backend_actually_used = result.backend_actually_used
            (outdir / "_raw_perspective_llm.md").write_text(draft, encoding="utf-8")
            (outdir / "_llm_generation.log").write_text(
                f"--- command: quantum_kb perspective ---\n"
                f"--- backend_requested: {result.backend_requested} ---\n"
                f"--- backend_actually_used: {result.backend_actually_used} ---\n"
                f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
                f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
                encoding="utf-8",
            )
            write_backend_marker(outdir, result)
        except RuntimeError as exc:
            mode = "llm-failed-deterministic-fallback"
            llm_error = str(exc)
            (outdir / "_llm_failure.md").write_text(
                "# LLM Perspective Generation Failed\n\n"
                f"`{exc}`\n\n"
                "The deterministic KB-grounded perspective was used instead.\n",
                encoding="utf-8",
            )

    fidelity = verify_perspective_quote_fidelity(
        draft,
        quote_items,
        kb_ids,
        kb_root=root,
    )
    claim_audit = build_perspective_claim_audit(draft, fidelity)
    final_text = append_perspective_appendices(
        draft,
        fidelity=fidelity,
        claim_audit=claim_audit,
    )

    final_path = outdir / "01_quantum_perspective.md"
    final_path.write_text(final_text, encoding="utf-8")
    combined_path = outdir / "quantum_perspective.md"
    combined_path.write_text(final_text, encoding="utf-8")
    (outdir / "quote_fidelity.json").write_text(
        json.dumps(fidelity, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (outdir / "claim_audit.json").write_text(
        json.dumps(claim_audit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    citations = citations_from_quote_items(quote_items)
    (outdir / "citations.md").write_text(
        "# Citations\n\n" + "".join(f"- {c}\n" for c in citations),
        encoding="utf-8",
    )
    fact_check = (
        "# KB-Only Fact Check\n\n"
        "This deterministic pass checks quote fidelity against the local "
        "QuantumNovelty KB chunks. It does not perform external web validation.\n\n"
        f"- Body quote spans: {fidelity['quote_count']}\n"
        f"- KB-verified quote spans: {fidelity['verified_count']}\n"
        f"- Unverified quote spans: {fidelity['unverified_count']}\n"
        f"- Cited claim sentences: {claim_audit['claim_count']}\n"
        f"- Inconclusive cited claim sentences: {claim_audit['inconclusive_count']}\n"
    )
    (outdir / "fact_check.md").write_text(fact_check, encoding="utf-8")

    parity = {
        "workflow": "quantum-kb-perspective",
        "target_workflow": "ScienceSkills ai_emma_perspective_chain own-post workflow",
        "question": args.question,
        "kb_ids": kb_ids,
        "mode": mode,
        "backend_actually_used": backend_actually_used,
        "llm_error": llm_error,
        "quote_candidates": len(quote_items),
        "body_quote_spans": fidelity["quote_count"],
        "verified_quote_spans": fidelity["verified_count"],
        "unverified_quote_spans": fidelity["unverified_count"],
        "claim_count": claim_audit["claim_count"],
        "unsupported_count": claim_audit["unsupported_count"],
        "inconclusive_count": claim_audit["inconclusive_count"],
        "artifacts": {
            "final_perspective": str(final_path),
            "combined_perspective": str(combined_path),
            "prompt": str(prompt_path),
            "quotes_for_prompt": str(outdir / "quotes_for_prompt.txt"),
            "quote_candidates": str(outdir / "quote_candidates.json"),
            "quote_fidelity": str(outdir / "quote_fidelity.json"),
            "claim_audit": str(outdir / "claim_audit.json"),
            "fact_check": str(outdir / "fact_check.md"),
            "citations": str(outdir / "citations.md"),
            "deterministic_perspective": str(deterministic_path),
        },
    }
    (outdir / "emma_parity_report.json").write_text(
        json.dumps(parity, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "question": args.question,
        "kb_ids": kb_ids,
        "outdir": str(outdir),
        "mode": mode,
        "quote_candidates": len(quote_items),
        "verified_quote_spans": fidelity["verified_count"],
        "unverified_quote_spans": fidelity["unverified_count"],
        "artifacts": parity["artifacts"],
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    root = get_quantum_kb_path(kb_root=args.kb_root)
    payload = bootstrap_quantum_core(kb_root=root)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    _write_operation(args.outdir, payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kb-root",
        default=None,
        help="KB root directory. Defaults to QUANTUMNOVELTY_KB_PATH or ./quantum-kb.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="List registered quantum KBs")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("status", help="Show root or KB status as JSON")
    p.add_argument("--kb", default=None)
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("create", help="Create a KB directory and registry entry")
    p.add_argument("--kb", required=True)
    p.add_argument("--name", default=None)
    p.add_argument("--description", default="")
    p.add_argument("--default", action="store_true", help="Make this a default search KB")
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("ingest", help="Copy documents into a KB")
    p.add_argument("--kb", required=True)
    p.add_argument("--source", required=True, help="File or directory to ingest")
    p.add_argument("--refresh", action="store_true", help="Overwrite existing copied files")
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("index", help="Build or update the KB retrieval index")
    p.add_argument("--kb", required=True)
    p.add_argument("--purge", action="store_true", help="Delete old index artifacts first")
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("search", help="Search one or more KBs and emit RAG artifacts")
    p.add_argument("--query", required=True)
    p.add_argument("--kb", default=None, help="Comma-separated KB IDs; default registry defaults")
    p.add_argument("--top-k", type=int, default=40)
    p.add_argument("--max-results", type=int, default=12)
    p.add_argument("--max-words", type=int, default=120)
    p.add_argument("--max-per-source", type=int, default=4)
    p.add_argument("--min-score", type=float, default=0.02)
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser(
        "substantiate",
        help="Retrieve exact quote evidence and citations for one or more claims",
    )
    p.add_argument("--claim", action="append", default=[])
    p.add_argument("--claims-file", type=Path, default=None)
    p.add_argument("--kb", default=None, help="Comma-separated KB IDs; default registry defaults")
    p.add_argument("--quotes-per-claim", type=int, default=3)
    p.add_argument("--top-k", type=int, default=60)
    p.add_argument("--max-words", type=int, default=140)
    p.add_argument("--min-score", type=float, default=0.02)
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_substantiate)

    p = sub.add_parser(
        "review",
        help="Run an Emma-like KB-grounded review with exact quotes and citations",
    )
    p.add_argument("--question", default=None)
    p.add_argument("--paper", type=Path, default=None)
    p.add_argument("--claim", action="append", default=[])
    p.add_argument("--claims-file", type=Path, default=None)
    p.add_argument("--kb", default=None, help="Comma-separated KB IDs; default registry defaults")
    p.add_argument("--quotes-per-claim", type=int, default=3)
    p.add_argument("--max-claims", type=int, default=8)
    p.add_argument("--top-k", type=int, default=60)
    p.add_argument("--max-words", type=int, default=140)
    p.add_argument("--min-score", type=float, default=0.02)
    p.add_argument("--llm", default="claude")
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_review)

    p = sub.add_parser(
        "perspective",
        help="Run an Emma Perspectives-parity KB-grounded perspective workflow",
    )
    p.add_argument("--question", required=True)
    p.add_argument("--kb", default=None, help="Comma-separated KB IDs; default registry defaults")
    p.add_argument("--quote-count", type=int, default=3)
    p.add_argument("--top-k", type=int, default=80)
    p.add_argument("--max-words", type=int, default=90)
    p.add_argument("--min-score", type=float, default=0.02)
    p.add_argument("--llm", default="claude")
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_perspective)

    p = sub.add_parser("bootstrap", help="Create and index the starter quantum_core KB")
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(func=cmd_bootstrap)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
