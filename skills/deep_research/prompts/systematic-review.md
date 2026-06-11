# deep_research — SYSTEMATIC REVIEW mode (PRISMA-style on a quantum subtopic)

You are conducting a systematic literature review following PRISMA-2020,
adapted for quantum-computing methodology. Be explicit about every inclusion
and exclusion.

**Topic / research question:** {topic}

{context}

## Required deliverables

### 1. Search strategy
List the search terms you would use across CrossRef + arXiv + Semantic Scholar.

### 2. Inclusion criteria (must satisfy ALL)
- Topic relevance to the research question
- Hamiltonian-class match to the user's context (if a context was given)
- Peer-reviewed publication OR widely cited preprint
- Reported numerical results comparable on at least one axis (energy, gate
  count, fidelity, time)

### 3. Exclusion criteria
- System-size mismatch (different qubit count or active space)
- Methods only / no quantitative result
- Withdrawn / retracted

### 4. PRISMA flow
A table of:
| Stage | n papers in | n excluded | reason | n out |

### 5. Included papers (the survivors)
For each, one paragraph covering: contribution, method, key numerical result
(with units), strengths, limitations.

### 6. Synthesis
What the included papers collectively establish + what remains open.

## Constraints
- Do NOT include papers you have not actually read.
- Mark every numerical claim with the source paper's reported precision/CI.
- If the inclusion list is empty, say so — empty reviews are valid PRISMA outputs.
