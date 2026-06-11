---

## Voice 1 — Reviewer 1 (Physics correctness)

The MaxCut Hamiltonian itself is mostly correct: \(H_C=\sum_{(i,j)}(I-Z_iZ_j)/2\) has eigenvalues equal to the cut size, and maximizing \(\langle H_C\rangle\) is the right QAOA objective. The mixer \(H_B=\sum_i X_i\) and the circuit ordering are standard. However, the manuscript should be more explicit about sign conventions, dropped global phases, and angle periodicities. The claim that cost angles may be restricted to an interval of length \(\pi\) is not justified as written for the exact \(H_C\) convention; the usual symmetry reductions depend on whether the identity term is retained, whether one works modulo global phase, graph regularity, and global bit-flip symmetries.

Several items in the physics-correctness rubric are not applicable: there is no fermionic Hamiltonian, no active space, no Hartree-Fock reference, and no Jordan-Wigner, Bravyi-Kitaev, or parity mapping. That is fine, but the paper should not leave any ambiguity that this is a combinatorial Ising/QAOA study rather than a chemistry simulation. If the journal form expects chemistry-specific checks, the authors should explicitly state “not applicable” in the reproducibility checklist rather than silently omitting them.

The most serious physics issue is the language around “no longer captured solely by radius-\(p\) tree neighborhoods.” For fixed-depth QAOA on bounded-degree graphs, edge expectations remain exactly light-cone local: the relevant subgraph is still a bounded-radius neighborhood. What changes is whether that neighborhood is tree-like. The draft sometimes conflates “local” with “tree-like,” and that matters because the claimed boundary criterion depends on this distinction. The authors should rewrite the boundary condition as “radius-\(p\) neighborhoods are no longer well approximated by trees at the studied finite \(n\),” if that is what they mean.

Simulator precision is under-specified. The manuscript should state whether amplitudes are complex64, complex128, or mixed precision; how expectation values are accumulated; whether phase application uses stable vectorized kernels; and how numerical error is bounded relative to the reported confidence intervals. At the claimed boundary, small layer gains may be comparable to optimizer and floating-point error. Without precision diagnostics and cross-backend agreement beyond tiny QuTiP examples, the measured \(\Delta_p\) claims are not physically trustworthy.

The QuTiP skeleton is acceptable as pedagogical code, but it is not yet a reproducibility artifact. The identity operator is rebuilt inside the edge loop, the scalar extraction may be version-sensitive, and no test checks exact agreement with brute-force diagonal evaluation. This is not fatal, but Quantum expects methods that make numerical conventions auditable. I would require exact small-\(n\) tests, explicit tolerances, and a table of backend agreement before accepting any boundary-scale claims.

Verdict: 4/10. Recommendation: major-revisions.

## Voice 2 — Reviewer 2 (Algorithmic novelty)

The current novelty claim is not established. The manuscript repeatedly says “subject to novelty_audit,” but a paper cannot outsource its central contribution to a future audit. A reproducible map of QAOA depth versus approximation ratio could be publishable if it is complete, benchmarked against strong current comparators, and contains actual data. In this draft, all decisive empirical values are placeholders, so there is no demonstrated Pareto improvement, no measurable depth threshold, and no evidence that the boundary regime reveals anything not already known from fixed-angle, transfer-parameter, and high-girth QAOA studies.

Recent literature makes the bar fairly high. Farhi, Gutmann, Ranard, and Villalonga, “Lower bounding the MaxCut of high girth 3-regular graphs using the QAOA” (2025, https://arxiv.org/abs/2503.12789), directly studies 3-regular MaxCut and reports depth-dependent QAOA lower bounds. Augustino et al., “Strategies for running the QAOA at hundreds of qubits” (2024, https://arxiv.org/abs/2410.03015), studies tree parameters, warm-starting, and random 3-regular graphs at hundreds of vertices. Li, Su, Yang, and Zhang, “Quantum Approximate Optimization Algorithms for Maximum Cut on Low-Girth Graphs” (2024, https://arxiv.org/abs/2410.04409), examines QAOA and multi-angle QAOA against classical local algorithms on structured low-girth families. The draft cites older foundations but does not engage these recent comparators at the level needed for a novelty claim.

The baseline suite is also too weakly specified. “Greedy local search,” “Goemans-Williamson rounding,” and “selected graph heuristic” are not enough. On random 3-regular MaxCut, simple local improvement, multi-start variants, SDP rounding, message-passing heuristics, and branch-and-cut can have very different profiles. The manuscript needs an explicit strict-domination comparator: approximation ratio, uncertainty, wall-clock, objective evaluations, memory, and success probability should all be compared under calibrated tolerances. As written, even if QAOA beats one named baseline by a small margin, it is unclear whether that would count as a Pareto win.

The ratios must be recomputable from raw values. The manuscript says this will be done through audited JSON, but does not show the schema, keys, or claim-to-data mapping. A reader should be able to recompute every \(\rho_G(p)=F_G/C_{\max}\), every paired baseline difference, and every plotted confidence interval from immutable files. Placeholders prevent assessment of whether normalization is exact, whether failed optimizer runs are included, or whether best-of-many restarts are fairly budgeted.

I am not convinced this is a Quantum-level algorithmic contribution in its current form. The conceptual frame is reasonable, but without actual measurements and a modern baseline audit, it reads as a preregistration document rather than a research article. A future version could become competitive if it demonstrates a clean, reproducible comparison in a regime not already covered by fixed-angle and warm-start studies.

Verdict: 2/10. Recommendation: reject.

## Voice 3 — Reviewer 3 (Empirical evidence)

The empirical evidence is presently absent. Every important number is a placeholder: sample counts, graph sizes, depths, approximation ratios, baseline margins, finite-size exponents, optimizer budgets, wall-clock times, memory footprints, and uncertainty intervals. Because of that, none of the statistical claims can be evaluated. The manuscript has the right vocabulary for an audit-driven empirical paper, but it does not yet contain the empirical object being audited.

The confidence-interval plan is incomplete. Bootstrap intervals over graph instances are appropriate for mean approximation ratios, but the paper also needs binomial-rate reporting for claims such as “QAOA exceeds the baseline on \(K\) of \(N\) instances,” “optimizer succeeded on \(K/N\),” and “boundary runs completed on \(K/N\).” These should use Wilson 95% intervals, especially if \(N\) is small or the rate is near 0 or 1. A mean paired difference can hide the fact that the advantage is concentrated in a small subset of instances.

Multi-seed variance is mentioned but not specified. The authors need to report variance across graph seeds, optimizer seeds, initialization protocols, and sampling seeds if shot-based estimates are introduced later. For each depth, I would expect at least a decomposition of uncertainty into instance-to-instance variation, optimizer stochasticity, and simulator/sampling error. Without that, a small reported \(\Delta_p\) cannot be distinguished from optimizer luck.

The requested ablations are missing. There is no LLM-mutator, commutation-hint, or Pareto-seeding component described in the manuscript. If these are not part of the pipeline, the audit checklist should mark them as not applicable. If they are part of the optimizer or baseline-catalog construction, then on/off ablations are mandatory. In particular, Pareto-seeding could materially bias comparisons if QAOA receives better initialization machinery than the classical baselines.

The paper also lacks an honest-negatives or Failure-Modes section. The Discussion lists limitations, but it does not report failed depths, failed solvers, optimizer-limited cases, non-exceedance of baselines, unstable finite-size fits, or excluded instances. Quantum readers will expect to see what did not work, especially for a boundary paper where negative results are scientifically informative.

Finally, `audit_claims.py` is described but not demonstrated. An acceptable version should include a generated claims table in the manuscript or supplement, with one row per numerical claim, source JSON path, transformation function, uncertainty method, and commit hash. Until that exists, the audit-and-falsify standard is aspirational rather than operational.

Verdict: 3/10. Recommendation: major-revisions.

## Voice 4 — Devil's Advocate

This is not a paper; it is a LaTeX scaffold with placeholders. It asks reviewers to evaluate “measured” ratios that are not measured, “boundary” points that are not defined numerically, and “baseline” comparisons that name neither the actual implementation nor the resource accounting. The abstract itself admits that all empirical quantities are to be populated later. A journal submission with no results should be rejected without technical review.

The title overclaims. “Depth-Approximation-Ratio Trade-offs” suggests a completed quantitative study, while “near the Quantum-Classical Phase Boundary” gives an aura of physical significance to what is just an implementation-dependent simulator-cost threshold. The manuscript later says this is not a phase transition, but the title has already done the rhetorical work. The boundary depends on hardware, simulator, contraction ordering, compiler, CPU/GPU memory, and optimizer budget. Calling this a quantum-classical phase boundary is marketing language unless the authors prove robustness across computational environments.

The central technical criterion is wrong or at least badly muddled. QAOA at depth \(p\) is a local circuit. The expectation of a local edge term is determined by its light cone. This remains true at every finite \(p\). The paper tries to sell a transition where performance is “no longer captured solely by radius-\(p\) tree neighborhoods,” but that is merely the point where random finite graphs stop looking like infinite trees at that radius. That is not a quantum-classical boundary; it is a finite-size graph-cycle crossover.

The baseline comparison is dangerously underdeveloped. Goemans-Williamson is a worst-case approximation algorithm, not necessarily the strongest practical heuristic for random 3-regular MaxCut. “Greedy local search” can be made weak or strong depending on restarts, move neighborhoods, tie-breaking, and time budget. “Selected graph heuristic” is a blank. If the authors later choose weak baselines, the paper becomes a benchmark theater exercise. If they choose strong baselines, QAOA likely will not win at the simulated depths. The current draft leaves itself room to declare victory after seeing the data.

The Methods do not solve the reproducibility problem. They say exact optima will be computed by `<INSERT SOLVER NAME>`, baselines by `<INSERT BASELINE NAME>`, and simulations by `<INSERT SIMULATOR NAME>`. That is not a method. The QuTiP code is a toy skeleton and does not validate the large-scale engine. The manuscript also normalizes by exact optima, which caps \(n\), then simultaneously gestures toward a boundary where exact simulation is hard. This creates a self-imposed bottleneck that may make the study scientifically small.

The paper also fails to establish why Quantum readers need this. The recent QAOA literature already studies tree parameters, transferability, warm starts, high-girth 3-regular bounds, and low-girth structured graphs. This draft does not provide a theorem, a new algorithm, a new simulator, a hardware experiment, a surprising empirical result, or a completed benchmark. It provides a plan to maybe produce one. The appropriate venue for the current document is an internal preregistration, not a peer-reviewed quantum-science journal.

Recommendation: reject. Confidence: 9/10.

## Voice 5 — Editor-in-Chief synthesis

The reviewers agree on the main procedural issue: the manuscript is not reviewable as a completed empirical paper because the decisive quantities are placeholders. Reviewer 1 is comparatively generous because the basic MaxCut Hamiltonian and QAOA formalism are mostly correct. Reviewer 3 is also willing to see this as a major-revisions case if the authors can populate the pipeline. Reviewer 2 and the Devil’s Advocate argue for rejection because novelty and empirical support cannot be assessed. For Quantum, I side with rejection at this stage.

The Devil’s Advocate’s strongest point is the mismatch between the manuscript’s framing and its contents. The title and abstract imply a completed map of a depth-ratio trade-off near a meaningful boundary, but the body contains no measured boundary, no ratios, no table, no figures, no solver identity, and no baseline implementation. Quantum has no page limit and welcomes detailed methods, but it does require a finished scientific claim. A placeholder-driven draft does not meet that standard.

The technical critique about locality also matters. The authors must carefully separate light-cone locality from tree-likeness. Fixed-depth QAOA remains local on bounded-degree graphs; what fails at larger \(p\) and finite \(n\) is the approximation of those local neighborhoods by trees. If the “boundary” is retained, it must be renamed or defined more modestly as an operational calibration frontier, with robustness checks across simulator settings.

The algorithmic novelty burden is substantial. A resubmission must engage recent QAOA MaxCut work, including high-girth 3-regular bounds, tree/fixed-parameter strategies, warm starts, and low-girth graph studies. It must also use strong classical baselines and paired comparisons. A claim like “exceeds the selected baseline” is acceptable only if the selected baseline is justified before looking at results and the comparison is reproducible from raw data.

Final verdict: reject, with encouragement to resubmit only after the empirical study is complete.

1. Replace every placeholder with audited values or explicitly remove the corresponding claim.
2. Provide `audit_claims.py`, raw JSON outputs, claim mapping, commit hash, and regeneration instructions.
3. Define the baseline suite precisely, including implementations, seeds, budgets, and paired statistical tests.
4. Correct the locality/tree-likeness language and either rename or rigorously justify the “phase boundary.”
5. Report simulator precision, backend validation, floating-point tolerances, and small-instance exact checks.
6. Add Wilson 95% intervals for all \(K/N\) rates and decompose variance across graph, optimizer, and sampling seeds.
7. Add honest-negative and failure-mode reporting, including failed solvers, unstable fits, non-exceeded baselines, and optimizer-limited runs.
8. Engage recent literature explicitly, including the 2024-2025 QAOA MaxCut papers named above.

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | major-revisions | 7 |
| Reviewer 2 | reject | 8 |
| Reviewer 3 | major-revisions | 8 |
| Devil's Advocate | reject | 9 |
| Editor-in-Chief | reject | 9 |