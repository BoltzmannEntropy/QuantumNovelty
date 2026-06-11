"""Built-in numpy-only ansatz evaluator for pareto_explorer.

Self-contained: a dense statevector simulator (<= 10 qubits), a small
Hamiltonian registry, and an SPSA optimizer. No quantum SDK required —
candidates are JSON gate lists, not framework code, so LLM proposals are
data, never executed.

Gate-list DSL (what the LLM emits inside a ```json fence):

    {"name": "g1-s1",
     "gates": [
       {"gate": "ry",   "q": 0, "param": 0},
       {"gate": "cnot", "control": 0, "target": 1},
       {"gate": "rz",   "q": 1, "param": 1}
     ]}

Gates: rx / ry / rz (rotation, takes "param": index into the shared
parameter vector), h / x / z (fixed), cnot / cz (control+target).
Parameter count = max param index + 1.

Metrics returned per candidate:
    energy_ha        optimized <H> (lower is better; E_exact is fixed)
    energy_error_ha  energy_ha - exact ground energy (>= 0 up to SPSA noise)
    params / ops / cnots
    e_exact_ha       dense-diagonalization ground truth

Hamiltonian registry (IDs parsed as NAME_<n>q...):
    TFIM_<n>q        transverse-field Ising, J=1, h=1, open chain
    HEISENBERG_<n>q  isotropic Heisenberg, J=1, open chain
    H2_2q            2-qubit tapered H2 @ R=0.7414 A (published BK-tapered
                     coefficients; E_0 = -1.85728 Ha)
"""
from __future__ import annotations

import json
import re
from typing import Any

import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H_GATE = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)

MAX_QUBITS = 10


def _kron_term(paulis: dict[int, np.ndarray], n: int) -> np.ndarray:
    out = np.array([[1.0 + 0j]])
    for q in range(n):
        out = np.kron(out, paulis.get(q, I2))
    return out


def build_hamiltonian(ham_id: str) -> tuple[np.ndarray, int]:
    """Return (dense H, n_qubits) for a registry ID."""
    m = re.match(r"^(TFIM|HEISENBERG)_(\d+)q", ham_id, re.IGNORECASE)
    if m:
        name, n = m.group(1).upper(), int(m.group(2))
        if not 2 <= n <= MAX_QUBITS:
            raise ValueError(f"{ham_id}: qubit count must be 2..{MAX_QUBITS}")
        dim = 2 ** n
        H = np.zeros((dim, dim), dtype=complex)
        if name == "TFIM":
            for q in range(n - 1):
                H -= _kron_term({q: Z, q + 1: Z}, n)
            for q in range(n):
                H -= _kron_term({q: X}, n)
        else:
            for q in range(n - 1):
                for P in (X, Y, Z):
                    H += _kron_term({q: P, q + 1: P}, n)
        return H, n
    if re.match(r"^H2_2q", ham_id, re.IGNORECASE):
        # O'Malley et al., PRX 6, 031007 (2016), Table 1 @ R = 0.7414 A
        # (BK-tapered 2-qubit H2). Published coefficients.
        g = (-1.052373245772859, 0.39793742484318045,
             -0.39793742484318045, -0.01128010425623538,
             0.18093119978423156)
        H = (g[0] * _kron_term({}, 2)
             + g[1] * _kron_term({0: Z}, 2)
             + g[2] * _kron_term({1: Z}, 2)
             + g[3] * _kron_term({0: Z, 1: Z}, 2)
             + g[4] * _kron_term({0: X, 1: X}, 2))
        return H, 2
    raise ValueError(
        f"unknown Hamiltonian ID {ham_id!r}; built-in registry: "
        f"TFIM_<n>q, HEISENBERG_<n>q (n=2..{MAX_QUBITS}), H2_2q")


def exact_ground_energy(H: np.ndarray) -> float:
    return float(np.linalg.eigvalsh(H)[0])


# ---------------------------------------------------------------------
# Statevector simulation of a gate list
# ---------------------------------------------------------------------

def _apply_1q(state: np.ndarray, gate: np.ndarray, q: int,
              n: int) -> np.ndarray:
    psi = state.reshape((2,) * n)
    psi = np.tensordot(gate, psi, axes=([1], [q]))
    psi = np.moveaxis(psi, 0, q)
    return psi.reshape(-1)

def _apply_ctrl(state: np.ndarray, gate: np.ndarray, control: int,
                target: int, n: int) -> np.ndarray:
    psi = state.reshape((2,) * n).copy()
    idx = [slice(None)] * n
    idx[control] = 1
    sub = psi[tuple(idx)]                       # control == |1> slab
    t_axis = target - (1 if control < target else 0)
    sub = np.tensordot(gate, sub, axes=([1], [t_axis]))
    sub = np.moveaxis(sub, 0, t_axis)
    psi[tuple(idx)] = sub
    return psi.reshape(-1)


def validate_gates(gates: list[dict], n: int) -> tuple[int, int, int]:
    """Return (n_params, n_ops, n_cnots); raise ValueError on bad input."""
    if not isinstance(gates, list) or not gates:
        raise ValueError("gates must be a non-empty list")
    if len(gates) > 500:
        raise ValueError("more than 500 gates")
    max_param = -1
    cnots = 0
    for i, g in enumerate(gates):
        kind = str(g.get("gate", "")).lower()
        if kind in ("rx", "ry", "rz"):
            q = g.get("q"); p = g.get("param")
            if not (isinstance(q, int) and 0 <= q < n):
                raise ValueError(f"gate {i}: bad qubit {q!r}")
            if not (isinstance(p, int) and 0 <= p < 200):
                raise ValueError(f"gate {i}: bad param index {p!r}")
            max_param = max(max_param, p)
        elif kind in ("h", "x", "z"):
            q = g.get("q")
            if not (isinstance(q, int) and 0 <= q < n):
                raise ValueError(f"gate {i}: bad qubit {q!r}")
        elif kind in ("cnot", "cx", "cz"):
            c, t = g.get("control"), g.get("target")
            if not (isinstance(c, int) and isinstance(t, int)
                    and 0 <= c < n and 0 <= t < n and c != t):
                raise ValueError(f"gate {i}: bad control/target")
            if kind in ("cnot", "cx"):
                cnots += 1
        else:
            raise ValueError(f"gate {i}: unknown gate {kind!r}")
    return max_param + 1, len(gates), cnots


def run_circuit(gates: list[dict], theta: np.ndarray,
                n: int) -> np.ndarray:
    state = np.zeros(2 ** n, dtype=complex)
    state[0] = 1.0
    rot = {"rx": X, "ry": Y, "rz": Z}
    for g in gates:
        kind = str(g["gate"]).lower()
        if kind in rot:
            t = float(theta[g["param"]])
            U = (np.cos(t / 2) * I2
                 - 1j * np.sin(t / 2) * rot[kind])
            state = _apply_1q(state, U, g["q"], n)
        elif kind == "h":
            state = _apply_1q(state, H_GATE, g["q"], n)
        elif kind == "x":
            state = _apply_1q(state, X, g["q"], n)
        elif kind == "z":
            state = _apply_1q(state, Z, g["q"], n)
        elif kind in ("cnot", "cx"):
            state = _apply_ctrl(state, X, g["control"], g["target"], n)
        elif kind == "cz":
            state = _apply_ctrl(state, Z, g["control"], g["target"], n)
    return state


def energy(gates: list[dict], theta: np.ndarray, H: np.ndarray,
           n: int) -> float:
    psi = run_circuit(gates, theta, n)
    return float(np.real(psi.conj() @ (H @ psi)))


def spsa_minimize(gates: list[dict], n_params: int, H: np.ndarray,
                  n: int, iters: int = 250, seed: int = 42,
                  restarts: int = 3) -> tuple[float, np.ndarray]:
    """Small SPSA with restarts — numpy-only, deterministic by seed."""
    rng = np.random.RandomState(seed)
    if n_params == 0:
        return energy(gates, np.zeros(0), H, n), np.zeros(0)
    best_e, best_t = np.inf, None
    for _ in range(restarts):
        theta = rng.uniform(-np.pi, np.pi, n_params)
        a0, c0 = 0.3, 0.15
        for k in range(1, iters + 1):
            ak = a0 / k ** 0.602
            ck = c0 / k ** 0.101
            delta = rng.choice([-1.0, 1.0], n_params)
            e_plus = energy(gates, theta + ck * delta, H, n)
            e_minus = energy(gates, theta - ck * delta, H, n)
            theta = theta - ak * (e_plus - e_minus) / (2 * ck) * delta
        e = energy(gates, theta, H, n)
        if e < best_e:
            best_e, best_t = e, theta
    return best_e, best_t


# ---------------------------------------------------------------------
# Baselines — hardware-efficient ansatz, L layers
# ---------------------------------------------------------------------

def hea_gates(n: int, layers: int) -> list[dict]:
    gates: list[dict] = []
    p = 0
    for _ in range(layers):
        for q in range(n):
            gates.append({"gate": "ry", "q": q, "param": p}); p += 1
        for q in range(n - 1):
            gates.append({"gate": "cnot", "control": q, "target": q + 1})
    for q in range(n):
        gates.append({"gate": "ry", "q": q, "param": p}); p += 1
    return gates


def evaluate_candidate(gates: list[dict], H: np.ndarray, n: int,
                       label: str, seed: int = 42,
                       iters: int = 250) -> dict[str, Any]:
    n_params, n_ops, n_cnots = validate_gates(gates, n)
    e_opt, _ = spsa_minimize(gates, n_params, H, n,
                             iters=iters, seed=seed)
    e_exact = exact_ground_energy(H)
    return {
        "label": label,
        "status": "ok",
        "energy_ha": round(e_opt, 8),
        "energy_error_ha": round(e_opt - e_exact, 8),
        "e_exact_ha": round(e_exact, 8),
        "params": n_params,
        "ops": n_ops,
        "cnots": n_cnots,
        "evaluator": "builtin-numpy-spsa",
    }


def evaluate_baseline_label(label: str, H: np.ndarray,
                            n: int) -> dict[str, Any] | None:
    """Evaluate labels like 'HEA-2L' for real; return None if unknown."""
    m = re.match(r"^HEA-(\d+)L$", label.strip(), re.IGNORECASE)
    if not m:
        return None
    rec = evaluate_candidate(hea_gates(n, int(m.group(1))), H, n, label)
    rec["source"] = "baseline"
    return rec


def parse_candidate_json(block: str) -> list[dict]:
    data = json.loads(block)
    if isinstance(data, dict) and "gates" in data:
        return data["gates"]
    if isinstance(data, list):
        return data
    raise ValueError("candidate JSON must be {'gates': [...]} or a list")
