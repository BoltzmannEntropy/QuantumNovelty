# quantum_paper — DISCLOSURE mode (generate the venue-required disclosure block)

You are generating the disclosure / required-statements block for a paper,
sized to the target journal's policy. Output LaTeX suitable for direct
inclusion at the document's end.

**Draft (for context — extract relevant facts):**

```
{draft}
```

{context}

## Output

Produce a `\section*{{...}}` block for each item in the target journal's
`required_statements`. Standard statements include:

### Funding
List explicit funding sources with grant numbers, OR write
"This work received no specific external funding."

### Competing Interests
List any financial / employment / consulting / advisory / IP / personal
COIs, OR write "The author declares no competing interests."

### Author Contributions
CRediT-style per-author roles. Include: Conceptualization, Methodology,
Software, Validation, Formal Analysis, Investigation, Resources, Data
Curation, Writing - Original Draft, Writing - Review & Editing,
Visualization, Supervision, Project Administration, Funding Acquisition.

### Data Availability
Where the data lives, accession IDs if any, embargo period, justified
exceptions (privacy / IP / dual-use).

### Code Availability
Repo URL + license + version/commit. Incorporate the chosen quantum-library
from the context block. If the user opted for `no-code`, write "No code was
generated for this work."

### IRB / Ethics (if applicable)
Board name, protocol number, informed-consent status.

### Preprint Status
"This manuscript is not under consideration at any other journal and has
been / has not been posted to a preprint server."

### AI-Use Disclosure
Per journal policy: which AI assistance was used for text drafting / image
generation / data analysis / coding. Be specific (model name, scope,
human-review process). For QuantumNovelty-driven projects, also disclose
the use of the audit-and-falsify framework as a methodological aid.

## Constraints
- Use the EXACT statement headings the target journal requires.
- If a statement does not apply (e.g., no IRB needed for theoretical work),
  include it and write "Not applicable."
- DO NOT invent funding sources, grant numbers, or co-authors.
