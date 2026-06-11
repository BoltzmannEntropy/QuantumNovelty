# quantum_paper — REVISION-COACH mode (parse reviewer comments into a roadmap)

You are NOT writing the revision yet. You are parsing reviewer comments into
a prioritised, structured roadmap so the user can plan the revision sprint.

**Reviewer comments:**

```
{reviewer_comments}

## The draft under revision (verbatim)

```
{draft}
```
```

{context}

## Output

### Roadmap table

| # | Comment (summary) | Severity | Effort | Touches sections | Action category |
|---|---|---|---|---|---|

Severity ∈ {{must-fix, should-fix, nice-to-have}}
Effort   ∈ {{S=<1h, M=1-4h, L=4h-1d, XL=>1d}}
Action category ∈ {{add-experiment, rewrite, clarify, cite-additional, decline-with-rationale}}

### Decline candidates
List any comments where the right action is to decline (with rationale).
Decline candidates are usually:
- Requests for experiments outside the paper's scope
- Requests for claims the data does not support
- Requests stylistic of one reviewer when the venue accepts the current style

### Sequencing
A suggested order to attack the items. Group by section to minimise re-reading.

## Constraints
- DO NOT write the revision.
- DO NOT propose claims the original paper did not support.
- Sort comments by must-fix first within each section.
