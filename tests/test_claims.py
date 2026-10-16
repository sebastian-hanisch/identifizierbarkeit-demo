"""Jede Zahl aus README.md und den App-Texten wird hier über dieselben Auswertungsfunktionen nachgerechnet (DEMO-PLAYBOOK §4).

Alle Experimente sind Aufzählungen aller Graphen (ganzzahlig, exakt) oder laufen über SplitMix64-Ströme (plattformstabil). Die Anteile gelten für diese Aufzählung bzw. dieses Ensemble,
nicht für die Häufigkeit in der Praxis.
"""

import pytest

import idf_constants as C
import idf_evaluation as ev


@pytest.fixture(scope="module")
def random_rows():
    return {r["hidden"]: r for r in ev.random_experiment()}


def test_named_graphs():
    verdicts = {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}
    assert [(a.identified, a.linear) for a in verdicts.values()] == [(False, True), (False, False), (True, True), (True, True), (True, True), (False, False)]
    assert verdicts["Napkin"].kind == "napkin" and verdicts["Instrument (Voreinstellung)"].methods["instruments"] == [0] and verdicts["Napkin"].methods == {"backdoor": None, "frontdoor": None, "instruments": []}


def test_experiment_1_three_nodes(exh3):
    assert exh3["cases"] == 104 and exh3["identified"] == 45 and exh3["linear"] == 50 and exh3["identified"] / exh3["cases"] == pytest.approx(0.433, abs=0.0005)
    assert exh3["linear"] / exh3["cases"] == pytest.approx(0.481, abs=0.0005) and exh3["kinds"]["linear_iv"] == 5 and exh3["kinds"]["backdoor"] == 44 and exh3["kinds"]["frontdoor"] == 1
    assert {b: round(100 * r["identified"] / r["cases"]) for b, r in exh3["by_bi"].items()} == {0: 100, 1: 64, 2: 18, 3: 0}


def test_experiment_1_four_nodes(exh3, exh4):
    assert exh4["cases"] == 14272 and exh4["identified"] == 5169 and exh4["linear"] == 6683
    assert exh4["identified"] / exh4["cases"] == pytest.approx(0.362, abs=0.0005) and exh4["linear"] / exh4["cases"] == pytest.approx(0.468, abs=0.0005)
    assert {b: (r["cases"], r["identified"], r["linear"]) for b, r in exh4["by_bi"].items()} == {0: (223, 223, 223), 1: (1338, 1078, 1112), 2: (3345, 1891, 2182), 3: (4460, 1392, 2127),
                                                                                                  4: (3345, 515, 901), 5: (1338, 70, 138), 6: (223, 0, 0)}
    assert [round(100 * r["identified"] / r["cases"]) for r in exh4["by_bi"].values()] == [100, 81, 57, 31, 15, 5, 0]
    assert [round(100 * r["linear"] / r["cases"]) for r in exh4["by_bi"].values()] == [100, 83, 65, 48, 27, 10, 0]
    assert exh4["mismatch"] == 0 and exh4["id_not_linear"] == 0 and exh3["mismatch"] == 0 and exh3["id_not_linear"] == 0


def test_experiment_2_kinds(exh4):
    k = exh4["kinds"]
    assert k == {"backdoor": 4956, "frontdoor": 176, "napkin": 37, "linear_iv": 888, "linear_other": 626, "none": 7589}
    assert k["napkin"] / exh4["identified"] == pytest.approx(0.007, abs=0.0005) and k["none"] / exh4["cases"] == pytest.approx(0.532, abs=0.0005)
    assert k["linear_iv"] + k["linear_other"] == 1514 and exh4["linear"] - exh4["identified"] == 1514


def test_experiment_2_napkin_examples(exh4):
    ex = exh4["neither_examples"]
    assert len(ex) == 6 and all(e[0] == 5 for e in ex[:3])
    assert ex[0][1:] == ([(0, 1), (0, 2), (1, 2), (2, 3)], [(1, 3)], 1, 3) and ex[2][1:] == ([(0, 1), (1, 2), (2, 3)], [(0, 2), (0, 3)], 2, 3)


def test_experiment_3_random_graphs(random_rows):
    assert C.RANDOM_PER == 800 and C.RANDOM_NODES == 5 and C.RANDOM_MAX_BI == 8
    expected = {0: 1.0, 1: 0.864, 2: 0.719, 3: 0.581, 4: 0.396, 5: 0.275, 6: 0.196, 7: 0.12, 8: 0.06}
    for hidden, share in expected.items():
        assert random_rows[hidden]["share"] == pytest.approx(share, abs=0.0006), hidden
    assert [round(100 * random_rows[h]["share"]) for h in range(9)] == [100, 86, 72, 58, 40, 28, 20, 12, 6]


def test_experiment_4_two_worlds():
    w = ev.two_worlds()
    assert w["same"] and w["effect_a"] == 0.0 and w["effect_b"] == pytest.approx(0.40, abs=0.005) and w["lower"] == pytest.approx(-0.30, abs=0.005) and w["upper"] == pytest.approx(0.70, abs=0.005)
    assert w["upper"] - w["lower"] == pytest.approx(1.0) and [round(w["joint_b"][c], 2) for c in ((1, 1), (1, 0), (0, 1), (0, 0))] == [0.35, 0.15, 0.15, 0.35]


def test_the_text_numbers_of_the_app_follow_the_findings(exh3, exh4, random_rows):
    text = ev.verdict_exhaustive(exh3, exh4)[1]
    assert "36,2 %" in text and "46,8 %" in text and "14272 Fälle" in text and "in 0 von 14376 Fällen" in text and "mit sechs 0 %" in text
    assert "37 (0,7 %)" in ev.verdict_kinds(exh4)[1] and "davon 888" in ev.verdict_kinds(exh4)[1]
    assert "bei 8 nur noch 6 %" in ev.verdict_random([random_rows[h] for h in range(9)])[1]
