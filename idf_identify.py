"""Identifizierbarkeit in Diagrammen mit verborgenen gemeinsamen Ursachen (ADMG: gerichtete Pfeile i -> j mit i < j, bidirektionale Kanten i <-> j).

Zwei Wege zur Entscheidung, ob P(y | do(x)) aus der Beobachtungsverteilung bestimmbar ist:
  * `identify`: der ID-Algorithmus als Entscheidung (rekursiv auf Teilgraphen, mit Spur der angewendeten Zeilen);
  * `find_hedge`: das Hedge-Kriterium aus der Definition durch Aufzählen aller Paare von C-Wäldern F ⊇ F' (liefert den Beweis der Verneinung).
Nur Standardbibliothek, kein Streamlit."""

from __future__ import annotations

import itertools


def ancestors(S, V, D) -> set:
    """Vorfahren (einschließlich S) im von V induzierten Graphen mit den gerichteten Kanten D (höchstens |V| Runden: jede Runde nimmt die Eltern der bisherigen Menge hinzu)."""
    out = set(S)
    for _ in range(len(V) + 1):
        grown = out | {i for (i, j) in D if j in out and i in V}
        if grown == out:
            break
        out = grown
    return out


def components(V, Bi) -> list[frozenset]:
    """C-Komponenten: zusammenhängende Komponenten der bidirektionalen Kanten im von V induzierten Graphen, nach kleinstem Knoten sortiert."""
    left, out = set(V), []
    while left:
        comp = {min(left)}
        for _ in range(len(V)):
            grown = comp | {b for (i, j) in Bi for a, b in ((i, j), (j, i)) if a in comp and b in left}
            if grown == comp:
                break
            comp = grown
        left -= comp
        out.append(frozenset(comp))
    return sorted(out, key=min)


def restrict(V, D, Bi):
    return frozenset(e for e in D if e[0] in V and e[1] in V), frozenset(e for e in Bi if e[0] in V and e[1] in V)


def has_directed_path(x: int, y: int, D, n: int) -> bool:
    """Gibt es einen gerichteten Pfad von x nach y im Graphen mit den Knoten 0..n−1?"""
    return x in ancestors({y}, set(range(n)), D)


def identify(Y, X, V, D, Bi, trace: list | None = None) -> bool:
    """ID-Algorithmus (Shpitser/Pearl) nur als Entscheidung: True, wenn P(Y | do(X)) im von V induzierten Graphen aus der Beobachtungsverteilung bestimmbar ist.
    `trace` sammelt (Zeile, Mengen) der angewendeten Zeilen."""
    Y, X, V = frozenset(Y), frozenset(X), frozenset(V)
    D, Bi = restrict(V, D, Bi)
    log = trace.append if trace is not None else (lambda entry: None)
    if not X:
        log(("1", Y, X))
        return True
    A = ancestors(Y, V, D)
    if V != A:
        log(("2", Y, frozenset(A)))
        return identify(Y, X & A, A, D, Bi, trace)
    D_cut = frozenset(e for e in D if e[1] not in X)                             # G ohne die Pfeile in X
    W = (V - X) - ancestors(Y, V, D_cut)
    if W:
        log(("3", Y, frozenset(W)))
        return identify(Y, X | W, V, D, Bi, trace)
    rest = V - X
    rest_comps = components(rest, Bi)
    if len(rest_comps) > 1:
        log(("4", Y, tuple(rest_comps)))
        return all([identify(S, V - S, V, D, Bi, trace) for S in rest_comps])
    S = rest
    graph_comps = components(V, Bi)
    if len(graph_comps) == 1:
        log(("5a", Y, S))
        return False
    if S in graph_comps:
        log(("5b", Y, S))
        return True
    for S2 in graph_comps:
        if S < S2:
            log(("5c", Y, S2))
            return identify(Y, X & S2, S2, D, Bi, trace)
    raise AssertionError("S liegt in einer C-Komponente von G")


def find_hedge(x: int, y: int, V, D, Bi):
    """Hedge für P(y | do(x)) aus der Definition: zwei C-Wälder F ⊇ F' (Teilgraphen: jeder Knoten behält höchstens ein Kind, bidirektionale Kanten bleiben) mit gleicher
    Wurzelmenge R ⊆ An(y) im Graphen ohne Pfeile in x, x ∈ F, x ∉ F'. Rückgabe None oder {"F", "F_edges", "Fp", "Fp_edges", "R"}; die erste gefundene Lösung, nach Größe sortiert."""
    V = frozenset(V)
    D_cut = frozenset(e for e in D if e[1] != x)
    anc_y = ancestors({y}, V, D_cut)

    def connected(F):
        return len(components(F, restrict(F, D, Bi)[1])) == 1

    def child_choices(F):
        nodes = sorted(F)
        options = [[None] + sorted(j for (i, j) in D if i == v and j in F) for v in nodes]
        for combo in itertools.product(*options):
            yield dict(zip(nodes, combo))

    nodes = sorted(V)
    for r in range(1, len(nodes) + 1):
        for F in map(frozenset, itertools.combinations(nodes, r)):
            if x not in F or not connected(F):
                continue
            for fc in child_choices(F):
                R = frozenset(v for v, c in fc.items() if c is None)
                if not R <= anc_y:
                    continue
                rest = sorted(F - {x})
                for k in range(1, len(rest) + 1):
                    for Fp in map(frozenset, itertools.combinations(rest, k)):
                        if not connected(Fp):
                            continue
                        members = sorted(Fp)
                        options = [[None] + ([fc[v]] if fc[v] is not None and fc[v] in Fp else []) for v in members]
                        for combo in itertools.product(*options):
                            if frozenset(v for v, c in zip(members, combo) if c is None) == R:
                                return {"F": F, "F_edges": frozenset((v, c) for v, c in fc.items() if c is not None), "Fp": Fp,
                                        "Fp_edges": frozenset((v, c) for v, c in zip(members, combo) if c is not None), "R": R}
    return None
