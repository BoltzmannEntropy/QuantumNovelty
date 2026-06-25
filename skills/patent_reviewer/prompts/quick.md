# patent_reviewer — quick examination triage

A fast, single-voice patentability triage of a quantum-computing patent
document (not a full Office Action). Use for a first-pass screen.

**Document status:** {status_line}

**Patent under examination ({n_claims} claims):**

```
{patent}
```

{art_unit_block}

Produce a concise triage memo:

1. **What is claimed** — one paragraph: the independent claims' core subject
   matter (hardware? algorithm? method of manufacture?).
2. **§ 101 risk** — abstract-idea / law-of-nature exposure under Alice/Mayo,
   high/medium/low with one sentence of reasoning.
3. **§ 102/103 risk** — the most likely anticipating or rendering-obvious
   prior art (name specific references if you can), high/medium/low.
4. **§ 112 risk** — enablement / definiteness flags for the broad functional
   or quantum-fidelity language, high/medium/low.
5. **Quantum operability** — any physics red flags (no-cloning, Holevo,
   unjustified speedup / fault-tolerance claims), or "sound engineering".
6. **Likely first disposition** — one line, exactly:
   `Disposition: <allowance | non-final-rejection | final-rejection | restriction-requirement>`

Reason under patent law, not peer-review standards. Keep it under ~600 words.
