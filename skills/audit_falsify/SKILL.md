# `audit_falsify` — strict-domination comparator + claim audit primitives

The low-level primitives that `novelty_audit` builds on. Surfaced as its own
skill so other audit pipelines can compose the same primitives independently.

**Provides:**
- `strict_dominates(row_a, row_b, axes, eps_abs, eps_rel) -> bool`
- `classify_row(row, others, axes, ...) -> verdict`
- `wilson_interval(k, n) -> (lo, hi)`
- ratio-recompute scanner for draft text
- audit-script generator

Same Python API is available by `import` from `skills/audit_falsify/` (implementation pending — run.sh is a documented placeholder)
(equivalent surface as `skills/novelty_audit/skill.py` exposes); the CLI wraps
it for chain composition.

**When to use directly:** when you are auditing a paper whose Pareto archive
is structured differently from what `novelty_audit` expects, or when you want
to write a custom verdict policy.
