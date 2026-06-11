# quantum_paper — REVISION mode (apply reviewer comments to a draft)

You are applying reviewer comments to an existing draft. Output the revised
LaTeX (or markdown) AND a response-to-reviewers letter keyed to comment numbers.

**Current draft:**

```
{draft}
```

**Reviewer comments:**

```
{reviewer_comments}
```

{context}

## Output

### Revised draft (full)
The complete revised paper. Mark all substantive changes with `% R1: <comment>`
inline comments so the user can review them.

### Response-to-reviewers letter (separate; emit after `===RESPONSE===` separator)
For each numbered reviewer comment:
- **Comment N (verbatim from reviewer):** ...
- **Response:** What was changed and why
- **Change location:** Section / paragraph / line in the revised draft

If a comment was deliberately NOT actioned, explain why with technical
specificity. "We respectfully disagree because the requested ablation is
out of scope (see Section X)" is fine; "Comment noted" is not.

## Constraints
- DO NOT silently drop reviewer comments; every comment gets a response.
- Distinguish ACTIONED / PARTIALLY-ACTIONED / NOT-ACTIONED with rationale.
- Do NOT inflate claims to please reviewers; if a reviewer demanded a claim
  the data does not support, decline politely with the audit-and-falsify
  framework citation as the methodological backing.
