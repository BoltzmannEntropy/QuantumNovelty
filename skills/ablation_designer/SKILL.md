# `ablation_designer` — design controlled ablations

Designs and runs the ablation tests that distinguish "the LLM contributed" from
"random would have worked".

**Standard ablations:**
1. LLM mutator OFF (random grammar-respecting mutations) vs ON.
2. Commutation-hint OFF vs ON in the prompt.
3. Pareto-front seeding OFF vs ON.
4. Cross-LLM swap (same prompt, different vendor).

**Inputs:** `--axis NAME`, `--seeds LIST`, `--proposals-per-seed N`,
  `--hamiltonian ID`
**Outputs:** `ablation_results.json`, `interpretation.md` (LLM-drafted reading
  of which ablation axes were load-bearing)

The interpretation is provisional; the audit-and-falsify framework subsequently
checks that the manuscript's claims about which ablations were load-bearing
match the JSON evidence.
