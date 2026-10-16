"""Orakel über alle Graphen mit vier Knoten (schwer: etwa 20 Sekunden): ID-Algorithmus gegen Hedge-Aufzählung gegen linearen Jacobi-Rang. Die Aufzählung wird in conftest.py einmal gerechnet."""

import idf_identify as I
import idf_linear as L
import idf_methods as M


def test_id_and_hedge_agree_everywhere_and_id_implies_linear(exh4):
    assert exh4["cases"] == 14272 and exh4["mismatch"] == 0 and exh4["id_not_linear"] == 0
    assert exh4["linear"] >= exh4["identified"] and exh4["linear"] - exh4["identified"] == exh4["kinds"]["linear_iv"] + exh4["kinds"]["linear_other"]


def test_every_case_has_exactly_one_kind(exh4):
    assert sum(exh4["kinds"].values()) == exh4["cases"] and set(exh4["kinds"]) == {"backdoor", "frontdoor", "napkin", "linear_iv", "linear_other", "none"}
    assert exh4["kinds"]["backdoor"] + exh4["kinds"]["frontdoor"] + exh4["kinds"]["napkin"] == exh4["identified"]


def test_the_share_falls_with_every_added_hidden_cause(exh4):
    shares = [r["identified"] / r["cases"] for r in exh4["by_bi"].values()]
    lin = [r["linear"] / r["cases"] for r in exh4["by_bi"].values()]
    assert shares == sorted(shares, reverse=True) and lin == sorted(lin, reverse=True) and shares[0] == lin[0] == 1.0 and shares[-1] == lin[-1] == 0.0
    assert all(s <= l for s, l in zip(shares, lin))


def test_the_napkin_family_has_neither_door_and_is_identified(exh4):
    for _, D, Bi, x, y in exh4["neither_examples"]:
        D, Bi = frozenset(D), frozenset(Bi)
        m = M.methods(4, D, Bi, x, y)
        assert m["backdoor"] is None and m["frontdoor"] is None and not m["instruments"]
        assert I.identify({y}, {x}, set(range(4)), D, Bi) and I.find_hedge(x, y, set(range(4)), D, Bi) is None and L.linear_identified(4, D, Bi, [(x, y)])[0][(x, y)]
