"""Lineare Bestimmbarkeit der Gesamtwirkung im linear-gaußschen Modell mit verborgenen gemeinsamen Ursachen (generisch, lokal): Der Gradient der Wirkung nach den Parametern liegt im
Zeilenraum der Jacobi-Matrix der Kovarianz. Nur numpy, kein Streamlit.

Parameter: ein Koeffizient je gerichteter Kante, eine Kovarianz je bidirektionaler Kante, eine Varianz je Knoten. Σ = (I − B)⁻¹ Ω (I − B)⁻ᵀ."""

from __future__ import annotations

import numpy as np

import idf_constants as C
from kausal_generator import SplitMix64

STEP = 1e-6


def _unpack(theta: np.ndarray, n: int, D: list, Bi: list):
    k = 0
    b = np.zeros((n, n))
    for (i, j) in D:
        b[j, i] = theta[k]
        k += 1
    om = np.zeros((n, n))
    for (i, j) in Bi:
        om[i, j] = om[j, i] = theta[k]
        k += 1
    for i in range(n):
        om[i, i] = theta[k]
        k += 1
    return b, om


def covariance(theta: np.ndarray, n: int, D: list, Bi: list) -> np.ndarray:
    b, om = _unpack(theta, n, D, Bi)
    inv = np.linalg.inv(np.eye(n) - b)
    return inv @ om @ inv.T


def total_effect(theta: np.ndarray, n: int, D: list, Bi: list, x: int, y: int) -> float:
    b, _ = _unpack(theta, n, D, Bi)
    return float(np.linalg.inv(np.eye(n) - b)[y, x])


def random_parameters(n: int, D: list, Bi: list, seed: int = C.LINEAR_SEED) -> np.ndarray:
    """Ein fester, 'generischer' Parameterpunkt: Koeffizienten 0,5 bis 1,2 mit Vorzeichen, Kovarianzen 0,2 bis 0,5 mit Vorzeichen, Varianzen 1,5 bis 2,5."""
    rng = SplitMix64(seed)
    u = rng.uniform(2 * len(D) + 2 * len(Bi) + n)
    k = 0
    coef = [(0.5 + 0.7 * u[k + t]) * (1.0 if u[k + len(D) + t] < 0.5 else -1.0) for t in range(len(D))]
    k += 2 * len(D)
    cov = [(0.2 + 0.3 * u[k + t]) * (1.0 if u[k + len(Bi) + t] < 0.5 else -1.0) for t in range(len(Bi))]
    k += 2 * len(Bi)
    var = [1.5 + u[k + t] for t in range(n)]
    return np.array(coef + cov + var)


def jacobian(theta: np.ndarray, n: int, D: list, Bi: list) -> np.ndarray:
    iu = np.triu_indices(n)
    cols = []
    for t in range(len(theta)):
        tp, tm = theta.copy(), theta.copy()
        tp[t] += STEP
        tm[t] -= STEP
        cols.append((covariance(tp, n, D, Bi)[iu] - covariance(tm, n, D, Bi)[iu]) / (2 * STEP))
    return np.column_stack(cols)


def linear_identified(n: int, D, Bi, pairs, seed: int = C.LINEAR_SEED) -> tuple[dict, int, int]:
    """Für jedes (x, y) in `pairs`: ist die Gesamtwirkung im linearen Modell generisch bestimmbar? Rückgabe: ({(x, y): bool}, Rang der Jacobi-Matrix, Zahl der Parameter)."""
    D, Bi = sorted(D), sorted(Bi)
    theta = random_parameters(n, D, Bi, seed)
    jac = jacobian(theta, n, D, Bi)
    _, s, vt = np.linalg.svd(jac)
    rank = int((s > 1e-7 * s[0]).sum())
    basis = vt[:rank]
    out = {}
    for (x, y) in pairs:
        g = np.zeros(len(theta))
        for t in range(len(theta)):
            tp, tm = theta.copy(), theta.copy()
            tp[t] += STEP
            tm[t] -= STEP
            g[t] = (total_effect(tp, n, D, Bi, x, y) - total_effect(tm, n, D, Bi, x, y)) / (2 * STEP)
        norm = float(np.linalg.norm(g))
        out[(x, y)] = True if norm < 1e-9 else bool(np.linalg.norm(g - basis.T @ (basis @ g)) / norm < 1e-5)
    return out, rank, len(theta)
