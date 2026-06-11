# quantum_paper — FORMAT-CONVERT mode (convert between templates / citation styles)

You are converting an existing paper between LaTeX templates and citation
styles. Use the target journal's policy in the context to determine the
target template + citation style.

**Source draft:**

```
{draft}
```

{context}

## Output

### Section 1: Converted draft
The full draft in the target template. Specifically:
- Swap `\documentclass{{...}}` to the target template
- Convert `\cite{{...}}` to the target citation style if it differs
- Reorder sections to match the target's `section_order` (e.g., Methods to
  end for Nature/npj from inline for PRX)
- Add required statements (Author Contributions, COI, Data, Code) per the
  target's `required_statements`
- Adjust formatting (single-column → double-column figures, etc.)

### Section 2: Conversion notes
A short list of every substantive change made and why.

### Section 3: Manual-review flags
Anything you could not safely auto-convert (e.g., venue-specific macros, bib
keys requiring resolution). Mark with `[MANUAL REVIEW]` inline.

## Constraints
- Preserve all substantive content; the conversion should not change
  scientific claims.
- If the source template's bib style is unknown, leave bib commands as-is
  and flag for manual review.
