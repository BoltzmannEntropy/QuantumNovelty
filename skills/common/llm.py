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
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# =========================================================================
# Public API
# =========================================================================

KNOWN_BACKENDS = ("claude", "codex", "codex-acp", "codex-mcp", "anthropic-api")


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
        return json.dumps({
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
        }, indent=2)


def call_llm(
    prompt: str,
    backend: str = "claude",
    timeout: int = 600,
    extra_env: dict[str, str] | None = None,
    acp_session: str | None = None,
) -> LLMResult:
    """Invoke the chosen backend and return a structured result.

    Raises RuntimeError on non-zero exit or empty output. Callers that want
    to write a degraded artefact on failure should catch the RuntimeError and
    log the LLMResult before deciding how to proceed.

    `extra_env`: extra env vars to merge on top of the scrubbed env. Use
    sparingly; prefer routing through `--flag VALUE` over env tunneling.

    `acp_session`: for backend="codex-acp" only — name of the persistent
    session. If None, the session name is derived from os.getpid().
    """
    if backend not in KNOWN_BACKENDS:
        raise ValueError(
            f"unknown backend {backend!r}; choose from {KNOWN_BACKENDS}"
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
    if backend == "anthropic-api":
        return _call_anthropic_api(prompt, timeout)
    # Should be unreachable given the KNOWN_BACKENDS check above.
    raise AssertionError(f"unhandled backend: {backend}")


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
    cmd = [
        "claude", "--print",
        "--output-format", "json",
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
                # The first key is the snapshot ID (e.g. claude-opus-4-5-20251101)
                result.model_id = next(iter(mu.keys()))
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
    ap.add_argument("--backend", default="claude", choices=KNOWN_BACKENDS)
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
