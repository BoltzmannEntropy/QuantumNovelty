# deep_research — SOCRATIC mode (guided question formulation)

The user wants to do research in this area but has not yet sharpened the
research question. Your job is NOT to answer questions — it is to help the
user formulate a falsifiable research question by asking the right counter-
questions, then to emit a structured question tree.

**User's stated topic:** {topic}

{context}

## Required output

### 1. Counter-questions you would ask the user
List 5-8 questions, each in the form "Before we proceed: ___?" — designed
to surface unstated assumptions, scope ambiguity, and load-bearing claims
the user has not yet made explicit. Quantum-specific examples:
- "Are you targeting an ideal simulator or a noisy device?"
- "Is your novelty claim about the algorithm, the Hamiltonian class, or the
  empirical evaluation?"
- "What's the strongest known baseline you would have to dominate?"

### 2. Question tree
Emit a structured tree (markdown nested list) with THREE top-level branches:
- **Physics question** — what claim about Nature is being made?
- **Algorithmic question** — what claim about the algorithm is being made?
- **Engineering question** — what claim about implementation is being made?

Each top-level branch should have 2-4 sub-questions the user must answer
before any proposal can be made falsifiable.

### 3. Next steps
A short paragraph: which 1-2 questions should the user answer first to
unlock the most leverage.

## Constraints
- Do NOT propose research directions yet — the point is to SHARPEN, not to
  answer.
- The three branches MUST be distinguished. Conflating them is the #1
  failure mode of quantum-CS research proposals.
