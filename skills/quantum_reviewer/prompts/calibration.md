# quantum_reviewer — CALIBRATION against a gold set

You are calibrating the reviewer panel against a user-supplied gold set of
known-good and known-flawed quantum-computing papers. The user provides:
(a) a directory of papers with their known labels (in
filename suffix or sidecar JSON)
(b) the current draft for which the panel's verdict needs calibration

This is a meta-task: report the panel's reliability metrics.

**Draft under calibration:**

```
{draft}
```

{context}

## Output

### Section 1: Gold-set assessment
For each paper in the gold set (provided separately as --gold-set DIR):
- Paper title / filename
- Known label (gold)
- Panel verdict (rerun the full panel mentally)
- Match? YES / NO

(In practice the user runs this skill once per gold paper and aggregates
the JSON; this prompt assesses one round.)

### Section 2: Confusion matrix
For the gold set as a whole:
- True-accepts / False-accepts
- True-rejects / False-rejects
- Precision and recall against gold

### Section 3: Bias detection
Specific systematic biases you observe:
- "panel too generous on novelty"
- "panel too strict on presentation"
- "panel undervalues honest negatives"
etc.

### Section 4: Calibration recommendations
Specific rubric adjustments to bring the panel's verdict distribution closer
to the gold set.

## Constraints
- DO NOT inflate the panel's accuracy.
- Recommend rubric adjustments to the FRAMEWORK, not to the gold set
  ("the panel undervalues X, so the framework should weight X more").
