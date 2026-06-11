# deep_research — FULL mode (multi-source synthesis with augmented-baseline catalog)

You are doing a comprehensive literature survey on a quantum-computing topic.
Produce a synthesis suitable for direct inclusion in a manuscript's Related
Work section, plus a structured baseline catalog that downstream skills
(`novelty_audit`) will merge with the user's Pareto archive.

**Topic:** {topic}

{context}

## Required deliverables (write in this order)

### 1. Synthesis (~600-900 words)
Connected prose covering:
- Current state of the art for the topic (cite specific papers by Author Year)
- Open problems still unsolved
- Where this topic interfaces with adjacent quantum subfields
- Methodological norms (statistical reporting, simulator precision)

### 2. Baseline catalog (machine-readable; will be parsed)
Emit a single fenced ```json block titled `baseline_catalog` containing:
```json
{{
  "rows": [
    {{ "label": "AuthorYear-Method",
       "energy_ha":   <value or null>,
       "params":      <integer or null>,
       "ops":         <integer or null>,
       "cnots":       <integer or null>,
       "source":      "literature",
       "citation":    "Author et al. (Year). Title. Venue."
    }}
  ]
}}
```
Include rows ONLY for papers reporting numerical values comparable to the
user's Hamiltonian context. If a paper used a different active space / qubit
count, omit it from the catalog and note it in the synthesis as
`out-of-scope-for-comparator`.

### 3. Methodological norms checklist
A short bulleted list noting which papers in the catalog reported:
- Wilson 95% CIs on rate claims
- Multiple random seeds
- Cross-LLM / cross-simulator falsifiability checks
- Honest negatives (failure cases)

This helps the user calibrate how much methodological rigour the venue expects.

## Constraints
- Cite by Author Year only; do NOT invent DOIs or arXiv IDs.
- Distinguish published peer-reviewed work from preprints in the synthesis.
- If you do not know a number, write `null` in the JSON; do NOT guess.
