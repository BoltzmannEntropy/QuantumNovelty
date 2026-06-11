# quantum_paper — OUTLINE-ONLY mode (section-by-section outline + word budget)

You are producing a section outline ONLY — no prose drafting. The output is
both human-readable (markdown) and machine-readable (a fenced ```json block).

**Topic:** {topic}

{context}

## Output

### Section 1: Outline (markdown)
For each section in the journal's `section_order`:
- **Section name**
- One-paragraph purpose
- 3-5 key claims this section will support
- Word target

### Section 2: Word-budget table

| Section | Word target | Notes |
|---|---|---|

Total should match the journal's `body_word_limit` (use a conservative
distribution if no limit is set).

### Section 3: Machine-readable JSON

```json
{{
  "sections": [
    {{"name": "Introduction",
      "purpose": "...",
      "key_claims": ["...", "..."],
      "word_target": [600, 800]}}
  ]
}}
```

## Constraints
- Section names MUST match the journal's `section_order`.
- Word targets MUST sum within the journal's `body_word_limit` (±10%).
- Use [lo, hi] ranges, not single numbers.
