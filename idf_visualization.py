"""Plotly-Figuren und Tabellen. Alle Achsen fest (fixedrange), damit Touch-Scrollen nicht am Diagramm hängen bleibt."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import idf_constants as C
from idf_evaluation import KIND_TEXT, Analysis, de, edge_text, names_of

POS = {0: (0.0, 0.5), 1: (0.5, 1.0), 2: (0.5, 0.0), 3: (1.0, 0.5)}
CENTER = (0.5, 0.5)


def _fixed(fig: go.Figure, height: int = 380, **layout) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.22), **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _arrow(fig, p0, p1, color, width=2, shrink=0.12):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / ln, dy / ln
    fig.add_annotation(x=x1 - ux * shrink, y=y1 - uy * shrink, ax=x0 + ux * shrink, ay=y0 + uy * shrink, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3,
                       arrowsize=1.3, arrowwidth=width, arrowcolor=color, text="")


def _curve(p0, p1, bulge=0.22, steps=24):
    """Gebogene Linie von p0 nach p1, nach außen (weg von der Mitte) gewölbt."""
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    ln = (dx * dx + dy * dy) ** 0.5 or 1.0
    nx, ny = -dy / ln, dx / ln
    if (mx + nx - CENTER[0]) ** 2 + (my + ny - CENTER[1]) ** 2 < (mx - nx - CENTER[0]) ** 2 + (my - ny - CENTER[1]) ** 2:
        nx, ny = -nx, -ny
    cx, cy = mx + nx * bulge * 2, my + ny * bulge * 2
    ts = [k / steps for k in range(steps + 1)]
    return [(1 - t) ** 2 * x0 + 2 * t * (1 - t) * cx + t ** 2 * x1 for t in ts], [(1 - t) ** 2 * y0 + 2 * t * (1 - t) * cy + t ** 2 * y1 for t in ts]


def build_graph(a: Analysis) -> go.Figure:
    """Das Diagramm: durchgezogene Pfeile gerichtet, gestrichelte rote Bögen verborgene gemeinsame Ursachen; x grün, y orange umrandet; Knoten eines Hedges (F′ rot, F orange) markiert."""
    s = a.settings
    fig = go.Figure()
    for (i, j) in sorted(s.hidden):
        xs, ys = _curve(POS[i], POS[j])
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_BAD, width=2.5, dash="dash"), hoverinfo="skip", showlegend=False))
    for (i, j) in sorted(s.directed):
        _arrow(fig, POS[i], POS[j], "#6b6b6b", 3)
    roles = {s.x: "Regel B (x)", s.y: "Servicegrad (y)"}
    ring = {}
    if a.hedge:
        for v in a.hedge["F"]:
            ring[v] = C.COLOR_TRUTH
        for v in a.hedge["Fp"]:
            ring[v] = C.COLOR_BAD
    for v in range(C.N_NODES):
        color = ring.get(v, C.COLOR_GOOD if v == s.x else "#1b1b1b")
        width = 6 if v in ring else (5 if v in (s.x, s.y) else 2)
        fig.add_trace(go.Scatter(x=[POS[v][0]], y=[POS[v][1]], mode="markers+text", text=[f"{C.NODE_LETTERS[v]}<br>{roles.get(v, 'Größe')}"], textposition="middle center", textfont=dict(size=10),
                                 marker=dict(size=84, color="rgba(47,107,101,0.12)" if v != s.y else "rgba(214,138,46,0.18)", line=dict(width=width, color=color)), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, range=[-0.3, 1.3])
    fig.update_yaxes(visible=False, range=[-0.3, 1.3])
    return _fixed(fig, 400, showlegend=False)


def build_methods_table(a: Analysis) -> pd.DataFrame:
    m = a.methods
    return pd.DataFrame([
        {"Verfahren": "Backdoor-Adjustierung (Stück 3)", "Ergebnis": f"Menge {names_of(m['backdoor'])}" if m["backdoor"] is not None else "keine gültige Menge"},
        {"Verfahren": "Frontdoor (Stück 8)", "Ergebnis": f"Menge {names_of(m['frontdoor'])}" if m["frontdoor"] is not None else "keine gültige Menge"},
        {"Verfahren": "Instrument im linearen Modell (Stück 9)", "Ergebnis": names_of(m["instruments"]) if m["instruments"] else "keines"},
        {"Verfahren": "ID-Algorithmus (nicht-parametrisch)", "Ergebnis": "bestimmbar" if a.identified else "nicht bestimmbar"},
        {"Verfahren": "Hedge-Aufzählung (zweiter Weg zum selben Satz)", "Ergebnis": "kein Hedge" if a.hedge is None else "Hedge gefunden"},
        {"Verfahren": "lineares Modell (Rang der Jacobi-Matrix)", "Ergebnis": f"bestimmbar (Rang {a.rank} von {a.params} Parametern)" if a.linear else f"nicht bestimmbar (Rang {a.rank} von {a.params} Parametern)"},
    ])


# ----------------------------------------------------------------------------- Experiment 1

def build_share_chart(res3: dict, res4: dict) -> go.Figure:
    fig = go.Figure()
    for res, label, dash in ((res3, "3 Knoten", "dot"), (res4, "4 Knoten", "solid")):
        bs = list(res["by_bi"])
        fig.add_trace(go.Scatter(x=bs, y=[100 * res["by_bi"][b]["identified"] / res["by_bi"][b]["cases"] for b in bs], mode="lines+markers", name=f"{label}: ohne Modellannahme",
                                 line=dict(color=C.COLOR_GOOD, dash=dash, width=3)))
        fig.add_trace(go.Scatter(x=bs, y=[100 * res["by_bi"][b]["linear"] / res["by_bi"][b]["cases"] for b in bs], mode="lines+markers", name=f"{label}: linear",
                                 line=dict(color=C.COLOR_CONTROL, dash=dash, width=2)))
    fig.update_xaxes(title="Zahl der verborgenen gemeinsamen Ursachen im Graphen", dtick=1)
    fig.update_yaxes(title="Anteil der Fälle mit bestimmbarer Wirkung (%)", range=[-2, 104])
    return _fixed(fig, 400)


def build_share_table(res3: dict, res4: dict) -> pd.DataFrame:
    out = []
    for b in sorted(set(res3["by_bi"]) | set(res4["by_bi"])):
        row = {"verborgene Ursachen": b}
        for res, label in ((res3, "3 Knoten"), (res4, "4 Knoten")):
            r = res["by_bi"].get(b)
            row[f"{label}: Fälle"] = str(r["cases"]) if r else "-"
            row[f"{label}: bestimmbar"] = f"{de(100 * r['identified'] / r['cases'], 0)} %" if r else "-"
            row[f"{label}: linear"] = f"{de(100 * r['linear'] / r['cases'], 0)} %" if r else "-"
        out.append(row)
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- Experiment 2

KIND_ORDER = (("none", "nicht bestimmbar, auch linear nicht", C.COLOR_BAD), ("linear_other", "nur linear, kein einzelnes Instrument", C.COLOR_NEUTRAL), ("linear_iv", "nur linear, durch ein Instrument", C.COLOR_CONTROL),
              ("backdoor", "bestimmbar durch Backdoor", C.COLOR_GOOD), ("frontdoor", "bestimmbar durch Frontdoor (ohne Backdoor)", "#6aa49d"), ("napkin", "bestimmbar nur durch den ID (unter anderem Napkin)", C.COLOR_TRUTH))


def build_kinds_chart(res4: dict) -> go.Figure:
    k = res4["kinds"]
    vals = [k.get(key, 0) for key, _, _ in KIND_ORDER]
    fig = go.Figure(go.Bar(y=[label for _, label, _ in KIND_ORDER], x=[100 * v / res4["cases"] for v in vals], orientation="h", marker_color=[c for _, _, c in KIND_ORDER],
                           text=[f"{v} ({de(100 * v / res4['cases'], 1)} %)" for v in vals], textposition="outside"))
    fig.update_xaxes(title="Anteil der Fälle mit vier Knoten (%)", range=[0, 66])
    fig.update_yaxes(autorange="reversed")
    return _fixed(fig, 360, showlegend=False)


def build_kinds_table(res4: dict) -> pd.DataFrame:
    return pd.DataFrame([{"Einordnung": KIND_TEXT[key], "Fälle": res4["kinds"].get(key, 0), "Anteil": f"{de(100 * res4['kinds'].get(key, 0) / res4['cases'], 1)} %"} for key, _, _ in KIND_ORDER])


def build_examples_table(res4: dict) -> pd.DataFrame:
    return pd.DataFrame([{"gerichtete Pfeile": edge_text(D, "→"), "verborgene Ursachen": edge_text(Bi, "↔"), "x": C.NODE_LETTERS[x], "y": C.NODE_LETTERS[y]}
                         for _, D, Bi, x, y in res4["neither_examples"]])


# ----------------------------------------------------------------------------- Experiment 3

def build_random_chart(rows: list) -> go.Figure:
    fig = go.Figure(go.Scatter(x=[r["hidden"] for r in rows], y=[100 * r["share"] for r in rows], mode="lines+markers+text", line=dict(color=C.COLOR_GOOD, width=3),
                               text=[f"{de(100 * r['share'], 0)} %" for r in rows], textposition="top center"))
    fig.update_xaxes(title="Zahl der verborgenen gemeinsamen Ursachen (fünf Knoten, zehn mögliche Paare)", dtick=1)
    fig.update_yaxes(title="Anteil mit bestimmbarer Wirkung (%)", range=[0, 110])
    return _fixed(fig, 360, showlegend=False)


def build_random_table(rows: list) -> pd.DataFrame:
    return pd.DataFrame([{"verborgene Ursachen": r["hidden"], "Graphen": r["per"], "bestimmbar": f"{de(100 * r['share'], 1)} %"} for r in rows])


# ----------------------------------------------------------------------------- Experiment 4

def build_worlds_table(w: dict) -> pd.DataFrame:
    rows = []
    for (x, y) in ((1, 1), (1, 0), (0, 1), (0, 0)):
        rows.append({"Zelle": f"x = {x}, y = {y}", "Welt A (verborgene Ursache, kein Pfeil)": de(w["joint_a"][(x, y)], 2), "Welt B (Pfeil, keine verborgene Ursache)": de(w["joint_b"][(x, y)], 2)})
    rows.append({"Zelle": "Wirkung von x auf y", "Welt A (verborgene Ursache, kein Pfeil)": de(w["effect_a"], 2), "Welt B (Pfeil, keine verborgene Ursache)": de(w["effect_b"], 2)})
    return pd.DataFrame(rows)


def build_worlds_chart(w: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=w["lower"], y1=w["upper"], fillcolor="rgba(76,120,168,0.15)", line_width=0, annotation_text=f"ohne Annahme: [{de(w['lower'], 2)}; {de(w['upper'], 2)}]", annotation_position="top left")
    fig.add_trace(go.Bar(x=["Welt A", "Welt B"], y=[w["effect_a"], w["effect_b"]], marker_color=[C.COLOR_BAD, C.COLOR_GOOD], text=[de(w["effect_a"], 2), de(w["effect_b"], 2)], textposition="outside"))
    fig.add_hline(y=0.0, line=dict(color="#888888", width=1))
    fig.update_yaxes(title="Wirkung von x auf y", range=[-0.45, 0.85])
    return _fixed(fig, 340, showlegend=False)
