# quantum_paper — ABSTRACT-ONLY mode (write an abstract sized to the venue)

You are writing a single abstract for the supplied draft. Size it to the
journal's `abstract_word_limit` policy; if no limit is set, target 200 words.

**Draft:**

```
{draft}
```

{context}

## Output
The abstract only. No "Abstract:" prefix. No section headings. Connected
prose. Within the venue's word limit.

## Style constraints (quantum-specific)
- Include the specific Hamiltonian / problem class (e.g., "H₂O at the
  (4e, 4o) active space, 8 qubits, STO-3G").
- Include the quantitative headline result with units AND simulator
  precision (e.g., "0.005 mHa absolute error at float64 reference").
- Include the comparison baseline by name (e.g., "vs UCCSD-1-Trotter").
- Include the limitation, not just the strength.
- Do NOT use "state-of-the-art" without a specific baseline.
- Do NOT use marketing words ("revolutionary", "groundbreaking").
