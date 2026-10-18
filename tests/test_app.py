"""End-to-end Smoke-Test via Streamlits AppTest: lädt app.py, klickt jeden Preset-Button, schaltet jedes Kästchen um und prüft, dass kein Python-Fehler auftritt."""

import os

from streamlit.testing.v1 import AppTest

import idf_constants as C
import idf_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 300


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def test_app_loads_without_exception_with_the_instrument_graph():
    at = _fresh_app()
    m = _metrics(at)
    assert m == {"ID-Algorithmus": "nicht bestimmbar", "Hedge-Aufzählung": "Hedge gefunden", "Lineares Modell": "bestimmbar", "Einordnung": "nur linear (Instrument)"}
    assert at.selectbox(key="x_select").value == 1 and at.selectbox(key="y_select").value == 2 and at.checkbox(key="dir_01").value and at.checkbox(key="bi_12").value and not at.checkbox(key="bi_01").value
    assert any("im linearen Modell (generisch) aber schon" in w.value for w in at.warning)


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if label.startswith("▶"):
            continue                                                         # der schwere Versuch läuft im eigenen Test
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_preset_is_applied_to_the_widgets_and_gives_its_verdict():
    labels = {b.label: i for i, b in enumerate(_fresh_app().button)}
    expected = {"Instrument (Voreinstellung)": "nur linear (Instrument)", "Bow-Arc": "keine", "Backdoor": "Backdoor", "Frontdoor": "Frontdoor", "Napkin": "nur der ID", "Viele verborgene Ursachen": "keine"}
    for name, preset in C.PRESETS.items():
        at = _fresh_app()
        at.button[labels[name]].click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])
        assert at.selectbox(key="x_select").value == preset["x"] and at.selectbox(key="y_select").value == preset["y"]
        for k, pair in enumerate(C.PAIRS):
            assert at.checkbox(key=P.DIR_KEYS[pair]).value == bool(preset["d"] >> k & 1) and at.checkbox(key=P.BI_KEYS[pair]).value == bool(preset["b"] >> k & 1), (name, pair)
        assert _metrics(at)["Einordnung"] == expected[name], name


def test_every_checkbox_can_be_toggled():
    for pair in C.PAIRS:
        for keys in (P.DIR_KEYS, P.BI_KEYS):
            at = _fresh_app()
            box = at.checkbox(key=keys[pair])
            box.set_value(not box.value).run(timeout=TIMEOUT)
            assert not at.exception, (keys[pair], [str(e) for e in at.exception])


def test_toggling_a_hidden_cause_changes_the_verdict():
    at = _fresh_app()
    at.button[[b.label for b in at.button].index("Backdoor")].click().run(timeout=TIMEOUT)
    assert _metrics(at)["ID-Algorithmus"] == "bestimmbar"
    at.checkbox(key="bi_12").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception and _metrics(at)["ID-Algorithmus"] == "nicht bestimmbar" and _metrics(at)["Hedge-Aufzählung"] == "Hedge gefunden"


def test_equal_x_and_y_show_an_error_and_stop():
    at = _fresh_app()
    at.selectbox(key="y_select").set_value(1).run(timeout=TIMEOUT)
    assert not at.exception and any("verschiedene Knoten" in e.value for e in at.error)
    assert not at.metric


def test_the_heavy_experiments_run_on_click():
    at = _fresh_app()
    assert "exhaustive_ready" not in at.session_state and not any("Bei vier Knoten" in i.value for i in at.info)
    at.button(key="exhaustive_run").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Bei vier Knoten sind 36,2 %" in i.value for i in at.info) and any("Von 5169 bestimmbaren Fällen" in i.value for i in at.info)


def test_pdf_is_created_only_after_the_click():
    at = _fresh_app()
    assert "pdf_made" not in at.session_state
    at.button(key="pdf_make").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    settings, data = at.session_state["pdf_made"]
    assert data[:5] == b"%PDF-" and len(data) > 1000


def test_permalink_values_are_taken_and_clamped():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["d"] = "9999"
    at.query_params["b"] = "1"
    at.query_params["x"] = "0"
    at.query_params["y"] = "abc"
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert all(at.checkbox(key=P.DIR_KEYS[p]).value for p in C.PAIRS) and at.checkbox(key="bi_01").value and not at.checkbox(key="bi_02").value
    assert at.selectbox(key="x_select").value == 0 and at.selectbox(key="y_select").value == 2                          # y bleibt bei der Voreinstellung


def test_the_address_bar_mirrors_the_settings():
    at = _fresh_app()
    at.checkbox(key="dir_23").set_value(True).run(timeout=TIMEOUT)
    assert at.query_params["d"] in (str(C.PRESETS["Instrument (Voreinstellung)"]["d"] + 32), [str(C.PRESETS["Instrument (Voreinstellung)"]["d"] + 32)])
