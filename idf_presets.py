"""Permalink, Presets und der Zustand der Kästchen (Standardmuster aus dem Demo-Portfolio, angepasst: Das Diagramm besteht aus Kästchen statt aus Reglern)."""

import streamlit as st

import idf_constants as C
from idf_evaluation import Settings

DIR_KEYS = {pair: f"dir_{pair[0]}{pair[1]}" for pair in C.PAIRS}
BI_KEYS = {pair: f"bi_{pair[0]}{pair[1]}" for pair in C.PAIRS}
DEFAULT_PRESET = next(iter(C.PRESETS.values()))


def _set_state(p: dict):
    for k, pair in enumerate(C.PAIRS):
        st.session_state[DIR_KEYS[pair]] = bool(p["d"] >> k & 1)
        st.session_state[BI_KEYS[pair]] = bool(p["b"] >> k & 1)
    st.session_state["x_select"] = p["x"]
    st.session_state["y_select"] = p["y"]


def init_session_state_defaults():
    if "x_select" not in st.session_state:
        _set_state(DEFAULT_PRESET)


def apply_preset(name):
    _set_state(C.PRESETS[name])


def settings_from_state() -> Settings:
    d = sum(1 << k for k, pair in enumerate(C.PAIRS) if st.session_state.get(DIR_KEYS[pair]))
    b = sum(1 << k for k, pair in enumerate(C.PAIRS) if st.session_state.get(BI_KEYS[pair]))
    return Settings(d, b, int(st.session_state["x_select"]), int(st.session_state["y_select"]))


def _clamped(value, lo, hi):
    return max(lo, min(hi, value))


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die erlaubten Bereiche begrenzt (Masken 0 bis 63, Knoten 0 bis 3)."""
    if "permalink_loaded" in st.session_state:
        return
    init_session_state_defaults()
    qp = st.query_params
    p = {"d": None, "b": None, "x": None, "y": None}
    for key, hi in (("d", C.MASK_MAX), ("b", C.MASK_MAX), ("x", C.N_NODES - 1), ("y", C.N_NODES - 1)):
        if key in qp:
            try:
                p[key] = _clamped(int(float(qp[key])), 0, hi)
            except (ValueError, TypeError):
                pass
    current = settings_from_state()
    _set_state({"d": current.d if p["d"] is None else p["d"], "b": current.b if p["b"] is None else p["b"],
                "x": current.x if p["x"] is None else p["x"], "y": current.y if p["y"] is None else p["y"]})
    st.session_state["permalink_loaded"] = True


def sync_query_params(s: Settings):
    """Die Adresszeile spiegelt die Konfiguration."""
    try:
        st.query_params["d"] = str(s.d)
        st.query_params["b"] = str(s.b)
        st.query_params["x"] = str(s.x)
        st.query_params["y"] = str(s.y)
    except Exception:
        pass
