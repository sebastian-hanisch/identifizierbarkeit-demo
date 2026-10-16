"""Verdikte: Art und Text je Lage; jede Zahl im Text stammt aus dem Befund, nicht aus einer Konstanten."""

import idf_constants as C
import idf_evaluation as ev


def _verdict(name):
    return ev.verdict_graph(ev.analyse(ev.Settings(**C.PRESETS[name])))


def test_identifiable_graphs_are_a_success_and_name_the_door():
    kind, text = _verdict("Backdoor")
    assert kind == "success" and "Die Wirkung von B auf C ist **bestimmbar**" in text and "Backdoor-Adjustierung" in text
    assert "Frontdoor-Formel" in _verdict("Frontdoor")[1] and "nur der ID-Algorithmus findet den Weg" in _verdict("Napkin")[1] and _verdict("Frontdoor")[0] == "success"


def test_the_instrument_graph_is_a_warning_with_the_instrument_named():
    kind, text = _verdict("Instrument (Voreinstellung)")
    assert kind == "warning" and "ohne Modellannahme nicht bestimmbar" in text and "im linearen Modell aber schon" in text and "Instrument {A}" in text


def test_hopeless_graphs_are_an_error_with_the_two_worlds():
    for name in ("Bow-Arc", "Viele verborgene Ursachen"):
        kind, text = _verdict(name)
        assert kind == "error" and "nicht bestimmbar, auch nicht im linearen Modell" in text and "zweier Welten mit denselben Daten" in text


def test_a_linear_only_case_without_a_single_instrument_says_so():
    """A -> B, A -> C, B -> D, C -> D mit B <-> D, x = B, y = D: A ist erst nach Festhalten von C ein Instrument (bedingt), kein einzelnes unbedingtes."""
    s = ev.Settings(d=C.mask_of({(0, 1), (0, 2), (1, 3), (2, 3)}), b=C.mask_of({(1, 3)}), x=1, y=3)
    a = ev.analyse(s)
    assert a.kind == "linear_other" and not a.identified and a.linear
    kind, text = ev.verdict_graph(a)
    assert kind == "warning" and "wenn auch nicht durch ein einzelnes Instrument" in text


def test_a_graph_without_a_path_is_info():
    kind, text = ev.verdict_graph(ev.analyse(ev.Settings(d=C.mask_of({(0, 1)}), b=0, x=3, y=0)))
    assert kind == "info" and "keinen gerichteten Pfad von D nach A" in text


def test_exhaustive_verdicts_quote_the_findings(exh3):
    kind, text = ev.verdict_exhaustive(exh3, {**exh3, "by_bi": {**exh3["by_bi"], 6: exh3["by_bi"][3]}})
    assert kind == "info" and "Der ID-Algorithmus und die Hedge-Aufzählung widersprechen sich in 0 von 208 Fällen" in text and "43,3 %" in text and "48,1 %" in text
    kind, text = ev.verdict_kinds(exh3)
    assert kind == "info" and "löst eine Backdoor-Menge 44, die Frontdoor zusätzlich 1" in text and "0 (0,0 %) brauchen den ID-Algorithmus" in text and "davon 5 durch ein Instrument" in text


def test_random_verdict_quotes_the_rows():
    rows = ev.random_experiment(n=5, per=50, max_bi=8)
    kind, text = ev.verdict_random(rows)
    assert kind == "info" and "Bei 0 verborgenen Ursachen sind 100 % der zufälligen Graphen bestimmbar" in text and f"bei 8 nur noch {ev.de(100 * rows[-1]['share'], 0)} %" in text


def test_worlds_verdict_quotes_the_effects_and_the_bounds():
    kind, text = ev.verdict_worlds(ev.two_worlds())
    assert kind == "info" and "in der einen 0,00, in der anderen 0,40" in text and "[−0,30; 0,70]" in text and "Breite von 1,00" in text
