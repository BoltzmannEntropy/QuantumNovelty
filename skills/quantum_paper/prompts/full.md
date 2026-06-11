# quantum_paper — FULL mode (write a complete draft)

You are writing a complete first draft of a quantum-computing paper. Output
valid LaTeX matching the target journal's preferred template. Methods
section placement, citation style, and required statements follow the
journal policy in the context block.

**Topic:** {topic}

{context}

## Structure
Follow the journal's `section_order` policy from the context. If no journal
was specified, use: Abstract → Introduction → Methods → Results → Discussion
→ Conclusion → Acknowledgments → References.

## Constraints
- Use the LaTeX template specified in the journal policy.
- Use the citation style specified in the journal policy.
- Include placeholders `[INSERT FIG REF]`, `[INSERT TABLE REF]` where the
  user will paste in their own figure/table sources.
- Use placeholder citations of the form `\cite{Author2024Method}` — the user
  will resolve these against their bibliography.
- Include the journal's required-statements sections at the appropriate
  position (end-of-paper for Nature/npj/Communications Physics; inline for
  PRX/PRL/PRA).
- Aim for the journal's word/page limits; if no limit is set, target ~5000-
  8000 words for the main text.
- Use roman-numeral enumerate `\begin{enumerate}[label=(\roman*)]` (load
  `enumitem`) for in-text lists; do NOT use bullet itemize for substantive
  enumeration.

## Do NOT
- Invent specific numerical results. Leave `<INSERT MEASURED VALUE>` where
  empirical numbers should appear; the user wires these in from their
  on-disk JSON via `novelty_audit`'s `audit_claims.py` integration.
- Claim novelty without flagging that `novelty_audit` should verify the
  claim against the augmented baseline catalog.
- Use the phrase "state-of-the-art" without naming the specific baseline.
