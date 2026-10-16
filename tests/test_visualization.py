"""Figuren und Tabellen: bauen ohne Fehler, und die gezeichneten Zahlen sind die der Auswertung."""

import pytest

import idf_constants as C
import idf_evaluation as ev
import idf_visualization as V


def test_graph_chart_draws_every_edge_and_marks_the_hedge():
    a = ev.analyse(ev.Settings())
    fig = V.build_graph(a)
    arrows = sum(1 for ann in fig.layout.annotations if ann.showarrow)
    dashed = [t for t in fig.data if t.mode == "lines"]
    nodes = [t for t in fig.data if t.mode == "markers+text"]
    assert arrows == len(a.settings.directed) == 2 and len(dashed) == len(a.settings.hidden) == 1 and len(nodes) == 4
    ring = [t.marker.line.color for t in nodes]
    assert ring.count(C.COLOR_BAD) >= 1 and ring.count(C.COLOR_TRUTH) >= 1                  # Hedge: F′ rot, F orange
    ok = V.build_graph(ev.analyse(ev.Settings(**C.PRESETS["Backdoor"])))
    assert not [t for t in ok.data if t.mode == "markers+text" and t.marker.line.color in (C.COLOR_BAD, C.COLOR_TRUTH)]


def test_graph_chart_builds_for_every_graph_with_the_first_row_of_masks():
    for p in C.PRESETS.values():
        assert V.build_graph(ev.analyse(ev.Settings(**p))) is not None
    assert V.build_graph(ev.analyse(ev.Settings(d=C.MASK_MAX, b=C.MASK_MAX, x=0, y=3))) is not None


def test_curves_bulge_away_from_the_center():
    xs, ys = V._curve(V.POS[1], V.POS[3])
    assert len(xs) == 25 and (xs[0], ys[0]) == pytest.approx(V.POS[1]) and (xs[-1], ys[-1]) == pytest.approx(V.POS[3])
    mid = (xs[12], ys[12])
    straight_mid = ((V.POS[1][0] + V.POS[3][0]) / 2, (V.POS[1][1] + V.POS[3][1]) / 2)
    d_mid = (mid[0] - 0.5) ** 2 + (mid[1] - 0.5) ** 2
    d_straight = (straight_mid[0] - 0.5) ** 2 + (straight_mid[1] - 0.5) ** 2
    assert d_mid > d_straight


def test_methods_table_names_every_verfahren():
    a = ev.analyse(ev.Settings())
    t = V.build_methods_table(a)
    assert len(t) == 6 and t.iloc[0]["Ergebnis"] == "keine gültige Menge" and t.iloc[1]["Ergebnis"] == "keine gültige Menge" and t.iloc[2]["Ergebnis"] == "{A}" and t.iloc[3]["Ergebnis"] == "nicht bestimmbar" and t.iloc[4]["Ergebnis"] == "Hedge gefunden"
    assert t.iloc[5]["Ergebnis"] == "bestimmbar (Rang 7 von 7 Parametern)"
    b = V.build_methods_table(ev.analyse(ev.Settings(**C.PRESETS["Backdoor"])))
    assert b.iloc[0]["Ergebnis"] == "Menge {A}" and b.iloc[4]["Ergebnis"] == "kein Hedge"


def test_experiment_figures_and_tables_build(exh3):
    assert V.build_share_chart(exh3, exh3) is not None and len(V.build_share_table(exh3, exh3)) == 4
    assert V.build_kinds_chart(exh3) is not None and len(V.build_kinds_table(exh3)) == 6 and len(V.build_examples_table(exh3)) == 0
    rows = ev.random_experiment(n=5, per=30, max_bi=3)
    assert V.build_random_chart(rows) is not None and len(V.build_random_table(rows)) == 4
    w = ev.two_worlds()
    assert V.build_worlds_chart(w) is not None and len(V.build_worlds_table(w)) == 5


def test_share_table_by_hand(exh3):
    t = V.build_share_table(exh3, exh3)
    assert list(t["verborgene Ursachen"]) == [0, 1, 2, 3] and list(t["3 Knoten: Fälle"]) == ["13", "39", "39", "13"] and list(t["3 Knoten: bestimmbar"]) == ["100 %", "64 %", "18 %", "0 %"]
    assert list(t["3 Knoten: linear"]) == ["100 %", "67 %", "28 %", "0 %"]


def test_kinds_table_sums_to_all_cases(exh3):
    t = V.build_kinds_table(exh3)
    assert t["Fälle"].sum() == exh3["cases"] == 104 and t.iloc[3]["Fälle"] == 44


def test_worlds_table_by_hand():
    t = V.build_worlds_table(ev.two_worlds())
    assert list(t["Welt A (verborgene Ursache, kein Pfeil)"]) == ["0,35", "0,15", "0,15", "0,35", "0,00"] and list(t["Welt B (Pfeil, keine verborgene Ursache)"]) == ["0,35", "0,15", "0,15", "0,35", "0,40"]
