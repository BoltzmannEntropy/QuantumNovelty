# quantum_paper — CITATION-CHECK mode (verify cites match claims)

You are auditing the citations in a quantum-computing paper. For each
`\cite{{key}}` (or numerical [N]) in the draft, check:
1. Does the key resolve in the bibliography?
2. Does the cited claim match what the source paper actually established?
3. Is the citation at the right level of specificity (e.g., citing a textbook
   for a result from a recent paper)?

**Draft:**

```
{draft}
```

{context}

## Output

For each citation in the draft, in order of appearance:

### Cite N: `\cite{{KEY}}` — at line/section <where>
- **Surrounding claim (verbatim):** ...
- **Resolves in bibliography?** YES / NO / NOT_CHECKED
- **Claim-to-source fit:** GOOD / WEAK / MISMATCHED / UNVERIFIABLE
- **Issue:** specific problem if any (e.g., "cite is to a 2010 textbook but
  the result was first proven in [Author 2018]")
- **Recommended fix:** specific replacement or addition

## Constraints
- If you cannot verify a cite from the draft text alone, mark UNVERIFIABLE
  — do NOT guess.
- Distinguish citations to foundational textbooks (acceptable) from
  citations to textbooks for very recent results (problematic).
- Flag self-citations as a separate issue if they are concentrated in one
  paragraph.
