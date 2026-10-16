"""Zuordnung zu den Verfahren der Linie: Welche Tür öffnet die Wirkung (Backdoor-Menge, Frontdoor-Menge, Instrument)? Verborgene gemeinsame Ursachen werden als verborgene Knoten mit
zwei Kindern in ein gewöhnliches Diagramm übersetzt und dann mit dsep_graph, bdr_backdoor und ins_criterion (wortgleich aus den Vorgängern) geprüft."""

from __future__ import annotations

import itertools

import bdr_backdoor as B
import ins_criterion as K


def to_dag(n: int, D, Bi) -> tuple:
    """Diagramm als Tupel von Elternmengen: Knoten 0..n−1 beobachtet, danach je bidirektionaler Kante ein verborgener Knoten mit den beiden Enden als Kindern."""
    parents = [[] for _ in range(n + len(Bi))]
    for (i, j) in D:
        parents[j].append(i)
    for k, (i, j) in enumerate(sorted(Bi)):
        parents[i].append(n + k)
        parents[j].append(n + k)
    return tuple(tuple(sorted(p)) for p in parents)


def methods(n: int, D, Bi, x: int, y: int) -> dict:
    """Die kleinste Backdoor-Menge, die kleinste Frontdoor-Menge und alle Instrumente unter den beobachteten Knoten (ohne x und y); None bzw. leere Liste, wenn es keine gibt."""
    parents = to_dag(n, D, Bi)
    observed = [v for v in range(n) if v not in (x, y)]
    backdoor = next((z for k in range(len(observed) + 1) for z in itertools.combinations(observed, k) if B.adjustment_valid(parents, x, y, z)), None)
    frontdoor = K.frontdoor_sets(parents, x, y, observed)
    return {"backdoor": backdoor, "frontdoor": frontdoor[0] if frontdoor else None, "instruments": K.instruments(parents, x, y, observed)}
