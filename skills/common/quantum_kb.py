"""Offline-first quantum knowledge-base and RAG utilities.

The ScienceSkills project uses a central seed-kb plus dense/sparse retrieval.
QuantumNovelty needs the same workflow shape, but its base install should keep
working with no model downloads and no network. This module therefore builds a
hybrid index from:

* BM25 lexical postings.
* Deterministic hashed vectors over tokens, bigrams, and character n-grams.
* Quantum-domain query expansion and metadata boosts.

The index format is intentionally plain files under ``quantum-kb/<kb_id>/`` so
it is easy to inspect, sync, and rebuild.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:  # Keep the skill usable from a raw checkout before dependencies install.
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - exercised in minimal runtimes
    np = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_ENV = "QUANTUMNOVELTY_KB_PATH"
DEFAULT_KB_DIRNAME = "quantum-kb"
DEFAULT_KB_ID = "quantum_core"
INDEX_VERSION = "quantum-kb-v1"
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".tex", ".rst", ".bib", ".json", ".jsonl",
    ".pdf", ".docx",
}
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+\-./]*")
SPACE_RE = re.compile(r"\s+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "for", "from", "has", "have", "if", "in", "into", "is", "it", "its",
    "may", "more", "not", "of", "on", "or", "our", "that", "the", "their",
    "this", "to", "under", "using", "via", "was", "we", "were", "with",
}

QUANTUM_EXPANSIONS = {
    "vqe": ["variational", "quantum", "eigensolver", "ansatz", "hamiltonian"],
    "qaoa": ["quantum", "approximate", "optimization", "ansatz"],
    "qec": ["quantum", "error", "correction", "surface", "code"],
    "nnisq": ["noisy", "intermediate", "scale", "quantum"],
    "nisq": ["noisy", "intermediate", "scale", "quantum"],
    "trotter": ["suzuki", "product", "formula", "hamiltonian", "simulation"],
    "ansatz": ["circuit", "variational", "parameters", "state", "preparation"],
    "hamiltonian": ["observable", "energy", "operator", "spectrum"],
    "pauli": ["operator", "string", "observable", "qubit"],
    "entanglement": ["correlation", "nonlocal", "schmidt", "circuit"],
    "qml": ["quantum", "machine", "learning", "kernel", "classifier"],
    "kernel": ["feature", "map", "quantum", "machine", "learning"],
    "surface": ["code", "stabilizer", "syndrome", "logical", "qubit"],
    "logical": ["qubit", "error", "correction", "fault", "tolerant"],
    "fault": ["tolerant", "error", "correction", "logical", "qubit"],
    "shor": ["factoring", "period", "finding", "quantum", "algorithm"],
    "grover": ["amplitude", "amplification", "search", "oracle"],
}

PHRASE_EXPANSIONS = {
    "variational quantum eigensolver": ["vqe", "ansatz", "hamiltonian", "energy"],
    "quantum approximate optimization": ["qaoa", "optimization", "ansatz"],
    "quantum error correction": ["qec", "surface", "code", "stabilizer"],
    "surface code": ["stabilizer", "syndrome", "logical", "qubit"],
    "hamiltonian simulation": ["trotter", "suzuki", "product", "formula"],
    "quantum machine learning": ["qml", "kernel", "feature", "map"],
    "parameter shift": ["gradient", "variational", "circuit"],
}


@dataclass
class KBInfo:
    kb_id: str
    name: str
    description: str
    path: str
    document_count: int = 0
    chunk_count: int = 0
    indexed_at: str | None = None
    status: str = "unknown"


@dataclass
class KBConfig:
    kb_id: str
    name: str
    description: str
    source: dict[str, Any]
    chunking: dict[str, Any]
    retrieval: dict[str, Any]
    indexed_at: str | None
    status: str
    kb_path: Path
    documents_path: Path
    index_path: Path
    cards_path: Path
    manifest_path: Path


@dataclass
class SearchResult:
    kb_id: str
    chunk_id: str
    document_id: str
    title: str
    author: str
    year: str
    source_path: str
    score: float
    bm25_score: float
    vector_score: float
    metadata_score: float
    quote: str
    text: str
    start_char: int | None = None
    end_char: int | None = None
    citation: str = ""
    citation_short: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("score", "bm25_score", "vector_score", "metadata_score"):
            data[key] = round(float(data[key]), 6)
        data["exact_quote"] = self.quote in self.text
        return data


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def slugify(value: str, max_len: int = 80) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return (value or "document")[:max_len]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")
    text = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def simple_tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    tokens: list[str] = []
    for match in WORD_RE.finditer(text.lower()):
        token = match.group(0).strip("_")
        if len(token) < 2:
            continue
        if not keep_stopwords and token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def get_quantum_kb_path(
    project_root: str | Path | None = None,
    kb_root: str | Path | None = None,
) -> Path:
    if kb_root:
        return Path(kb_root).expanduser().resolve()
    env_path = os.environ.get(KB_ENV)
    if env_path:
        return Path(env_path).expanduser().resolve()
    root = Path(project_root).resolve() if project_root else PROJECT_ROOT
    return root / DEFAULT_KB_DIRNAME


def load_registry(kb_root: str | Path | None = None) -> dict[str, Any]:
    root = get_quantum_kb_path(kb_root=kb_root)
    path = root / "kb.json"
    if not path.exists():
        return {"version": "1.0", "default_kbs": [], "knowledge_bases": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(kb_root: str | Path, registry: dict[str, Any]) -> None:
    root = get_quantum_kb_path(kb_root=kb_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "kb.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def list_kbs(kb_root: str | Path | None = None) -> list[KBInfo]:
    root = get_quantum_kb_path(kb_root=kb_root)
    registry = load_registry(root)
    out: list[KBInfo] = []
    for kb_id, info in sorted(registry.get("knowledge_bases", {}).items()):
        out.append(
            KBInfo(
                kb_id=kb_id,
                name=info.get("name", kb_id),
                description=info.get("description", ""),
                path=info.get("path", kb_id),
                document_count=int(info.get("document_count", 0) or 0),
                chunk_count=int(info.get("chunk_count", 0) or 0),
                indexed_at=info.get("indexed_at"),
                status=info.get("status", "unknown"),
            )
        )
    return out


def _default_config(kb_id: str, name: str, description: str) -> dict[str, Any]:
    return {
        "kb_id": kb_id,
        "name": name,
        "description": description,
        "domain": "quantum-computing",
        "source": {"type": "local", "path": "documents"},
        "chunking": {
            "target_words": 220,
            "overlap_words": 55,
            "min_words": 24,
        },
        "retrieval": {
            "index_version": INDEX_VERSION,
            "bm25": {"k1": 1.5, "b": 0.75, "weight": 0.56},
            "hashed_vector": {
                "dims": 2048,
                "weight": 0.36,
                "features": ["tokens", "bigrams", "char4"],
            },
            "metadata_weight": 0.08,
            "query_expansion": "quantum-v1",
        },
        "indexed_at": None,
        "status": "pending_index",
    }


def create_kb(
    kb_id: str,
    name: str | None = None,
    description: str = "",
    *,
    kb_root: str | Path | None = None,
    make_default: bool = False,
) -> KBConfig:
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$", kb_id):
        raise ValueError("kb_id must contain only letters, numbers, hyphen, underscore")

    root = get_quantum_kb_path(kb_root=kb_root)
    registry = load_registry(root)
    if kb_id in registry.get("knowledge_bases", {}):
        raise ValueError(f"KB already exists: {kb_id}")

    name = name or kb_id.replace("_", " ").title()
    kb_path = root / kb_id
    for child in ("documents", "index", "cards"):
        (kb_path / child).mkdir(parents=True, exist_ok=True)

    config = _default_config(kb_id, name, description)
    (kb_path / "kb_config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    registry.setdefault("knowledge_bases", {})[kb_id] = {
        "name": name,
        "description": description,
        "path": kb_id,
        "document_count": 0,
        "chunk_count": 0,
        "indexed_at": None,
        "status": "pending_index",
    }
    if make_default and kb_id not in registry.setdefault("default_kbs", []):
        registry["default_kbs"].append(kb_id)
    save_registry(root, registry)
    return load_kb(kb_id, kb_root=root)


def load_kb(kb_id: str, *, kb_root: str | Path | None = None) -> KBConfig:
    root = get_quantum_kb_path(kb_root=kb_root)
    registry = load_registry(root)
    info = registry.get("knowledge_bases", {}).get(kb_id)
    if not info:
        raise ValueError(f"KB not found: {kb_id}")

    kb_path = root / info.get("path", kb_id)
    config_path = kb_path / "kb_config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        config = _default_config(
            kb_id,
            info.get("name", kb_id),
            info.get("description", ""),
        )

    documents_path = kb_path / config.get("source", {}).get("path", "documents")
    if documents_path.is_symlink():
        documents_path = documents_path.resolve()
    return KBConfig(
        kb_id=kb_id,
        name=config.get("name", info.get("name", kb_id)),
        description=config.get("description", info.get("description", "")),
        source=config.get("source", {"type": "local", "path": "documents"}),
        chunking=config.get("chunking", {}),
        retrieval=config.get("retrieval", {}),
        indexed_at=config.get("indexed_at") or info.get("indexed_at"),
        status=config.get("status", info.get("status", "unknown")),
        kb_path=kb_path,
        documents_path=documents_path,
        index_path=kb_path / "index",
        cards_path=kb_path / "cards",
        manifest_path=kb_path / "manifest.jsonl",
    )


def update_kb_status(
    kb_id: str,
    *,
    kb_root: str | Path | None = None,
    status: str,
    indexed_at: str | None = None,
    document_count: int | None = None,
    chunk_count: int | None = None,
) -> None:
    root = get_quantum_kb_path(kb_root=kb_root)
    registry = load_registry(root)
    info = registry.setdefault("knowledge_bases", {}).get(kb_id)
    if not info:
        raise ValueError(f"KB not found: {kb_id}")
    info["status"] = status
    if indexed_at is not None:
        info["indexed_at"] = indexed_at
    if document_count is not None:
        info["document_count"] = document_count
    if chunk_count is not None:
        info["chunk_count"] = chunk_count
    save_registry(root, registry)

    cfg_path = root / info.get("path", kb_id) / "kb_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["status"] = status
        if indexed_at is not None:
            cfg["indexed_at"] = indexed_at
        cfg_path.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def iter_document_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.name.startswith("_"):
            continue
        if any(part in {"index", "cards", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def ingest_documents(
    kb_id: str,
    source: str | Path,
    *,
    kb_root: str | Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    cfg = load_kb(kb_id, kb_root=kb_root)
    src = Path(source).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"source not found: {src}")
    cfg.documents_path.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    files = list(iter_document_files(src))
    base = src if src.is_dir() else src.parent
    for path in files:
        rel = path.relative_to(base) if path.is_relative_to(base) else Path(path.name)
        dest = cfg.documents_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and not refresh:
            skipped += 1
            continue
        shutil.copy2(path, dest)
        copied += 1
    return {
        "kb_id": kb_id,
        "source": str(src),
        "copied": copied,
        "skipped": skipped,
        "documents_path": str(cfg.documents_path),
    }


def _front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip().lower()] = val.strip().strip("\"'")
    return meta, text[end + 4 :].lstrip()


def _metadata_from_text(path: Path, text: str) -> dict[str, str]:
    meta, body = _front_matter(text)
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    title = meta.get("title", "")
    if not title:
        for line in lines[:20]:
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
    title = title or path.stem.replace("_", " ").replace("-", " ").strip()
    year = meta.get("year", "")
    if not year:
        m = re.search(r"\b(19|20)\d{2}\b", text[:4000])
        year = m.group(0) if m else ""
    author = meta.get("author", meta.get("authors", ""))
    keywords = meta.get("keywords", "")
    return {
        "title": title,
        "author": author,
        "year": year,
        "keywords": keywords,
    }


def read_document(path: Path) -> tuple[str, dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pdfminer.high_level import extract_text
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("pdfminer.six is required for PDF ingest") from exc
        text = extract_text(str(path)) or ""
    elif suffix == ".docx":
        try:
            import docx  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("python-docx is required for DOCX ingest") from exc
        doc = docx.Document(str(path))
        text = "\n\n".join(p.text for p in doc.paragraphs)
    elif suffix == ".jsonl":
        rows: list[str] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                rows.append(_json_obj_to_text(obj))
            except json.JSONDecodeError:
                rows.append(line)
        text = "\n\n".join(rows)
    elif suffix == ".json":
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            text = _json_obj_to_text(json.loads(raw))
        except json.JSONDecodeError:
            text = raw
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")
    text = normalize_text(text)
    meta = _metadata_from_text(path, text)
    _, body = _front_matter(text)
    return normalize_text(body), meta


def _json_obj_to_text(obj: Any) -> str:
    if isinstance(obj, dict):
        preferred = []
        for key in ("title", "abstract", "summary", "text", "content", "body"):
            val = obj.get(key)
            if isinstance(val, str) and val.strip():
                preferred.append(f"{key}: {val.strip()}")
        if preferred:
            return "\n".join(preferred)
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _words_with_spans(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(text)]


def chunk_document(
    text: str,
    *,
    target_words: int = 220,
    overlap_words: int = 55,
    min_words: int = 24,
) -> list[dict[str, Any]]:
    spans = _words_with_spans(text)
    if not spans:
        return []
    target_words = max(40, int(target_words))
    overlap_words = max(0, min(int(overlap_words), target_words // 2))
    step = max(1, target_words - overlap_words)
    chunks: list[dict[str, Any]] = []
    i = 0
    while i < len(spans):
        j = min(len(spans), i + target_words)
        if j - i < min_words and chunks:
            break
        start = spans[i][1]
        end = spans[j - 1][2]
        chunk_text = text[start:end].strip()
        if len(simple_tokenize(chunk_text, keep_stopwords=True)) >= min_words:
            chunks.append(
                {
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "word_count": j - i,
                }
            )
        if j >= len(spans):
            break
        i += step
    return chunks


def _feature_hash(feature: str, dims: int) -> tuple[int, float]:
    digest = int.from_bytes(
        hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(),
        "big",
    )
    sign = -1.0 if digest & (1 << 63) else 1.0
    return digest % dims, sign


def _zero_vector(dims: int) -> Any:
    if np is not None:
        return np.zeros(dims, dtype=np.float32)
    return [0.0] * dims


def _normalize_vector(vec: Any) -> Any:
    if np is not None and hasattr(vec, "shape"):
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec
    norm = math.sqrt(sum(float(x) * float(x) for x in vec))
    if norm > 0:
        return [float(x) / norm for x in vec]
    return vec


def _dot(a: Any, b: Any) -> float:
    if np is not None and hasattr(a, "shape"):
        return float(a @ b)
    return float(sum(float(x) * float(y) for x, y in zip(a, b)))


def hashed_vector(text: str, *, dims: int = 2048) -> Any:
    tokens = simple_tokenize(text)
    vec = _zero_vector(dims)
    if not tokens:
        return vec
    features: list[tuple[str, float]] = []
    features.extend((f"tok:{t}", 1.0) for t in tokens)
    features.extend((f"bi:{tokens[i]}_{tokens[i + 1]}", 1.35) for i in range(len(tokens) - 1))
    compact = re.sub(r"[^a-z0-9]+", " ", text.lower())
    compact = SPACE_RE.sub(" ", compact).strip()
    for word in compact.split():
        if len(word) >= 5:
            for i in range(0, len(word) - 3):
                features.append((f"c4:{word[i:i + 4]}", 0.22))
    for feat, weight in features:
        idx, sign = _feature_hash(feat, dims)
        vec[idx] += sign * weight
    return _normalize_vector(vec)


def expand_query_terms(query: str) -> list[str]:
    base = simple_tokenize(query)
    expanded = list(base)
    lower = query.lower()
    for phrase, extras in PHRASE_EXPANSIONS.items():
        if phrase in lower:
            expanded.extend(extras)
    for token in base:
        expanded.extend(QUANTUM_EXPANSIONS.get(token, []))
    return list(dict.fromkeys(expanded))


def _build_lexical_index(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    postings: dict[str, list[list[int]]] = defaultdict(list)
    df: Counter[str] = Counter()
    doc_lens: list[int] = []
    for idx, chunk in enumerate(chunks):
        terms = simple_tokenize(chunk["text"])
        counts = Counter(terms)
        doc_lens.append(sum(counts.values()))
        for term, tf in sorted(counts.items()):
            postings[term].append([idx, int(tf)])
            df[term] += 1
    avgdl = float(sum(doc_lens) / max(1, len(doc_lens)))
    return {
        "index_version": INDEX_VERSION,
        "chunk_count": len(chunks),
        "avgdl": avgdl,
        "doc_lens": doc_lens,
        "df": dict(df),
        "postings": dict(postings),
    }


def build_index(
    kb_id: str,
    *,
    kb_root: str | Path | None = None,
    purge: bool = False,
) -> dict[str, Any]:
    cfg = load_kb(kb_id, kb_root=kb_root)
    if purge and cfg.index_path.exists():
        shutil.rmtree(cfg.index_path)
    cfg.index_path.mkdir(parents=True, exist_ok=True)

    chunking = cfg.chunking or {}
    target_words = int(chunking.get("target_words", 220))
    overlap_words = int(chunking.get("overlap_words", 55))
    min_words = int(chunking.get("min_words", 24))
    dims = int(
        cfg.retrieval.get("hashed_vector", {}).get("dims", 2048)
    )

    chunks: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for doc_path in iter_document_files(cfg.documents_path):
        try:
            text, meta = read_document(doc_path)
        except Exception as exc:
            errors.append({"path": str(doc_path), "error": str(exc)})
            continue
        if not text.strip():
            continue
        rel_source = doc_path.relative_to(cfg.kb_path) if doc_path.is_relative_to(cfg.kb_path) else doc_path
        stable = hashlib.blake2b(str(rel_source).encode("utf-8"), digest_size=4).hexdigest()
        doc_id = slugify(f"{doc_path.stem}_{stable}")
        doc_chunks = chunk_document(
            text,
            target_words=target_words,
            overlap_words=overlap_words,
            min_words=min_words,
        )
        manifest_entry = {
            "document_id": doc_id,
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "year": meta.get("year", ""),
            "keywords": meta.get("keywords", ""),
            "source_path": str(rel_source),
            "char_count": len(text),
            "chunk_count": len(doc_chunks),
            "indexed_at": now_iso(),
        }
        manifest.append(manifest_entry)
        for i, chunk in enumerate(doc_chunks):
            chunk_id = f"{doc_id}:{i:04d}"
            chunks.append(
                {
                    **chunk,
                    "kb_id": kb_id,
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "title": meta.get("title", ""),
                    "author": meta.get("author", ""),
                    "year": meta.get("year", ""),
                    "keywords": meta.get("keywords", ""),
                    "source_path": str(rel_source),
                }
            )

    lexical = _build_lexical_index(chunks)
    vector_rows = [hashed_vector(c["text"], dims=dims) for c in chunks]
    with (cfg.index_path / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    (cfg.index_path / "lexical_index.json").write_text(
        json.dumps(lexical, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if np is not None:
        vectors = (
            np.vstack(vector_rows).astype(np.float32)
            if vector_rows
            else np.zeros((0, dims), dtype=np.float32)
        )
        np.savez_compressed(
            cfg.index_path / "hashed_vectors.npz",
            vectors=vectors,
            chunk_ids=np.array([c["chunk_id"] for c in chunks]),
        )
        vector_store = "hashed_vectors.npz"
    else:
        (cfg.index_path / "hashed_vectors.json").write_text(
            json.dumps({
                "dims": dims,
                "chunk_ids": [c["chunk_id"] for c in chunks],
                "vectors": vector_rows,
            }, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        vector_store = "hashed_vectors.json"
    with cfg.manifest_path.open("w", encoding="utf-8") as f:
        for item in manifest:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    indexed_at = now_iso()
    stats = {
        "index_version": INDEX_VERSION,
        "kb_id": kb_id,
        "document_count": len(manifest),
        "chunk_count": len(chunks),
        "vocabulary_terms": len(lexical["df"]),
        "vector_dims": dims,
        "vector_store": vector_store,
        "indexed_at": indexed_at,
        "errors": errors,
    }
    (cfg.index_path / "index_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    update_kb_status(
        kb_id,
        kb_root=kb_root,
        status="ready" if chunks else "empty",
        indexed_at=indexed_at,
        document_count=len(manifest),
        chunk_count=len(chunks),
    )
    return stats


def _load_chunks(cfg: KBConfig) -> list[dict[str, Any]]:
    path = cfg.index_path / "chunks.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"missing index chunks: {path}")
    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def _load_lexical(cfg: KBConfig, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    path = cfg.index_path / "lexical_index.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return _build_lexical_index(chunks)


def _load_vectors(cfg: KBConfig, dims: int) -> Any:
    npz_path = cfg.index_path / "hashed_vectors.npz"
    if np is not None and npz_path.exists():
        data = np.load(npz_path, allow_pickle=False)
        vectors = data["vectors"].astype(np.float32)
        if vectors.ndim == 2:
            return vectors
    json_path = cfg.index_path / "hashed_vectors.json"
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        return payload.get("vectors", [])
    if np is not None:
        return np.zeros((0, dims), dtype=np.float32)
    return []


def _bm25_scores(query_terms: list[str], lexical: dict[str, Any]) -> list[float]:
    n = int(lexical.get("chunk_count", 0) or 0)
    scores = [0.0] * n
    if n == 0:
        return scores
    avgdl = float(lexical.get("avgdl", 1.0) or 1.0)
    doc_lens = lexical.get("doc_lens", [avgdl] * n)
    df = lexical.get("df", {})
    postings = lexical.get("postings", {})
    k1 = 1.5
    b = 0.75
    for term in dict.fromkeys(query_terms):
        term_df = int(df.get(term, 0) or 0)
        if term_df <= 0:
            continue
        idf = math.log(1.0 + (n - term_df + 0.5) / (term_df + 0.5))
        for idx, tf in postings.get(term, []):
            dl = float(doc_lens[idx] or avgdl)
            denom = tf + k1 * (1.0 - b + b * dl / avgdl)
            scores[idx] += idf * ((tf * (k1 + 1.0)) / denom)
    return scores


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    hi = max(scores)
    if hi <= 0:
        return [0.0 for _ in scores]
    return [max(0.0, s) / hi for s in scores]


def _metadata_score(chunk: dict[str, Any], query: str, query_terms: list[str]) -> float:
    hay = " ".join(
        str(chunk.get(k, "")) for k in ("title", "author", "year", "keywords", "source_path")
    ).lower()
    if not hay:
        return 0.0
    hits = sum(1 for term in set(query_terms) if term in hay)
    exact = 1.0 if query.lower().strip() and query.lower().strip() in hay else 0.0
    return min(1.0, exact * 0.55 + hits / max(1, len(set(query_terms))))


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    start = 0
    for match in SENTENCE_RE.finditer(text):
        end = match.start()
        raw = text[start:end]
        if raw.strip():
            spans.append((start, end, raw))
        start = match.end()
    raw = text[start:]
    if raw.strip():
        spans.append((start, len(text), raw))
    return spans


def _trim_substring_words(text: str, query_terms: list[str], max_words: int) -> str:
    spans = list(WORD_RE.finditer(text))
    if len(spans) <= max_words:
        return text.strip()
    qset = set(query_terms)
    center = 0
    for i, match in enumerate(spans):
        token = match.group(0).lower()
        if token in qset:
            center = i
            break
    start_i = max(0, center - max_words // 2)
    end_i = min(len(spans) - 1, start_i + max_words - 1)
    return text[spans[start_i].start():spans[end_i].end()].strip()


def _best_quote(text: str, query: str, query_terms: list[str], max_words: int) -> str:
    sentence_spans = _sentence_spans(text)
    sentences = [s[2].strip() for s in sentence_spans]
    if not sentences:
        return _trim_substring_words(text, query_terms, max_words)
    qset = set(query_terms)
    best_i = 0
    best_score = -1.0
    query_lower = query.lower().strip()
    for i, sentence in enumerate(sentences):
        stoks = set(simple_tokenize(sentence))
        score = len(stoks & qset)
        if query_lower and query_lower in sentence.lower():
            score += 3
        if score > best_score:
            best_score = float(score)
            best_i = i
    start_i = max(0, best_i - 1)
    end_i = min(len(sentence_spans) - 1, best_i + 1)
    start = sentence_spans[start_i][0]
    end = sentence_spans[end_i][1]
    quote = text[start:end].strip()
    return _trim_substring_words(quote, query_terms, max_words)


def _trim_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip() + " ..."


def _citation(chunk: dict[str, Any]) -> tuple[str, str]:
    title = str(chunk.get("title") or chunk.get("document_id") or "Unknown")
    author = str(chunk.get("author") or "").strip()
    year = str(chunk.get("year") or "").strip()
    source = str(chunk.get("source_path") or "").strip()
    full_parts: list[str] = []
    if author:
        author_part = author if author.endswith(".") else f"{author}."
        full_parts.append(author_part)
    if year:
        full_parts.append(f"({year})")
    title_part = title if title.endswith(".") else f"{title}."
    full_parts.append(title_part)
    if source:
        full_parts.append(source)
    full = " ".join(p for p in full_parts if p).strip()
    if full and not full.endswith("."):
        full += "."
    if author:
        last = author.split(",")[0].split()[-1]
        short = f"{last} {year}".strip()
    else:
        short = f"{title[:46]} {year}".strip()
    return full or title, short


def _search_one_kb(
    cfg: KBConfig,
    query: str,
    *,
    top_k: int,
    max_words: int,
) -> list[SearchResult]:
    chunks = _load_chunks(cfg)
    if not chunks:
        return []
    lexical = _load_lexical(cfg, chunks)
    dims = int(cfg.retrieval.get("hashed_vector", {}).get("dims", 2048))
    vectors = _load_vectors(cfg, dims)
    query_terms = expand_query_terms(query)

    bm25_raw = _bm25_scores(query_terms, lexical)
    bm25_norm = _normalize_scores(bm25_raw)
    qvec = hashed_vector(" ".join(query_terms), dims=dims)
    if np is not None and hasattr(vectors, "shape") and len(vectors) == len(chunks) and vectors.size:
        vector_raw = np.maximum(vectors @ qvec, 0).astype(float).tolist()
    elif isinstance(vectors, list) and len(vectors) == len(chunks):
        vector_raw = [max(_dot(v, qvec), 0.0) for v in vectors]
    else:
        vector_raw = [0.0] * len(chunks)
    vector_norm = _normalize_scores(vector_raw)

    bm25_weight = float(cfg.retrieval.get("bm25", {}).get("weight", 0.56))
    vec_weight = float(cfg.retrieval.get("hashed_vector", {}).get("weight", 0.36))
    meta_weight = float(cfg.retrieval.get("metadata_weight", 0.08))

    results: list[SearchResult] = []
    for i, chunk in enumerate(chunks):
        meta = _metadata_score(chunk, query, query_terms)
        score = bm25_weight * bm25_norm[i] + vec_weight * vector_norm[i] + meta_weight * meta
        if score <= 0:
            continue
        full, short = _citation(chunk)
        results.append(
            SearchResult(
                kb_id=cfg.kb_id,
                chunk_id=str(chunk.get("chunk_id", "")),
                document_id=str(chunk.get("document_id", "")),
                title=str(chunk.get("title", "")),
                author=str(chunk.get("author", "")),
                year=str(chunk.get("year", "")),
                source_path=str(chunk.get("source_path", "")),
                score=score,
                bm25_score=bm25_norm[i],
                vector_score=vector_norm[i],
                metadata_score=meta,
                quote=_best_quote(str(chunk.get("text", "")), query, query_terms, max_words),
                text=str(chunk.get("text", "")),
                start_char=chunk.get("start_char"),
                end_char=chunk.get("end_char"),
                citation=full,
                citation_short=short,
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


def default_kb_ids(kb_root: str | Path | None = None) -> list[str]:
    registry = load_registry(kb_root)
    defaults = registry.get("default_kbs", [])
    if defaults:
        return list(defaults)
    return [
        info.kb_id for info in list_kbs(kb_root)
        if info.status in {"ready", "empty", "pending_index"}
    ]


def parse_kb_ids(value: str | None, *, kb_root: str | Path | None = None) -> list[str]:
    if value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return default_kb_ids(kb_root)


def _quote_signature(result: SearchResult) -> str:
    text = result.quote.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return SPACE_RE.sub(" ", text).strip()


def search_kbs(
    query: str,
    kb_ids: list[str],
    *,
    kb_root: str | Path | None = None,
    top_k: int = 40,
    max_results: int = 12,
    max_words: int = 120,
    max_per_source: int = 4,
    min_score: float = 0.02,
) -> list[SearchResult]:
    all_results: list[SearchResult] = []
    for kb_id in kb_ids:
        cfg = load_kb(kb_id, kb_root=kb_root)
        all_results.extend(_search_one_kb(cfg, query, top_k=top_k, max_words=max_words))
    all_results.sort(key=lambda r: r.score, reverse=True)

    selected: list[SearchResult] = []
    seen_quotes: set[str] = set()
    per_source: Counter[str] = Counter()
    for result in all_results:
        if result.score < min_score:
            continue
        sig = _quote_signature(result)
        if not sig or sig in seen_quotes:
            continue
        source_key = f"{result.kb_id}:{result.document_id}"
        if per_source[source_key] >= max_per_source:
            continue
        seen_quotes.add(sig)
        per_source[source_key] += 1
        selected.append(result)
        if len(selected) >= max_results:
            break
    return selected


def write_search_outputs(
    results: list[SearchResult],
    *,
    query: str,
    kb_ids: list[str],
    outdir: str | Path,
    kb_root: str | Path | None = None,
) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": query,
        "kb_ids": kb_ids,
        "kb_root": str(get_quantum_kb_path(kb_root=kb_root)),
        "timestamp": now_iso(),
        "result_count": len(results),
        "query_terms_expanded": expand_query_terms(query),
        "results": [r.to_dict() for r in results],
    }
    json_path = out / "search_results.json"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    md_path = out / "search_results.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Quantum KB Search Results\n\n")
        f.write(f"**Query:** {query}\n\n")
        f.write(f"**Knowledge bases:** {', '.join(kb_ids)}\n\n")
        f.write(f"**Results:** {len(results)}\n\n")
        for i, result in enumerate(results, 1):
            f.write(f"## Result {i} [{result.kb_id}] score={result.score:.3f}\n\n")
            f.write(f"**Source:** {result.title or result.document_id}\n\n")
            f.write(f"**Citation:** {result.citation}\n\n")
            f.write(f"**Chunk:** `{result.chunk_id}`\n\n")
            f.write(f"> {result.quote}\n\n")

    prompt_path = out / "quotes_for_prompt.txt"
    with prompt_path.open("w", encoding="utf-8") as f:
        f.write("# Retrieved Quantum KB Quotes\n\n")
        f.write("Use these snippets as retrieved evidence. Preserve quoted wording when citing.\n\n")
        for i, result in enumerate(results, 1):
            f.write(f"{i}. \"{result.quote}\" ({result.citation_short})\n")
            f.write(f"   Source: [{result.kb_id}] {result.title} / {result.source_path}\n\n")

    context_path = out / "context.md"
    with context_path.open("w", encoding="utf-8") as f:
        f.write("## Retrieved Context\n\n")
        for i, result in enumerate(results, 1):
            f.write(
                f"[{i}] {result.title} ({result.citation_short}), "
                f"{result.kb_id}, score {result.score:.3f}\n\n"
            )
            f.write(f"{result.quote}\n\n")
    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "quotes_for_prompt": str(prompt_path),
        "context": str(context_path),
    }


def substantiate_claims(
    claims: list[str],
    kb_ids: list[str],
    *,
    kb_root: str | Path | None = None,
    quotes_per_claim: int = 3,
    top_k: int = 60,
    max_words: int = 140,
    min_score: float = 0.02,
) -> dict[str, Any]:
    """Retrieve exact quote evidence for each claim.

    This is the ScienceSkills-style claim grounding layer: a claim is not
    treated as substantiated by summary text. It receives a small dossier of
    word-for-word snippets plus citations and source provenance.
    """
    dossiers: list[dict[str, Any]] = []
    clean_claims = [c.strip() for c in claims if c and c.strip()]
    for idx, claim in enumerate(clean_claims, 1):
        results = search_kbs(
            claim,
            kb_ids,
            kb_root=kb_root,
            top_k=top_k,
            max_results=quotes_per_claim,
            max_words=max_words,
            max_per_source=2,
            min_score=min_score,
        )
        evidence = []
        for rank, result in enumerate(results, 1):
            item = result.to_dict()
            item["rank"] = rank
            item["support_relation"] = "retrieved_relevant_quote"
            evidence.append(item)
        if len(evidence) >= quotes_per_claim:
            status = "substantiated"
        elif evidence:
            status = "partially_substantiated"
        else:
            status = "unsubstantiated"
        dossiers.append(
            {
                "claim_id": f"C{idx:03d}",
                "claim": claim,
                "status": status,
                "evidence_count": len(evidence),
                "evidence": evidence,
            }
        )
    return {
        "timestamp": now_iso(),
        "kb_ids": kb_ids,
        "kb_root": str(get_quantum_kb_path(kb_root=kb_root)),
        "claim_count": len(clean_claims),
        "quotes_per_claim": quotes_per_claim,
        "claims": dossiers,
    }


def write_substantiation_outputs(
    dossier: dict[str, Any],
    *,
    outdir: str | Path,
) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "claim_evidence.json"
    json_path.write_text(
        json.dumps(dossier, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    md_path = out / "claim_evidence.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Claim Evidence Dossier\n\n")
        f.write(f"**Knowledge bases:** {', '.join(dossier.get('kb_ids', []))}\n\n")
        f.write(f"**Claims:** {dossier.get('claim_count', 0)}\n\n")
        for claim in dossier.get("claims", []):
            f.write(f"## {claim['claim_id']} - {claim['status']}\n\n")
            f.write(f"**Claim:** {claim['claim']}\n\n")
            evidence = claim.get("evidence", [])
            if not evidence:
                f.write("_No supporting quote met the retrieval threshold._\n\n")
                continue
            for item in evidence:
                f.write(
                    f"### Evidence {item['rank']} "
                    f"(score {item['score']:.3f}, {item['kb_id']})\n\n"
                )
                f.write(f"**Citation:** {item.get('citation', '')}\n\n")
                f.write(f"**Inline cite:** ({item.get('citation_short', '')})\n\n")
                f.write(f"**Source:** `{item.get('source_path', '')}`\n\n")
                f.write(f"**Chunk:** `{item.get('chunk_id', '')}`\n\n")
                f.write(f"**Exact quote:** {bool(item.get('exact_quote'))}\n\n")
                f.write(f"> {item.get('quote', '')}\n\n")

    prompt_path = out / "evidence_for_prompt.txt"
    with prompt_path.open("w", encoding="utf-8") as f:
        f.write("# Claim-Grounded Evidence\n\n")
        f.write(
            "Use only these word-for-word quotes to substantiate the listed "
            "claims. Preserve quoted wording and include the inline citation.\n\n"
        )
        for claim in dossier.get("claims", []):
            f.write(f"{claim['claim_id']}. Claim: {claim['claim']}\n")
            evidence = claim.get("evidence", [])
            if not evidence:
                f.write("   Evidence: none retrieved above threshold.\n\n")
                continue
            for item in evidence:
                f.write(
                    f"   - \"{item.get('quote', '')}\" "
                    f"({item.get('citation_short', '')})\n"
                )
                f.write(
                    f"     Source: [{item.get('kb_id', '')}] "
                    f"{item.get('title', '')} / {item.get('source_path', '')}\n"
                )
            f.write("\n")

    bibliography_path = out / "citations.md"
    seen: set[str] = set()
    with bibliography_path.open("w", encoding="utf-8") as f:
        f.write("# Citations\n\n")
        for claim in dossier.get("claims", []):
            for item in claim.get("evidence", []):
                citation = item.get("citation", "")
                if not citation or citation in seen:
                    continue
                seen.add(citation)
                f.write(f"- {citation}\n")

    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "evidence_for_prompt": str(prompt_path),
        "citations": str(bibliography_path),
    }


LEFT_DQ = "\u201c"
RIGHT_DQ = "\u201d"
QUOTE_SPAN_RE = re.compile(
    r'"([^"]{8,1200})"|'
    + re.escape(LEFT_DQ)
    + r"([^"
    + re.escape(RIGHT_DQ)
    + r"]{8,1200})"
    + re.escape(RIGHT_DQ),
    re.S,
)
PROVENANCE_SECTION_RE = re.compile(
    r"\n+##\s+(?:Quotes used|Claims \(verified|Citations)\b.*\Z",
    re.S | re.I,
)


def _word_count(text: str) -> int:
    return len(simple_tokenize(text, keep_stopwords=True))


def _quote_match_text(needle: str, haystack: str) -> bool:
    n = SPACE_RE.sub(" ", needle).strip().lower()
    h = SPACE_RE.sub(" ", haystack).strip().lower()
    if not n:
        return False
    if n in h:
        return True
    na = re.sub(r"[^a-z0-9]+", "", n)
    ha = re.sub(r"[^a-z0-9]+", "", h)
    return len(na) >= 12 and na in ha


def _short_quote_fragment(
    result: SearchResult,
    *,
    query: str,
    max_words: int = 32,
    min_words: int = 7,
) -> str:
    """Choose an Emma-style short verbatim fragment from a retrieved chunk."""
    query_terms = expand_query_terms(query)
    qset = set(query_terms)
    candidates: list[tuple[float, str]] = []
    for source in (result.quote, result.text):
        for _, _, raw in _sentence_spans(source):
            raw_sentence = raw.strip()
            sentence = SPACE_RE.sub(" ", raw_sentence).strip()
            words = _word_count(raw_sentence)
            if words < min_words or words > max_words:
                continue
            if _bad_quote_candidate(raw_sentence):
                continue
            if '"' in raw_sentence or LEFT_DQ in raw_sentence or RIGHT_DQ in raw_sentence:
                continue
            if raw_sentence not in result.text:
                continue
            stoks = set(simple_tokenize(sentence))
            score = len(stoks & qset) + 0.01 * min(words, max_words)
            candidates.append((float(score), raw_sentence))
    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    base = result.quote if result.quote in result.text else result.text
    fragment = _trim_substring_words(base, query_terms, max_words)
    if fragment and fragment in result.text:
        return fragment
    return result.quote.strip()


def _bad_quote_candidate(text: str) -> bool:
    lower = text.lower()
    if any(marker in lower for marker in ("file://", "http://", "https://", "appdata", "/temp/")):
        return True
    if re.search(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", text):
        return True
    stripped = SPACE_RE.sub(" ", text).strip()
    if re.match(r"^\d{1,4}\s+", stripped):
        return True
    if re.search(r"\b\d+/\d+\b", stripped):
        return True
    alpha = sum(1 for ch in stripped if ch.isalpha())
    if stripped and alpha / max(1, len(stripped)) < 0.45:
        return True
    return False


def perspective_retrieval_query(question: str) -> str:
    """Expand a user-facing perspective question into a retrieval query.

    The prose question can be high-level ("is this ansatz novel?"). Retrieval
    needs concrete audit terms that appear in VQE/ADAPT-VQE papers.
    """
    lower = question.lower()
    extras: list[str] = []
    if "vqe" in lower or "ansatz" in lower:
        extras.extend(
            [
                "ADAPT-VQE",
                "UCCSD",
                "operator pool",
                "variational parameters",
                "circuit depth",
                "chemical accuracy",
                "gradient norm",
                "algorithm terminates",
                "shot count",
                "coherence times",
            ]
        )
    if any(term in lower for term in ("novel", "novelty", "llm-discovered", "discovered")):
        extras.extend(
            [
                "baseline",
                "comparison",
                "error",
                "resource",
                "robust",
                "generalization",
                "selection heuristic",
            ]
        )
    if not extras:
        return question
    return question + " " + " ".join(dict.fromkeys(extras))


def select_perspective_quotes(
    question: str,
    kb_ids: list[str],
    *,
    kb_root: str | Path | None = None,
    quote_count: int = 3,
    top_k: int = 80,
    max_words: int = 90,
    min_score: float = 0.02,
) -> list[dict[str, Any]]:
    """Retrieve short, exact quote fragments for an Emma-like perspective."""
    retrieval_query = perspective_retrieval_query(question)
    results = search_kbs(
        retrieval_query,
        kb_ids,
        kb_root=kb_root,
        top_k=top_k,
        max_results=max(quote_count * 5, 12),
        max_words=max_words,
        max_per_source=3,
        min_score=min_score,
    )
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results:
        quote = _short_quote_fragment(result, query=retrieval_query)
        if _bad_quote_candidate(quote):
            continue
        sig = re.sub(r"[^a-z0-9]+", " ", quote.lower()).strip()
        if not sig or sig in seen:
            continue
        item = result.to_dict()
        item.update(
            {
                "quote_id": f"Q{len(selected) + 1:03d}",
                "rank": len(selected) + 1,
                "quote": quote,
                "source_quote": result.quote,
                "quote_word_count": _word_count(quote),
                "exact_quote": quote in result.text,
                "support_relation": "retrieved_relevant_quote",
                "retrieval_query": retrieval_query,
            }
        )
        selected.append(item)
        seen.add(sig)
        if len(selected) >= quote_count:
            break
    return selected


def render_perspective_quote_packet(quote_items: list[dict[str, Any]]) -> str:
    lines = [
        "# Retrieved Quantum KB Quotes",
        "",
        "Use these as the only external evidence. Preserve quoted wording exactly.",
        "",
    ]
    if not quote_items:
        lines.append("_No quote evidence was retrieved above threshold._")
    for item in quote_items:
        lines.append(
            f"{item.get('quote_id', 'Q???')}. "
            f"\"{item.get('quote', '')}\" "
            f"({item.get('citation_short', '')})"
        )
        lines.append(f"   Full citation: {item.get('citation', '')}")
        lines.append(
            f"   Source: [{item.get('kb_id', '')}] "
            f"{item.get('source_path', '')} / {item.get('chunk_id', '')}"
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_perspective_prompt(
    *,
    question: str,
    quote_items: list[dict[str, Any]],
) -> str:
    packet = render_perspective_quote_packet(quote_items)
    return (
        "# QuantumNovelty Emma-Perspective-Parity Review\n\n"
        "Write a concise, argument-driven quantum review perspective in the "
        "style of the ScienceSkills Emma Perspectives workflow.\n\n"
        "Hard constraints:\n"
        "- Use only the retrieved KB quotes below for external support.\n"
        "- Include 2-3 short word-for-word quotations, each followed by its "
        "inline citation in parentheses.\n"
        "- Do not invent sources, page numbers, quotations, or citations.\n"
        "- If evidence is thin, say that directly rather than overstating it.\n"
        "- Do not include a bibliography or quote appendix; the workflow will "
        "append verified provenance after generation.\n\n"
        "Structure:\n"
        "1. Title.\n"
        "2. Position: the answer to the question.\n"
        "3. Evidence: what the quoted KB evidence does and does not establish.\n"
        "4. Decision rule: how to evaluate the claim going forward.\n\n"
        "## Question\n\n"
        f"{question}\n\n"
        "## Retrieved Evidence\n\n"
        f"{packet}"
    )


def build_deterministic_perspective(
    *,
    question: str,
    quote_items: list[dict[str, Any]],
) -> str:
    """No-LLM perspective used for tests and deterministic parity checks."""
    lines = [
        "# Evidence Standard for a Novel VQE Ansatz",
        "",
        f"**Question:** {question}",
        "",
        "## Position",
        "",
    ]
    if not quote_items:
        lines.extend(
            [
                "The KB did not return enough quote evidence to substantiate a "
                "novelty judgment. Treat the claim as ungrounded until the KB is "
                "expanded or the search terms are revised.",
                "",
            ]
        )
        return "\n".join(lines)

    first = quote_items[0]
    lines.extend(
        [
            "A genuinely novel LLM-discovered ansatz should survive comparison "
            "against established variational baselines, not merely produce a "
            "plausible circuit. The first evidentiary requirement is an explicit "
            "benchmark frame: "
            f"\"{first.get('quote', '')}\" ({first.get('citation_short', '')}).",
            "",
            "## Evidence Reading",
            "",
        ]
    )
    if len(quote_items) >= 2:
        second = quote_items[1]
        lines.extend(
            [
                "The second requirement is procedural: define the stopping rule, "
                "growth rule, or search budget before calling the ansatz new. "
                "The retrieved evidence makes that audit point concrete: "
                f"\"{second.get('quote', '')}\" "
                f"({second.get('citation_short', '')}).",
                "",
            ]
        )
    if len(quote_items) >= 3:
        third = quote_items[2]
        lines.extend(
            [
                "The third requirement is robustness. A novelty claim is stronger "
                "when it holds under realistic resource or noise comparisons, "
                "because a shallow improvement can disappear once the benchmark "
                "conditions change: "
                f"\"{third.get('quote', '')}\" "
                f"({third.get('citation_short', '')}).",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision Rule",
            "",
            "Count the LLM-discovered ansatz as genuinely novel only if the "
            "paper supplies source-backed evidence for three things: a named "
            "baseline set, a transparent search or termination protocol, and a "
            "resource-aware comparison that still favors the proposed circuit. "
            "If any one of those is missing, the safer verdict is partial "
            "support rather than novelty.",
            "",
        ]
    )
    return "\n".join(lines)


def extract_quoted_spans(markdown: str, *, body_only: bool = True) -> list[str]:
    text = PROVENANCE_SECTION_RE.sub("", markdown) if body_only else markdown
    spans: list[str] = []
    seen: set[str] = set()
    for match in QUOTE_SPAN_RE.finditer(text):
        quote = match.group(1) or match.group(2) or ""
        quote = SPACE_RE.sub(" ", quote).strip()
        sig = quote.lower()
        if len(quote) < 8 or _word_count(quote) < 2 or sig in seen:
            continue
        seen.add(sig)
        spans.append(quote)
    return spans


def _find_quote_in_kb_chunks(
    quote: str,
    kb_ids: list[str],
    *,
    kb_root: str | Path | None = None,
) -> dict[str, Any] | None:
    for kb_id in kb_ids:
        cfg = load_kb(kb_id, kb_root=kb_root)
        for chunk in _load_chunks(cfg):
            text = str(chunk.get("text", ""))
            if _quote_match_text(quote, text):
                full, short = _citation(chunk)
                return {
                    "kb_id": kb_id,
                    "chunk_id": str(chunk.get("chunk_id", "")),
                    "document_id": str(chunk.get("document_id", "")),
                    "title": str(chunk.get("title", "")),
                    "source_path": str(chunk.get("source_path", "")),
                    "citation": full,
                    "citation_short": short,
                    "text": text,
                }
    return None


def verify_perspective_quote_fidelity(
    markdown: str,
    quote_items: list[dict[str, Any]],
    kb_ids: list[str],
    *,
    kb_root: str | Path | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    spans = extract_quoted_spans(markdown)
    for quote in spans:
        matched: dict[str, Any] | None = None
        for item in quote_items:
            if _quote_match_text(quote, str(item.get("text", ""))):
                matched = dict(item)
                matched["match_method"] = "retrieved_quote_chunk"
                break
        if matched is None:
            matched = _find_quote_in_kb_chunks(quote, kb_ids, kb_root=kb_root)
            if matched is not None:
                matched["match_method"] = "kb_chunk_scan"

        if matched is None:
            rows.append(
                {
                    "quote": quote,
                    "verified": False,
                    "source": None,
                    "citation": "",
                    "citation_short": "",
                    "match_method": "not_found",
                }
            )
        else:
            rows.append(
                {
                    "quote": quote,
                    "verified": True,
                    "quote_id": matched.get("quote_id"),
                    "source": {
                        "kb_id": matched.get("kb_id", ""),
                        "source_path": matched.get("source_path", ""),
                        "chunk_id": matched.get("chunk_id", ""),
                        "title": matched.get("title", ""),
                    },
                    "citation": matched.get("citation", ""),
                    "citation_short": matched.get("citation_short", ""),
                    "match_method": matched.get("match_method", ""),
                }
            )
    verified_count = sum(1 for row in rows if row.get("verified"))
    return {
        "timestamp": now_iso(),
        "quote_count": len(rows),
        "verified_count": verified_count,
        "unverified_count": len(rows) - verified_count,
        "quotes": rows,
    }


def build_perspective_claim_audit(
    markdown: str,
    fidelity: dict[str, Any],
) -> dict[str, Any]:
    body = PROVENANCE_SECTION_RE.sub("", markdown)
    sentences = [
        SPACE_RE.sub(" ", s).strip()
        for s in SENTENCE_RE.split(body)
        if SPACE_RE.sub(" ", s).strip()
    ]
    verified_quotes = [
        row.get("quote", "")
        for row in fidelity.get("quotes", [])
        if row.get("verified")
    ]
    items: list[dict[str, Any]] = []
    for sent in sentences:
        has_cite = bool(re.search(r"\([^)]{2,100}\)", sent))
        if not has_cite:
            continue
        quoted = [q for q in verified_quotes if q and q in sent]
        verdict = "SUPPORTED" if quoted else "INCONCLUSIVE"
        items.append(
            {
                "claim": sent,
                "verdict": verdict,
                "source": "verified quote" if quoted else "citation without matched quote",
                "quotes": quoted,
                "why": (
                    "Sentence includes a KB-verified verbatim quote."
                    if quoted
                    else "Sentence has a citation but no verified quote span."
                ),
            }
        )
    unsupported = sum(1 for item in items if item["verdict"] == "NOT_SUPPORTED")
    inconclusive = sum(1 for item in items if item["verdict"] == "INCONCLUSIVE")
    return {
        "timestamp": now_iso(),
        "claim_count": len(items),
        "supported_count": sum(1 for item in items if item["verdict"] == "SUPPORTED"),
        "unsupported_count": unsupported,
        "inconclusive_count": inconclusive,
        "items": items,
        "note": (
            "Deterministic KB-only scaffold. It verifies quote-bearing cited "
            "sentences but does not replace ScienceSkills' LLM claim-audit vote."
        ),
    }


def append_perspective_appendices(
    markdown: str,
    *,
    fidelity: dict[str, Any],
    claim_audit: dict[str, Any] | None = None,
) -> str:
    base = PROVENANCE_SECTION_RE.sub("", markdown).rstrip()
    lines = ["", "## Quotes used (verbatim, with source)", ""]
    rows = fidelity.get("quotes", [])
    if not rows:
        lines.append("_No KB-cited quotations._")
    for row in rows:
        quote = row.get("quote", "")
        if row.get("verified"):
            source = row.get("source") or {}
            source_bits = [
                row.get("citation") or row.get("citation_short") or "unknown citation",
                source.get("source_path", ""),
                source.get("chunk_id", ""),
            ]
            source_label = ", ".join(bit for bit in source_bits if bit)
            lines.append(f'- "{quote}" - {source_label}')
        else:
            lines.append(f'- "{quote}" - (source not located)')

    if claim_audit is not None:
        lines.extend(
            [
                "",
                "## Claims (verified against cited sources)",
                "",
                (
                    f"_{claim_audit.get('claim_count', 0)} attributed claim(s): "
                    f"{claim_audit.get('supported_count', 0)} supported, "
                    f"{claim_audit.get('unsupported_count', 0)} unsupported, "
                    f"{claim_audit.get('inconclusive_count', 0)} inconclusive._"
                ),
                "",
            ]
        )
        if not claim_audit.get("items"):
            lines.append("_No cited claims detected._")
        for item in claim_audit.get("items", []):
            lines.append(
                f"- {item.get('verdict', '')}: "
                f"{item.get('claim', '').strip()} - {item.get('why', '')}"
            )
    return base + "\n" + "\n".join(lines).rstrip() + "\n"


def citations_from_quote_items(quote_items: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in quote_items:
        citation = str(item.get("citation", "")).strip()
        if citation and citation not in seen:
            seen.add(citation)
            out.append(citation)
    return out


BOOTSTRAP_DOCS = {
    "vqe_and_ansatzes.md": """---
title: VQE and Ansatz Baselines
author: QuantumNovelty starter KB
year: 2026
keywords: vqe ansatz hamiltonian variational quantum eigensolver
---

# VQE and Ansatz Baselines

The variational quantum eigensolver estimates ground-state energies by
preparing a parameterized ansatz circuit and minimizing the expectation value
of a Hamiltonian. A novelty audit should compare any proposed ansatz against
standard baselines such as hardware-efficient ansatz families, UCCSD-inspired
circuits, symmetry-preserving circuits, and problem-informed Trotterized
evolution.

For LLM-in-the-loop discovery, the important evidence is not only the best
energy. The audit should retain parameter counts, CNOT counts, optimizer
budgets, random-seed variance, precision mode, and whether the circuit still
dominates after recently surfaced literature baselines are added.
""",
    "error_correction.md": """---
title: Quantum Error Correction Search Notes
author: QuantumNovelty starter KB
year: 2026
keywords: quantum error correction surface code logical qubit stabilizer
---

# Quantum Error Correction Search Notes

Quantum error correction encodes logical qubits into physical qubits so that
syndrome measurements can reveal errors without directly measuring the logical
state. Surface-code discussions usually involve stabilizers, syndrome
extraction, thresholds, lattice surgery, decoder assumptions, and physical
error models.

When reviewing a claimed error-correction contribution, retrieve evidence for
the stated noise model, threshold definition, decoder, circuit-level versus
phenomenological simulation, and the overhead metric used for comparison.
""",
    "hamiltonian_simulation.md": """---
title: Hamiltonian Simulation and Trotter Evidence
author: QuantumNovelty starter KB
year: 2026
keywords: hamiltonian simulation trotter suzuki product formula qdrift
---

# Hamiltonian Simulation and Trotter Evidence

Hamiltonian simulation methods approximate time evolution under an operator.
Common baseline families include first-order and higher-order Suzuki-Trotter
product formulas, qubitization, Taylor-series methods, and randomized product
formula variants. Any claim about a new ordering or product formula should be
checked against commutation structure, step-size dependence, operator norm
assumptions, and empirical error scaling.
""",
}


def bootstrap_quantum_core(*, kb_root: str | Path | None = None) -> dict[str, Any]:
    root = get_quantum_kb_path(kb_root=kb_root)
    registry = load_registry(root)
    if DEFAULT_KB_ID not in registry.get("knowledge_bases", {}):
        create_kb(
            DEFAULT_KB_ID,
            "Quantum Core",
            "Starter quantum-computing KB for QuantumNovelty RAG workflows.",
            kb_root=root,
            make_default=True,
        )
    cfg = load_kb(DEFAULT_KB_ID, kb_root=root)
    cfg.documents_path.mkdir(parents=True, exist_ok=True)
    for filename, text in BOOTSTRAP_DOCS.items():
        path = cfg.documents_path / filename
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    stats = build_index(DEFAULT_KB_ID, kb_root=root, purge=True)
    return {"kb_root": str(root), "kb_id": DEFAULT_KB_ID, "index_stats": stats}
