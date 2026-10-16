"""Auswertung: Einstellungen, ein Graph mit allen Verfahren, Spur und Hedge als Text, die Aufzählung (drei Knoten), der Zufallsversuch und die zwei Welten."""

import itertools

import pytest

import idf_constants as C
import idf_evaluation as ev


def test_number_formats_and_names():
    assert ev.de(-1.234) == "−1,23" and ev.de(0.5, 1) == "0,5" and ev.de(3.0, 0) == "3" and ev.signed(0.3) == "+0,30" and ev.signed(-1e-12) == "+0,00"
    assert ev.names_of({2, 0}) == "{A, C}" and ev.names_of(set()) == "{}" and ev.edge_text({(1, 2), (0, 1)}, "→") == "A → B, B → C" and ev.edge_text(set(), "↔") == "keine"


def test_settings_decode_the_masks_and_default_to_the_first_preset():
    s = ev.Settings(d=0b000011, b=0b100000, x=1, y=2)
    assert s.directed == frozenset({(0, 1), (0, 2)}) and s.hidden == frozenset({(2, 3)})
    d = ev.Settings()
    assert (d.d, d.b, d.x, d.y) == (C.PRESETS["Instrument (Voreinstellung)"]["d"], C.PRESETS["Instrument (Voreinstellung)"]["b"], 1, 2)
    assert d.directed == frozenset({(0, 1), (1, 2)}) and d.hidden == frozenset({(1, 2)})


@pytest.mark.parametrize("name,identified,linear,kind", [("Instrument (Voreinstellung)", False, True, "linear_iv"), ("Bow-Arc", False, False, "none"), ("Backdoor", True, True, "backdoor"),
                                                         ("Frontdoor", True, True, "frontdoor"), ("Napkin", True, True, "napkin"), ("Viele verborgene Ursachen", False, False, "none")])
def test_every_preset_has_its_documented_verdict(name, identified, linear, kind):
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    assert (a.identified, a.linear, a.kind) == (identified, linear, kind) and a.consistent and (a.hedge is None) == identified and not a.trivial


def test_the_instrument_preset_names_its_instrument_and_the_bow_has_a_hedge():
    a = ev.analyse(ev.Settings())
    assert a.methods["instruments"] == [0] and a.rank == 7 and a.params == 7
    b = ev.analyse(ev.Settings(**C.PRESETS["Bow-Arc"]))
    assert b.hedge["F"] == frozenset({0, 1}) and b.hedge["R"] == frozenset({1}) and b.rank == 5 and b.params == 6


def test_no_path_is_trivial_and_equal_nodes_are_rejected():
    a = ev.analyse(ev.Settings(d=0b000001, b=0, x=3, y=0))
    assert a.trivial and a.kind == "trivial" and a.identified
    with pytest.raises(ValueError):
        ev.analyse(ev.Settings(x=1, y=1))


def test_classify_directly():
    D, Bi = frozenset({(0, 1), (1, 2)}), frozenset({(0, 2)})
    assert ev.classify(3, D, Bi, 0, 2, True, True) == "frontdoor" and ev.classify(3, D, frozenset({(1, 2)}), 1, 2, False, True) == "linear_iv" and ev.classify(3, D, Bi, 2, 0, True, True) == "trivial"
    assert ev.classify(3, frozenset({(0, 1)}), frozenset({(0, 1)}), 0, 1, False, False) == "none"
    assert ev.classify(3, frozenset({(0, 1), (0, 2), (1, 2)}), frozenset({(0, 1), (0, 2)}), 1, 2, False, True) in ("linear_iv", "linear_other")


def test_trace_text_of_the_bow_and_the_instrument():
    bow = ev.trace_text(ev.analyse(ev.Settings(**C.PRESETS["Bow-Arc"])).trace)
    assert bow == ["Zeile 2: Nur die Vorfahren von {B} zählen: {A, B}.", "Zeile 5(a): Hedge: Der Graph ist eine einzige C-Komponente, die Wirkung auf {B} ist nicht bestimmbar."]
    ins = ev.trace_text(ev.analyse(ev.Settings()).trace)
    assert ins[0].startswith("Zeile 2") and any("Zeile 3: Zusätzliche Eingriffe auf {A}" in t for t in ins) and any("Zeile 5(c)" in t and "{B, C}" in t for t in ins) and ins[-1].startswith("Zeile 5(a)")
    front = " ".join(ev.trace_text(ev.analyse(ev.Settings(**C.PRESETS["Frontdoor"])).trace))
    assert "Zeile 4: Ohne x zerfällt der Graph in 2 C-Komponenten" in front and "Zeile 5(b)" in front


def test_trace_text_of_the_trivial_lines():
    assert ev.trace_text([("1", frozenset({1}), frozenset())]) == ["Zeile 1: Es ist kein Eingriff übrig, die Wirkung ist eine Randverteilung."]


def test_hedge_text_by_hand():
    h = ev.analyse(ev.Settings(**C.PRESETS["Bow-Arc"])).hedge
    assert ev.hedge_text(h) == ("F = {A, B} mit den Pfeilen A → B; F′ = {B} mit den Pfeilen keine; gemeinsame Wurzelmenge {B}. F enthält x, F′ nicht; beide hängen über verborgene Ursachen zusammen.")


def test_exhaustive_with_three_nodes_by_hand(exh3):
    assert exh3["cases"] == 104 and exh3["identified"] == 45 and exh3["linear"] == 50 and exh3["mismatch"] == 0 and exh3["id_not_linear"] == 0
    assert {b: (r["cases"], r["identified"], r["linear"]) for b, r in exh3["by_bi"].items()} == {0: (13, 13, 13), 1: (39, 25, 26), 2: (39, 7, 11), 3: (13, 0, 0)}
    assert exh3["kinds"] == {"backdoor": 44, "frontdoor": 1, "linear_iv": 5, "none": 54} and sum(exh3["kinds"].values()) == 104 and exh3["neither_examples"] == []


def test_more_hidden_causes_never_help(exh3):
    shares = [r["identified"] / r["cases"] for r in exh3["by_bi"].values()]
    assert shares == sorted(shares, reverse=True) and shares[0] == 1.0 and shares[-1] == 0.0


def test_random_experiment_small_run():
    rows = ev.random_experiment(n=5, per=60, max_bi=3)
    assert [r["hidden"] for r in rows] == [0, 1, 2, 3] and rows[0]["share"] == 1.0 and rows[3]["share"] < rows[0]["share"] and all(r["per"] == 60 for r in rows)
    assert rows == ev.random_experiment(n=5, per=60, max_bi=3)


def test_joint_and_bounds_by_hand():
    j = ev.joint_of(0.5, 0.7, 0.3)
    assert j == pytest.approx({(1, 1): 0.35, (1, 0): 0.15, (0, 1): 0.15, (0, 0): 0.35}) and sum(j.values()) == pytest.approx(1.0)
    lo, hi = ev.manski_bounds(j)
    assert lo == pytest.approx(0.35 - 0.15 - 0.5) and hi == pytest.approx(0.35 + 0.5 - 0.15)


def test_bounds_have_width_one_and_contain_the_true_effects():
    for px, p1, p0 in itertools.product((0.2, 0.5, 0.8), (0.1, 0.7, 0.9), (0.05, 0.3, 0.6)):
        lo, hi = ev.manski_bounds(ev.joint_of(px, p1, p0))
        assert hi - lo == pytest.approx(1.0) and lo <= p1 - p0 <= hi


def test_two_worlds():
    w = ev.two_worlds()
    assert w["same"] is True and w["effect_a"] == 0.0 and w["effect_b"] == pytest.approx(0.4) and w["lower"] == pytest.approx(-0.3) and w["upper"] == pytest.approx(0.7)
    assert w["joint_a"][(1, 1)] == pytest.approx(0.35) and w["joint_b"][(1, 1)] == pytest.approx(0.35) and w["joint_a"][(0, 1)] == pytest.approx(0.15)
    other = ev.two_worlds(0.3, 0.9, 0.2)
    assert other["same"] and other["effect_b"] == pytest.approx(0.7) and other["upper"] - other["lower"] == pytest.approx(1.0)
