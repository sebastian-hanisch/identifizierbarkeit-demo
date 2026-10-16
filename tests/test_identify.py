"""ID-Algorithmus und Hedge: Hilfsfunktionen von Hand, benannte Graphen mit Spur, und die Kreuzprüfungen über alle Graphen mit drei Knoten und eine Stichprobe mit vier Knoten."""

import itertools

import pytest

import idf_identify as I


def _all(n):
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    for dm in range(2 ** len(pairs)):
        D = frozenset(pairs[k] for k in range(len(pairs)) if dm >> k & 1)
        for bm in range(2 ** len(pairs)):
            yield D, frozenset(pairs[k] for k in range(len(pairs)) if bm >> k & 1)


def _ident(g, trace=None):
    n, D, Bi, x, y = g
    return I.identify({y}, {x}, set(range(n)), D, Bi, trace)


def test_ancestors_components_and_restrict_by_hand():
    D = {(0, 1), (1, 2), (0, 3)}
    assert I.ancestors({2}, {0, 1, 2, 3}, D) == {0, 1, 2} and I.ancestors({3}, {0, 1, 2, 3}, D) == {0, 3} and I.ancestors({2}, {1, 2}, D) == {1, 2}      # ohne Knoten 0 reißt der Weg ab
    Bi = {(0, 1), (2, 3)}
    assert I.components({0, 1, 2, 3}, Bi) == [frozenset({0, 1}), frozenset({2, 3})] and I.components({0, 2, 3}, Bi) == [frozenset({0}), frozenset({2, 3})]
    assert I.components({0, 1, 2}, {(0, 1), (1, 2)}) == [frozenset({0, 1, 2})] and I.components(set(), Bi) == []
    assert I.restrict({0, 1}, D, Bi) == (frozenset({(0, 1)}), frozenset({(0, 1)}))


def test_has_directed_path():
    D = {(0, 1), (1, 2)}
    assert I.has_directed_path(0, 2, D, 4) and I.has_directed_path(1, 2, D, 4) and not I.has_directed_path(2, 0, D, 4) and not I.has_directed_path(0, 3, D, 4)


def test_named_graphs(bow, backdoor, frontdoor, instrument, napkin):
    assert _ident(bow) is False and _ident(instrument) is False
    assert _ident(backdoor) is True and _ident(frontdoor) is True and _ident(napkin) is True


def _tight(g):
    """Derselbe Graph nur mit den Knoten, die er braucht (die Fixtures haben vier Knoten; ein unbenutzter Knoten fügt Zeile 2 hinzu)."""
    n, D, Bi, x, y = g
    return (max(max(e) for e in D | Bi | {(x, y)}) + 1, D, Bi, x, y)


def test_unused_nodes_cost_a_line_2_step(bow):
    t = []
    assert _ident(bow, t) is False and [e[0] for e in t] == ["2", "5a"] and t[0][2] == frozenset({0, 1})


def test_traces_of_the_named_graphs(bow, backdoor, instrument):
    t = []
    _ident(_tight(bow), t)
    assert [e[0] for e in t] == ["5a"]
    t = []
    _ident(_tight(instrument), t)
    assert [e[0] for e in t] == ["3", "5c", "5a"] and t[0][2] == frozenset({0}) and t[1][2] == frozenset({1, 2})
    t = []
    _ident(_tight(backdoor), t)
    assert [e[0] for e in t] == ["4", "2", "1", "5b"]


def test_no_hidden_cause_means_identifiable():
    for D, Bi in _all(3):
        if Bi:
            continue
        for (x, y) in itertools.permutations(range(3), 2):
            assert I.identify({y}, {x}, {0, 1, 2}, D, Bi)


def test_find_hedge_of_the_bow_arc(bow):
    n, D, Bi, x, y = bow
    h = I.find_hedge(x, y, set(range(n)), D, Bi)
    assert h == {"F": frozenset({0, 1}), "F_edges": frozenset({(0, 1)}), "Fp": frozenset({1}), "Fp_edges": frozenset(), "R": frozenset({1})}


def test_hedge_needs_forests_that_drop_arrows():
    """0 -> 1 -> 2 und 0 -> 2 mit 0 <-> 1 und 0 <-> 2, x = 1, y = 2: Der Knoten 0 hat zwei Kinder, F muss den Pfeil 0 -> 2 weglassen (kein induzierter C-Wald)."""
    D, Bi = frozenset({(0, 1), (0, 2), (1, 2)}), frozenset({(0, 1), (0, 2)})
    assert I.identify({2}, {1}, {0, 1, 2}, D, Bi) is False
    h = I.find_hedge(1, 2, {0, 1, 2}, D, Bi)
    assert h is not None and h["F"] == frozenset({0, 1, 2}) and (0, 2) not in h["F_edges"] and h["F_edges"] == frozenset({(1, 2)}) and h["Fp"] == frozenset({0, 2}) and h["R"] == frozenset({0, 2})


def test_hedge_is_absent_for_identifiable_graphs(backdoor, frontdoor, napkin):
    for g in (backdoor, frontdoor, napkin):
        n, D, Bi, x, y = g
        assert I.find_hedge(x, y, set(range(n)), D, Bi) is None


def test_hedge_has_the_defining_properties_wherever_it_is_found():
    for D, Bi in _all(3):
        for (x, y) in itertools.permutations(range(3), 2):
            h = I.find_hedge(x, y, {0, 1, 2}, D, Bi)
            if h is None:
                continue
            F, Fp = h["F"], h["Fp"]
            assert x in F and x not in Fp and Fp < F and len(I.components(F, I.restrict(F, D, Bi)[1])) == 1 and len(I.components(Fp, I.restrict(Fp, D, Bi)[1])) == 1
            for edges, nodes in ((h["F_edges"], F), (h["Fp_edges"], Fp)):
                assert all(e in D and e[0] in nodes and e[1] in nodes for e in edges) and len({e[0] for e in edges}) == len(edges)          # höchstens ein Kind je Knoten
            assert h["R"] == frozenset(v for v in F if v not in {e[0] for e in h["F_edges"]}) == frozenset(v for v in Fp if v not in {e[0] for e in h["Fp_edges"]})
            assert h["R"] <= I.ancestors({y}, {0, 1, 2}, {e for e in D if e[1] != x})


def test_id_and_hedge_agree_on_all_graphs_with_three_nodes():
    checked = 0
    for D, Bi in _all(3):
        for (x, y) in itertools.permutations(range(3), 2):
            if not I.has_directed_path(x, y, D, 3):
                continue
            assert I.identify({y}, {x}, {0, 1, 2}, D, Bi) == (I.find_hedge(x, y, {0, 1, 2}, D, Bi) is None), (sorted(D), sorted(Bi), x, y)
            checked += 1
    assert checked == 104


def test_adding_a_hidden_cause_never_makes_a_problem_easier():
    """Monotonie: Ist die Wirkung mit der zusätzlichen verborgenen Ursache bestimmbar, dann auch ohne sie."""
    pairs = [(i, j) for i in range(3) for j in range(i + 1, 3)]
    for D, Bi in _all(3):
        for extra in pairs:
            if extra in Bi:
                continue
            for (x, y) in itertools.permutations(range(3), 2):
                if I.identify({y}, {x}, {0, 1, 2}, D, Bi | {extra}):
                    assert I.identify({y}, {x}, {0, 1, 2}, D, Bi)


def test_tian_pearl_sufficient_condition_on_all_graphs_with_three_nodes():
    """Gibt es keinen bidirektionalen Pfad von x zu einem Kind von x, ist die Wirkung auf alle anderen Knoten und damit auf y bestimmbar (Tian/Pearl, aus dem Gedächtnis)."""
    count = 0
    for D, Bi in _all(3):
        comps = I.components({0, 1, 2}, Bi)
        for (x, y) in itertools.permutations(range(3), 2):
            comp = next(c for c in comps if x in c)
            if not any(j in comp for (i, j) in D if i == x):
                assert I.identify({y}, {x}, {0, 1, 2}, D, Bi)
                count += 1
    assert count > 100


def test_id_and_hedge_agree_on_a_sample_of_graphs_with_four_nodes():
    """Stichprobe der Vier-Knoten-Graphen (feste Reihenfolge): ID gegen Hedge-Aufzählung, und ein bestimmbarer Fall ist auch linear bestimmbar."""
    import idf_linear as L

    pairs = [(i, j) for i in range(4) for j in range(i + 1, 4)]
    checked = hedges = 0
    for dm in range(0, 64, 3):
        D = frozenset(pairs[k] for k in range(6) if dm >> k & 1)
        for bm in range(1, 64, 5):
            Bi = frozenset(pairs[k] for k in range(6) if bm >> k & 1)
            targets = [(x, y) for (x, y) in pairs if I.has_directed_path(x, y, D, 4)]
            lin, _, _ = L.linear_identified(4, D, Bi, targets) if targets else ({}, 0, 0)
            for (x, y) in targets:
                ident = I.identify({y}, {x}, {0, 1, 2, 3}, D, Bi)
                hedge = I.find_hedge(x, y, {0, 1, 2, 3}, D, Bi)
                assert ident == (hedge is None), (sorted(D), sorted(Bi), x, y)
                assert not ident or lin[(x, y)]
                checked += 1
                hedges += hedge is not None
    assert checked > 400 and hedges > 100
