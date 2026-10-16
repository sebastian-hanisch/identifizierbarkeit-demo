"""Zuordnung zu den Verfahren der Linie: Übersetzung verborgener Ursachen in verborgene Knoten und die Tür je benanntem Graphen."""

import pytest

import bdr_backdoor as B
import idf_identify as I
import idf_methods as M


def test_to_dag_by_hand():
    parents = M.to_dag(3, {(0, 1)}, {(0, 2), (1, 2)})
    assert parents == ((3,), (0, 4), (3, 4), (), ()) and len(parents) == 5


def test_to_dag_without_hidden_causes_is_the_graph_itself():
    assert M.to_dag(3, {(0, 1), (0, 2), (1, 2)}, set()) == ((), (0,), (0, 1))


def test_methods_of_the_named_graphs(bow, backdoor, frontdoor, instrument, napkin):
    assert M.methods(*bow) == {"backdoor": None, "frontdoor": None, "instruments": []}
    assert M.methods(*backdoor) == {"backdoor": (0,), "frontdoor": None, "instruments": []}
    assert M.methods(*frontdoor) == {"backdoor": None, "frontdoor": (1,), "instruments": []}
    assert M.methods(*instrument) == {"backdoor": None, "frontdoor": None, "instruments": [0]}
    assert M.methods(*napkin) == {"backdoor": None, "frontdoor": None, "instruments": []}


def test_backdoor_set_is_the_smallest():
    """Ohne verborgene Ursache und ohne Störgröße genügt die leere Menge."""
    assert M.methods(3, {(0, 1), (1, 2)}, set(), 0, 2)["backdoor"] == ()


def test_a_covariate_confounded_with_x_blocks_the_path_from_the_hidden_cause():
    """A -> C, B -> C, A <-> B, x = A, y = C: Der Weg A <- L -> B -> C wird durch Festhalten von B blockiert (B ist dort kein Collider)."""
    assert M.methods(3, {(0, 2), (1, 2)}, {(0, 1)}, 0, 2)["backdoor"] == (1,)


def test_every_identified_graph_with_a_backdoor_or_frontdoor_set_is_identified_by_the_id():
    pairs = [(i, j) for i in range(3) for j in range(i + 1, 3)]
    seen = 0
    for dm in range(8):
        D = frozenset(pairs[k] for k in range(3) if dm >> k & 1)
        for bm in range(8):
            Bi = frozenset(pairs[k] for k in range(3) if bm >> k & 1)
            for (x, y) in pairs:
                if not I.has_directed_path(x, y, D, 3):
                    continue
                m = M.methods(3, D, Bi, x, y)
                if m["backdoor"] is not None or m["frontdoor"] is not None:
                    assert I.identify({y}, {x}, {0, 1, 2}, D, Bi), (sorted(D), sorted(Bi), x, y)
                    seen += 1
    assert seen > 40


def test_backdoor_set_found_is_valid_under_the_hidden_nodes():
    n, D, Bi = 3, {(0, 1), (0, 2), (1, 2)}, set()
    parents = M.to_dag(n, D, Bi)
    z = M.methods(n, D, Bi, 1, 2)["backdoor"]
    assert B.adjustment_valid(parents, 1, 2, z) and not B.adjustment_valid(parents, 1, 2, ())
