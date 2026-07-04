"""Unified LLM backend for every QuantumNovelty skill.

Backends (all share the `call_llm(prompt, backend, ...)` signature):

  - "claude"       (default)  Claude Code CLI via subprocess. Uses the user's
                              local Claude Code subscription. No API key.
  - "codex"                   Codex CLI via subprocess. Different vendor, used
                              for cross-LLM falsifiability checks.
  - "codex-acp"               Codex via Agent Client Protocol (acpx). A single
                              persistent session across multiple skill calls.
  - "codex-mcp"               Codex as an MCP client; QuantumNovelty skills are
                              exposed as MCP tools. (Driver registered separately.)
  - "kimi"                    Kimi/Moonshot via the Anthropic-compatible
                              Messages API. Requires KIMI_ENV_FILE or kikm.sh.
  - "anthropic-api"           Anthropic HTTP API. OPT-IN ONLY. Requires
                              ANTHROPIC_API_KEY. The framework will REFUSE to
                              fall back to this from any of the above; you must
                              pass --llm anthropic-api explicitly.

All backends enforce the nested-CLI isolation playbook:
  (1) Scrubbed env: CLAUDE_CODE_*, ANTHROPIC_* (so subscription path is used),
      and CLAUDECODE are removed before subprocess.run().
  (2) Neutral cwd: tempfile.gettempdir() so nested `claude --print` doesn't 400
      with "tool_use ids must be unique".
  (3) Session-persistence off: --no-session-persistence on claude.

If you find a 400 / silent codex fallback / billing-against-API failure mode the
isolation does not cover, file an issue with the reproducer.

This module deliberately has NO external dependencies beyond the Python stdlib.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# =========================================================================
# Public API
# =========================================================================

KNOWN_BACKENDS = (
    "claude", "codex", "codex-acp", "codex-mcp", "kimi", "anthropic-api"
)


@dataclass
class LLMResult:
    """Structured return type for call_llm.

    Always include enough provenance to (a) reproduce the call, (b) detect
    silent fallbacks downstream, (c) account for token cost. The chain's
    audit_backend_fidelity gate reads `backend_actually_used`; the per-stage
    cost rollup (in `process_summary`) reads the token + cost fields.

    Token fields come from `claude --output-format json` when available;
    fall back to char-count proxies (chars/4) when the backend doesn't
    expose usage stats.
    """
    text: str                            # raw model output
    backend_requested: str               # what the caller passed
    backend_actually_used: str           # what actually ran (catches silent fallbacks)
    model_id: str = ""                   # exact model snapshot reported by the CLI
    elapsed_s: float = 0.0
    exit_code: int = 0
    stderr_tail: str = ""                # last ~2 KB of stderr for debugging
    # Usage / cost — populated from CLI JSON when available, else estimated
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    total_cost_usd: float | None = None  # None means "not reported by backend"
    tokens_estimated: bool = False       # True if counts are char/4 proxies
    extras: dict[str, Any] = field(default_factory=dict)

    def as_marker_json(self) -> str:
        """JSON suitable for writing as `_backend_used.json` for audit gates."""
        marker = {
            "backend_requested": self.backend_requested,
            "backend_actually_used": self.backend_actually_used,
            "model_id": self.model_id,
            "elapsed_s": round(self.elapsed_s, 3),
            "exit_code": self.exit_code,
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cache_read_input_tokens": self.cache_read_input_tokens,
                "cache_creation_input_tokens": self.cache_creation_input_tokens,
                "tokens_estimated": self.tokens_estimated,
                "total_cost_usd": self.total_cost_usd,
            },
        }
        # Fallbacks and retries must be visible to audit gates, never silent.
        resilience = self.extras.get("resilience")
        if resilience:
            marker["resilience"] = {
                "fallback_used": bool(resilience.get("fallback_used")),
                "n_failed_attempts": len(resilience.get("attempts", [])),
                "attempts": resilience.get("attempts", []),
            }
        return json.dumps(marker, indent=2)


def call_llm(
    prompt: str,
    backend: str = "claude",
    timeout: int = 600,
    extra_env: dict[str, str] | None = None,
    acp_session: str | None = None,
    retries: int | None = None,
    fallback_backends: list[str] | None = None,
) -> LLMResult:
    """Invoke the chosen backend and return a structured result.

    Raises RuntimeError when every attempt fails. Callers that want to write
    a degraded artefact on failure should catch the RuntimeError and log the
    LLMResult before deciding how to proceed.

    Resilience (adopted from hermes-agent's credential-pool pattern):
      - TRANSIENT errors (timeouts, network errors, HTTP 429/5xx, empty
        output, error envelopes) are retried on the SAME backend with
        exponential backoff. `retries` counts extra attempts after the
        first; default from QN_LLM_RETRIES (2).
      - Cross-backend fallback is STRICTLY OPT-IN, honoring this module's
        no-silent-fallback doctrine: pass `fallback_backends` explicitly or
        set QN_LLM_FALLBACKS (comma-separated, e.g. "kimi,codex"). Every
        attempt is recorded in `extras["resilience"]`, and a fallback is
        visible to the audit_backend_fidelity gate because
        `backend_actually_used` differs from `backend_requested`.
      - "anthropic-api" is never accepted as a fallback target (it is
        opt-in-only by contract); listing it raises ValueError.

    `extra_env`: extra env vars to merge on top of the scrubbed env. Use
    sparingly; prefer routing through `--flag VALUE` over env tunneling.

    `acp_session`: for backend="codex-acp" only — name of the persistent
    session. If None, the session name is derived from os.getpid().
    """
    if not _is_known_backend(backend):
        raise ValueError(
            f"unknown backend {backend!r}; choose from {KNOWN_BACKENDS} "
            "or an explicit kimi-* / moonshot* model id"
        )
    # Test seam: QUANTUMNOVELTY_LLM_STUB shortcuts the entire call. Used by fixtures.
    stub = os.environ.get("QUANTUMNOVELTY_LLM_STUB")
    if stub and Path(stub).is_file():
        stub_text = Path(stub).read_text(encoding="utf-8")
        return LLMResult(
            text=stub_text,
            backend_requested=backend,
            backend_actually_used="stub",
            model_id="stub",
            elapsed_s=0.0,
            input_tokens=max(1, len(prompt) // 4),
            output_tokens=max(1, len(stub_text) // 4),
            tokens_estimated=True,
        )

    if retries is None:
        retries = max(0, int(os.environ.get("QN_LLM_RETRIES", "2")))
    if fallback_backends is None:
        raw = os.environ.get("QN_LLM_FALLBACKS", "")
        fallback_backends = [b.strip() for b in raw.split(",") if b.strip()]
    chain = [backend] + [b for b in fallback_backends if b != backend]
    for fb in chain[1:]:
        if fb == "anthropic-api":
            raise ValueError(
                "anthropic-api is opt-in only and may not be used as a "
                "fallback target (see module docstring); pass --llm "
                "anthropic-api explicitly instead"
            )
        if not _is_known_backend(fb):
            raise ValueError(f"unknown fallback backend {fb!r}")

    import time as _time
    attempts_log: list[dict[str, Any]] = []
    for be in chain:
        for attempt in range(1, retries + 2):
            try:
                result = _dispatch_backend(
                    prompt, be, timeout, extra_env, acp_session
                )
                result.backend_requested = backend
                if attempts_log:
                    result.extras["resilience"] = {
                        "attempts": attempts_log,
                        "fallback_used": be != backend,
                    }
                return result
            except RuntimeError as e:
                transient = _is_transient_error(str(e))
                attempts_log.append({
                    "backend": be,
                    "attempt": attempt,
                    "transient": transient,
                    "error": str(e)[:300],
                })
                if not transient:
                    break  # permanent for this backend; try next in chain
                if attempt <= retries:
                    _time.sleep(min(30.0, float(2 ** attempt)))
    raise RuntimeError(
        f"all backends failed after {len(attempts_log)} attempt(s) "
        f"(chain={chain}); last error: {attempts_log[-1]['error']}"
    )


def _dispatch_backend(
    prompt: str,
    backend: str,
    timeout: int,
    extra_env: dict[str, str] | None,
    acp_session: str | None,
) -> LLMResult:
    """Single-attempt dispatch to one backend (no retry, no fallback)."""
    env = _scrubbed_env()
    if extra_env:
        env.update(extra_env)

    if backend == "claude":
        return _call_claude_cli(prompt, env, timeout)
    if backend == "codex":
        return _call_codex_cli(prompt, env, timeout)
    if backend == "codex-acp":
        return _call_codex_acp(prompt, env, timeout, acp_session)
    if backend == "codex-mcp":
        return _call_codex_mcp(prompt, env, timeout)
    if _is_kimi_backend(backend):
        return _call_kimi(prompt, backend, timeout)
    if backend == "anthropic-api":
        return _call_anthropic_api(prompt, timeout)
    # Should be unreachable given the KNOWN_BACKENDS check above.
    raise AssertionError(f"unhandled backend: {backend}")


_TRANSIENT_MARKERS = (
    "timed out",
    "network error",
    "empty stdout",
    "error envelope",
    "returned no text",
    "result` is empty",
    "overloaded",
    "rate limit",
    "connection",
    "http 429",
    "http 5",
    "temporarily",
)


def _is_transient_error(message: str) -> bool:
    """Classify a backend failure as retry-worthy (vs permanent).

    Permanent failures (missing binary, missing env file, missing API key)
    contain "not found", "requires", or "missing" and should move straight
    to the next backend in the chain instead of burning retries.
    """
    low = message.lower()
    if any(p in low for p in ("not found on path", "requires", "missing")):
        return False
    return any(m in low for m in _TRANSIENT_MARKERS)


# =========================================================================
# Env scrub + neutral cwd — the nested-CLI isolation playbook
# =========================================================================

def _scrubbed_env() -> dict[str, str]:
    """Strip env vars that break nested CLI sessions OR force API billing.

    Removes three prefix groups:
      - CLAUDE_CODE_*  : nested claude --print 400s on these
      - ANTHROPIC_*    : forces API path instead of Claude Code subscription
      - CLAUDECODE     : same family as CLAUDE_CODE_*

    Keeps everything else (PATH, HOME, USER, ANNAS_ARCHIVE_KEY, etc.) so
    skills still see the user's normal toolchain.
    """
    drop_prefixes = ("CLAUDE_CODE_", "ANTHROPIC_")
    drop_exact = {"CLAUDECODE"}
    return {
        k: v for k, v in os.environ.items()
        if not any(k.startswith(p) for p in drop_prefixes)
        and k not in drop_exact
    }


def _neutral_cwd() -> str:
    """Run nested CLIs from a neutral dir to avoid session-id collisions."""
    return tempfile.gettempdir()


def _is_kimi_backend(backend: str) -> bool:
    """Return True for the generic Kimi backend or an explicit Kimi model id."""
    return (
        backend == "kimi"
        or backend == "moonshot"
        or backend.startswith("kimi-")
        or backend.startswith("moonshot")
    )


def _is_known_backend(backend: str) -> bool:
    """Validate fixed backend ids plus explicit Kimi/Moonshot model ids."""
    return backend in KNOWN_BACKENDS or _is_kimi_backend(backend)


# =========================================================================
# Backend: Claude Code CLI (DEFAULT)
# =========================================================================

def _call_claude_cli(prompt: str, env: dict[str, str],
                     timeout: int) -> LLMResult:
    """Invoke `claude --print --output-format json` via subprocess.

    Subscription billing. Flags:
      --print                          headless, no TUI
      --output-format json             return structured response with usage
      --dangerously-skip-permissions   needed for tool use from nested call
      --no-session-persistence         avoid session-id collisions

    The JSON envelope includes:
      result, usage.{input_tokens, output_tokens, cache_*}, total_cost_usd,
      modelUsage[<model-id>], duration_ms, session_id

    On JSON parse failure we degrade to plain text + char-count estimates.
    """
    # Pin a capable model explicitly. Without --model the Claude Code CLI
    # ADAPTIVELY ROUTES by prompt complexity: small prompts silently fall to
    # claude-haiku-4-5 while only large prompts reach Opus. We observed exactly
    # this in a paper-audit run -- the 5-voice panel and fallacy stages got
    # Opus, but the research-quality review and the claim-vs-evidence
    # requirements judge ran on Haiku. For a referee/audit pipeline that is a
    # quality AND reproducibility hole: identical inputs can land on different
    # models run-to-run. We therefore pin every stage to one capable model.
    # Default `opus` matches this codebase's own direct-API default
    # (QN_API_MODEL=claude-opus-4-5) and maximises review quality; override
    # with QN_CLAUDE_MODEL (e.g. `sonnet` for cheaper runs, or a pinned
    # snapshot id for byte-reproducibility). We use an evergreen alias rather
    # than a dated snapshot id (those 404 on retirement). The resolved model is
    # surfaced in each stage's _backend_used.json ledger.
    model = os.environ.get("QN_CLAUDE_MODEL", "opus")
    cmd = [
        "claude", "--print",
        "--output-format", "json",
        "--model", model,
        "--dangerously-skip-permissions",
        "--no-session-persistence",
        # Nested calls are pure text generation. If the model attempts a
        # tool call, the extra turn can trip the API's "tool_use ids must
        # be unique" 400 (observed whenever a prompt nudges file access —
        # e.g. reviewer personas told to "read the complete paper").
        # Disabling the tool set removes that failure class entirely.
        "--tools", "",
    ]
    result = _run_subprocess(cmd, prompt, env, timeout,
                             backend_requested="claude",
                             backend_actually_used="claude")
    # Parse the JSON envelope: result.text currently holds the WHOLE JSON.
    # Replace it with just the `result` field; populate usage stats.
    envelope_error = None
    try:
        envelope = json.loads(result.text)
        # The CLI can exit 0 while reporting an API error INSIDE the
        # envelope (is_error / non-success subtype, e.g. a 400 or
        # error_max_turns). Treating that as model output corrupts every
        # downstream artifact while the chain reports success.
        if isinstance(envelope, dict):
            subtype = envelope.get("subtype")
            if envelope.get("is_error") or subtype not in (None, "success"):
                envelope_error = (
                    f"claude returned an error envelope "
                    f"(subtype={subtype!r}): "
                    f"{str(envelope.get('result'))[:500]}"
                )
        if isinstance(envelope, dict) and "result" in envelope:
            result.text = envelope["result"] or ""
            usage = envelope.get("usage", {}) or {}
            result.input_tokens = int(usage.get("input_tokens", 0) or 0)
            result.output_tokens = int(usage.get("output_tokens", 0) or 0)
            result.cache_read_input_tokens = int(
                usage.get("cache_read_input_tokens", 0) or 0)
            result.cache_creation_input_tokens = int(
                usage.get("cache_creation_input_tokens", 0) or 0)
            cost = envelope.get("total_cost_usd")
            if isinstance(cost, (int, float)):
                result.total_cost_usd = float(cost)
            mu = envelope.get("modelUsage") or {}
            if isinstance(mu, dict) and mu:
                # The CLI may list MULTIPLE models: the pinned model that did
                # the main generation PLUS a tiny internal helper call (often
                # claude-haiku for titling/summarisation). `next(iter(...))`
                # picked an arbitrary first key, so the ledger could record
                # `haiku` for a stage that actually ran on `opus`. Attribute
                # the stage to the model that produced the most output tokens.
                def _out_tokens(v: object) -> int:
                    if isinstance(v, dict):
                        return int(v.get("outputTokens")
                                   or v.get("output_tokens")
                                   or v.get("tokens") or 0)
                    return 0
                result.model_id = max(mu.keys(),
                                      key=lambda k: _out_tokens(mu[k]))
    except (json.JSONDecodeError, ValueError):
        # Backend returned non-JSON despite the flag — keep raw text and
        # fall back to char-count token estimates.
        result.tokens_estimated = True
        result.input_tokens = max(1, len(prompt) // 4)
        result.output_tokens = max(1, len(result.text) // 4)
    # Raised OUTSIDE the try/except so the JSONDecodeError handler can't
    # swallow these:
    if envelope_error:
        raise RuntimeError(f"backend claude: {envelope_error}")
    if not result.text.strip():
        raise RuntimeError(
            "backend claude: envelope parsed but `result` is empty"
        )
    return result


# =========================================================================
# Backend: Codex CLI subprocess
# =========================================================================

def _call_codex_cli(prompt: str, env: dict[str, str],
                    timeout: int) -> LLMResult:
    """Invoke codex via `codex exec` reading prompt from stdin.

    Codex CLI does NOT surface token usage in plain mode, so the result
    carries char/4 estimates flagged with `tokens_estimated=True`.
    """
    cmd = ["codex", "exec", "--skip-git-repo-check", "-"]
    result = _run_subprocess(cmd, prompt, env, timeout,
                             backend_requested="codex",
                             backend_actually_used="codex")
    result.tokens_estimated = True
    result.input_tokens = max(1, len(prompt) // 4)
    result.output_tokens = max(1, len(result.text) // 4)
    return result


# =========================================================================
# Backend: Codex via Agent Client Protocol (persistent session)
# =========================================================================

def _call_codex_acp(prompt: str, env: dict[str, str],
                    timeout: int,
                    acp_session: str | None) -> LLMResult:
    """Invoke codex through `acpx` with a persistent session.

    The session persists across multiple call_llm invocations as long as the
    caller passes the same `acp_session` name. Useful for long chains where
    later skills consume context the earlier skills established.

    Requires `acpx` on PATH and a configured codex agent. If acpx is missing,
    we raise RuntimeError rather than silently downgrading.
    """
    if not _binary_exists("acpx"):
        raise RuntimeError(
            "backend codex-acp requires `acpx` on PATH "
            "(https://github.com/zed-industries/agent-client-protocol). "
            "Install it or pick --llm codex for a non-persistent codex call."
        )
    session = acp_session or f"quantumnovelty_pid{os.getpid()}"
    cmd = ["acpx", "--agent", "codex", "--session", session, "--prompt", "-"]
    res = _run_subprocess(cmd, prompt, env, timeout,
                          backend_requested="codex-acp",
                          backend_actually_used="codex-acp")
    res.extras["acp_session"] = session
    return res


# =========================================================================
# Backend: Codex via MCP (Model Context Protocol)
# =========================================================================

def _call_codex_mcp(prompt: str, env: dict[str, str],
                    timeout: int) -> LLMResult:
    """Invoke codex as an MCP client; QN skills are exposed as MCP tools.

    For inline calls (not interactive), this is a thin wrapper over codex CLI
    with the QN MCP server registered. The server itself is defined in
    `skills/common/mcp_server.py` (a separate process; not invoked by this
    function). Here we just spawn `codex` with the MCP server pre-registered
    and the prompt on stdin.

    This is mostly useful when the human is driving codex interactively and
    wants the QN skill catalog available as tools; the call_llm wrapper is
    provided for parity with the other backends.
    """
    if not _binary_exists("codex"):
        raise RuntimeError("codex CLI not found on PATH")
    mcp_config = _ensure_mcp_config()
    cmd = [
        "codex", "exec",
        "--skip-git-repo-check",
        "--mcp-config", str(mcp_config),
        "-",
    ]
    res = _run_subprocess(cmd, prompt, env, timeout,
                          backend_requested="codex-mcp",
                          backend_actually_used="codex-mcp")
    res.extras["mcp_config"] = str(mcp_config)
    return res


def _ensure_mcp_config() -> Path:
    """Write a per-process MCP config exposing the QN skill catalog.

    The MCP server itself is a separate process started on demand by codex
    when it wants to call a tool. See `skills/common/mcp_server.py`.
    """
    repo_root = Path(__file__).resolve().parents[2]
    mcp_server = repo_root / "skills" / "common" / "mcp_server.py"
    if not mcp_server.is_file():
        raise RuntimeError(
            "backend codex-mcp: skills/common/mcp_server.py is not shipped "
            "in this release — use --llm claude (default) or --llm codex"
        )
    config = {
        "mcpServers": {
            "quantumnovelty": {
                "command": sys.executable,
                "args": [str(mcp_server)],
            }
        }
    }
    cfg_path = Path(tempfile.gettempdir()) / f"qn_mcp_{os.getpid()}.json"
    cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return cfg_path


# =========================================================================
# Backend: Kimi / Moonshot Anthropic-compatible Messages API
# =========================================================================

def _find_kimi_env_file() -> Path | None:
    """Locate kikm.sh. KIMI_ENV_FILE wins; otherwise search upward.

    The DSS root normally holds kikm.sh. We search from both the caller's cwd
    and this module's location so QN works when launched from DSS, QN's repo
    root, a skill directory, or a workflow wrapper.
    """
    explicit = os.environ.get("KIMI_ENV_FILE")
    if explicit and Path(explicit).is_file():
        return Path(explicit)

    starts = [Path.cwd(), Path(__file__).resolve()]
    seen: set[Path] = set()
    for start in starts:
        base = start if start.is_dir() else start.parent
        for parent in (base, *base.parents):
            if parent in seen:
                continue
            seen.add(parent)
            cand = parent / "kikm.sh"
            if cand.is_file():
                return cand
    return None


def _parse_kimi_env_file(path: Path) -> dict[str, str]:
    """Parse ANTHROPIC_* exports from kikm.sh without sourcing shell code."""
    overrides: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*export\s+(ANTHROPIC_[A-Z_]+)=(.+)", line)
        if not m:
            continue
        value = m.group(2).strip().strip('"').strip("'")
        overrides[m.group(1)] = value
    return overrides


def _kimi_env_overrides() -> tuple[dict[str, str], Path]:
    """Load the Kimi/Moonshot gateway configuration from kikm.sh."""
    env_file = _find_kimi_env_file()
    if not env_file:
        raise RuntimeError(
            "Kimi env file not found "
            "(set KIMI_ENV_FILE=/path/to/kikm.sh)"
        )
    overrides = _parse_kimi_env_file(env_file)
    if not overrides.get("ANTHROPIC_BASE_URL") or not (
        overrides.get("ANTHROPIC_AUTH_TOKEN")
        or overrides.get("ANTHROPIC_API_KEY")
    ):
        raise RuntimeError(
            f"Kimi env file {env_file} missing "
            "ANTHROPIC_BASE_URL / AUTH_TOKEN"
        )
    return overrides, env_file


def _call_kimi(prompt: str, backend: str, timeout: int) -> LLMResult:
    """Invoke Kimi/Moonshot directly over the Messages API.

    `kimi-k2.7-code` requires `thinking: enabled`, which the Claude CLI path
    cannot express. This backend therefore uses direct HTTP while preserving
    QN's structured `_backend_used.json` provenance.
    """
    import time
    import urllib.error
    import urllib.request

    env, env_file = _kimi_env_overrides()
    base_url = env["ANTHROPIC_BASE_URL"].rstrip("/")
    token = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY")
    model = os.environ.get(
        "QN_KIMI_MODEL",
        env.get("ANTHROPIC_MODEL", "kimi-k2.7-code"),
    )
    if backend not in ("kimi", "moonshot"):
        model = backend

    max_tokens = int(os.environ.get(
        "QN_KIMI_MAX_TOKENS",
        os.environ.get("KIMI_MAX_TOKENS", "16384"),
    ))
    thinking_budget = int(os.environ.get(
        "QN_KIMI_THINKING_BUDGET",
        os.environ.get("KIMI_THINKING_BUDGET", "4096"),
    ))
    if thinking_budget >= max_tokens:
        max_tokens = thinking_budget + 4096

    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": token or "",
            "authorization": f"Bearer {token or ''}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8")[:500]
        except Exception:
            detail = ""
        raise RuntimeError(
            f"Kimi call failed ({model}): HTTP {e.code} {e.reason} {detail}"
        ) from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"Kimi network error ({model}): {e}") from e
    elapsed = time.monotonic() - t0

    parts = [
        block.get("text", "")
        for block in payload.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    text = "".join(parts).strip()
    if not text:
        raise RuntimeError(f"Kimi returned no text content ({model})")

    usage = payload.get("usage") or {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    tokens_estimated = not (input_tokens or output_tokens)
    if tokens_estimated:
        input_tokens = max(1, len(prompt) // 4)
        output_tokens = max(1, len(text) // 4)

    return LLMResult(
        text=text,
        backend_requested=backend,
        backend_actually_used="kimi",
        model_id=payload.get("model", model),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=int(
            usage.get("cache_read_input_tokens", 0) or 0
        ),
        cache_creation_input_tokens=int(
            usage.get("cache_creation_input_tokens", 0) or 0
        ),
        elapsed_s=elapsed,
        tokens_estimated=tokens_estimated,
        extras={
            "env_file": str(env_file),
            "max_tokens": max_tokens,
            "thinking_budget": thinking_budget,
        },
    )


# =========================================================================
# Backend: Anthropic API (OPT-IN ONLY; refuses to be a silent fallback)
# =========================================================================

def _call_anthropic_api(prompt: str, timeout: int) -> LLMResult:
    """Invoke the Anthropic HTTP API. Requires ANTHROPIC_API_KEY explicitly.

    NOT enabled by default and NOT used as a fallback from any other backend.
    The framework's philosophy is to route through the Claude Code subscription;
    the API path exists only for CI runs where Claude Code is not installable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "backend anthropic-api requires ANTHROPIC_API_KEY in env. "
            "Note: the framework's default is the Claude Code CLI subscription "
            "path; only use --llm anthropic-api if you genuinely cannot install "
            "Claude Code (e.g. CI). API runs are metered; subscription runs are "
            "flat-rate."
        )
    import urllib.request
    import urllib.error
    import time
    body = json.dumps({
        "model": os.environ.get("QN_API_MODEL", "claude-opus-4-5"),
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "Anthropic-Version": "2023-06-01",
        },
        method="POST",
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"anthropic-api HTTP error {e.code}: {e.reason}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"anthropic-api network error: {e}")
    elapsed = time.monotonic() - t0
    text = "".join(b.get("text", "") for b in data.get("content", []))
    usage = data.get("usage") or {}
    return LLMResult(
        text=text,
        backend_requested="anthropic-api",
        backend_actually_used="anthropic-api",
        model_id=data.get("model", ""),
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        elapsed_s=elapsed,
    )


# =========================================================================
# Shared subprocess wrapper
# =========================================================================

def _run_subprocess(
    cmd: list[str],
    prompt: str,
    env: dict[str, str],
    timeout: int,
    backend_requested: str,
    backend_actually_used: str,
) -> LLMResult:
    """One place that runs all subprocess-based backends.

    On non-zero exit OR empty stdout, raises RuntimeError so callers can decide
    how to handle failure (NEVER silently fall back to a different backend —
    that masquerades as success).
    """
    import time
    if not _binary_exists(cmd[0]):
        raise RuntimeError(
            f"{cmd[0]} not found on PATH "
            f"(needed for backend {backend_requested})"
        )
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
            cwd=_neutral_cwd(),
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"backend {backend_requested}: timed out after {timeout}s"
        )
    elapsed = time.monotonic() - t0
    stderr_tail = (proc.stderr or "")[-2048:]
    if proc.returncode != 0:
        # claude --print reports API errors INSIDE the stdout JSON envelope
        # (result field) with an empty stderr — surface stdout too, or the
        # error reads as a blank failure and misdirects debugging.
        stdout_tail = (proc.stdout or "")[-1024:]
        raise RuntimeError(
            f"backend {backend_requested}: exit={proc.returncode}; "
            f"stderr_tail=\n{stderr_tail}\n"
            f"stdout_tail=\n{stdout_tail}"
        )
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError(
            f"backend {backend_requested}: empty stdout; "
            f"stderr_tail=\n{stderr_tail}"
        )
    return LLMResult(
        text=out,
        backend_requested=backend_requested,
        backend_actually_used=backend_actually_used,
        elapsed_s=elapsed,
        exit_code=proc.returncode,
        stderr_tail=stderr_tail,
    )


def _binary_exists(name: str) -> bool:
    """Return True iff `name` is an executable on $PATH."""
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d:
            continue
        p = Path(d) / name
        if p.is_file() and os.access(p, os.X_OK):
            return True
    return False


# =========================================================================
# Convenience: write the backend-used marker
# =========================================================================

def write_backend_marker(outdir: Path, result: LLMResult) -> Path:
    """Persist `_backend_used.json` in `outdir` for audit_backend_fidelity.

    Returns the path written. Idempotent — overwrites any prior marker.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    marker = outdir / "_backend_used.json"
    marker.write_text(result.as_marker_json(), encoding="utf-8")
    return marker


# =========================================================================
# CLI driver — `python -m skills.common.llm --backend claude --prompt FILE`
# =========================================================================

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Invoke one of QuantumNovelty's LLM backends with a prompt."
    )
    ap.add_argument(
        "--backend",
        default="claude",
        help=(
            "backend id; one of "
            f"{', '.join(KNOWN_BACKENDS)}, or an explicit kimi-* / moonshot* "
            "model id"
        ),
    )
    ap.add_argument("--prompt-file", required=True, type=Path,
                    help="path to a UTF-8 file containing the prompt")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out", type=Path, default=None,
                    help="if set, write stdout to this path; else print to stdout")
    ap.add_argument("--marker-dir", type=Path, default=None,
                    help="if set, write _backend_used.json into this dir")
    ap.add_argument("--acp-session", default=None)
    args = ap.parse_args()

    prompt = args.prompt_file.read_text(encoding="utf-8")
    try:
        res = call_llm(prompt, backend=args.backend, timeout=args.timeout,
                       acp_session=args.acp_session)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)
    if args.out:
        args.out.write_text(res.text, encoding="utf-8")
        print(f"wrote {args.out} ({len(res.text)} chars, "
              f"backend={res.backend_actually_used}, "
              f"elapsed={res.elapsed_s:.1f}s)")
    else:
        sys.stdout.write(res.text)
    if args.marker_dir:
        write_backend_marker(args.marker_dir, res)
