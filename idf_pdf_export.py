"""PDF-Export der aktuellen Auswertung (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Pfeile und Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import idf_constants as C
from idf_evaluation import KIND_TEXT, Analysis, edge_text, hedge_text, trace_text, verdict_graph

_REPLACE = {"→": "->", "↔": "<->", "←": "<-", "–": "-", "—": "-", "−": "-", "„": '"', "“": '"', "′": "'", "⊇": ">=", "**": "", "≥": ">=", "≤": "<=", "×": "x"}


def _s(text) -> str:
    out = str(text)
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    s = a.settings
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Wann geht es gar nicht? Identifizierbarkeit"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"Gerichtete Pfeile: {edge_text(s.directed, '->')}. Verborgene gemeinsame Ursachen: {edge_text(s.hidden, '<->')}. "
                            f"Wirkung von {C.NODE_LETTERS[s.x]} auf {C.NODE_LETTERS[s.y]}. Alles ein Modelldiagramm, keine Daten."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(0, 5, _s(f"Urteil: {KIND_TEXT[a.kind]}."), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.6, _s(f"ID-Algorithmus: {'bestimmbar' if a.identified else 'nicht bestimmbar'}; Hedge-Aufzaehlung: {'kein Hedge' if a.hedge is None else 'Hedge gefunden'}; "
                              f"lineares Modell: {'bestimmbar' if a.linear else 'nicht bestimmbar'} (Rang {a.rank} von {a.params} Parametern)."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for line in trace_text(a.trace):
        pdf.multi_cell(0, 4.6, _s(line), new_x="LMARGIN", new_y="NEXT")
    if a.hedge:
        pdf.ln(2)
        pdf.multi_cell(0, 4.6, _s("Hedge: " + hedge_text(a.hedge)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 4.5, _s(verdict_graph(a)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: identifizierbarkeit-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
