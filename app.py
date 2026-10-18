"""Wann geht es gar nicht? Identifizierbarkeit und der Negativbefund - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zehntes Stück der Linie Kausale Diagramme und Adjustierung. Backdoor, Frontdoor und Instrument sind drei Türen; hier die Frage, ob es überhaupt eine gibt. Gebaut wird ein Diagramm mit
verborgenen gemeinsamen Ursachen; der ID-Algorithmus, die Hedge-Aufzählung und der lineare Jacobi-Rang entscheiden, ob die Wirkung aus Beobachtungsdaten bestimmbar ist.
Kern: idf_identify.py, idf_linear.py, idf_methods.py; Diagramme: dsep_graph.py, bdr_backdoor.py und ins_criterion.py (wortgleich aus den Vorgängern).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import idf_constants as C
from idf_evaluation import (
    Settings,
    analyse,
    de,
    exhaustive,
    hedge_text,
    random_experiment,
    trace_text,
    two_worlds,
    verdict_exhaustive,
    verdict_graph,
    verdict_kinds,
    verdict_random,
    verdict_worlds,
)
from idf_pdf_export import build_pdf
from idf_presets import BI_KEYS, DIR_KEYS, apply_preset, init_session_state_defaults, load_permalink_settings, settings_from_state, sync_query_params
from idf_visualization import (
    build_examples_table,
    build_graph,
    build_kinds_chart,
    build_kinds_table,
    build_methods_table,
    build_random_chart,
    build_random_table,
    build_share_chart,
    build_share_table,
    build_worlds_chart,
    build_worlds_table,
)

st.set_page_config(page_title="Wann geht es gar nicht? – Sebastian Hanisch", layout="wide")

SPINNER = "Experiment rechnet über alle Graphen …"
KIND_SHORT = {"trivial": "trivial", "backdoor": "Backdoor", "frontdoor": "Frontdoor", "napkin": "nur der ID", "linear_iv": "nur linear (Instrument)", "linear_other": "nur linear", "none": "keine"}


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=SPINNER)
def _exhaustive():
    return exhaustive(3), exhaustive(4)


@st.cache_data(show_spinner=False)
def _random():
    return random_experiment()


def verdict(kind_text):
    kind, text = kind_text
    getattr(st, kind)(text)


st.title("🚧 Wann geht es gar nicht?")
st.markdown(
    """
**Wenn keine Tür offen ist, gibt es vielleicht gar keine.** Dies ist das zehnte Stück der Linie **Kausale Diagramme und Adjustierung**. Backdoor (Stück 3), Frontdoor (Stück 8) und Instrument
(Stück 9) sind drei Türen, und jede war nur manchmal offen. Hier die Frage dahinter: Gibt es für dieses Diagramm **überhaupt** ein Verfahren, das die Wirkung von x auf y aus Beobachtungsdaten
bestimmt? Gebaut wird ein Diagramm mit **verborgenen gemeinsamen Ursachen** (gestrichelte rote Bögen); drei Wege entscheiden, und der negative Befund kommt mit einem **Beweis**.

Weiter unten: vier Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So liest man das Diagramm", expanded=True):
    st.markdown(
        """
1. **Durchgezogene Pfeile** sind Wirkungen zwischen beobachteten Größen (nur von links nach rechts im Alphabet: A vor B vor C vor D). **Gestrichelte rote Bögen** sind verborgene gemeinsame Ursachen zweier Größen.
2. **Bestimmbar** heißt: Aus der Verteilung der beobachteten Größen allein, ohne weitere Annahme über die Form der Zusammenhänge, folgt die Verteilung von y bei einem Eingriff auf x.
3. **Der ID-Algorithmus** entscheidet das vollständig; seine **Spur** zeigt, welche Zeile gegriffen hat. Bei „nicht bestimmbar“ endet er in einem **Hedge**: zwei verschachtelte Teilgraphen F und F′, die denselben Beweis liefern.
4. **Linear** heißt: Wenn alle Zusammenhänge linear sind, reicht manchmal weniger (zum Beispiel ein Instrument). Der Vergleich zeigt, wie viel eine Modellannahme kauft.
        """
    )

st.caption("🎯 Schnellstart – ein Beispieldiagramm laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Beispiel zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Diagramm")
    st.markdown("**Gerichtete Pfeile**")
    for pair, key in DIR_KEYS.items():
        st.checkbox(f"{C.NODE_LETTERS[pair[0]]} → {C.NODE_LETTERS[pair[1]]}", key=key)
    st.markdown("**Verborgene gemeinsame Ursachen**")
    for pair, key in BI_KEYS.items():
        st.checkbox(f"{C.NODE_LETTERS[pair[0]]} ↔ {C.NODE_LETTERS[pair[1]]}", key=key, help="Eine unbeobachtete Ursache, die beide Größen bewegt.")
    st.markdown("**Wirkung, nach der gefragt wird**")
    st.selectbox("Eingriff auf x", list(range(C.N_NODES)), format_func=lambda v: C.NODE_LETTERS[v], key="x_select", help="Die Größe, in die eingegriffen wird (Regel B).")
    st.selectbox("Ergebnis y", list(range(C.N_NODES)), format_func=lambda v: C.NODE_LETTERS[v], key="y_select", help="Die Größe, deren Verteilung bei dem Eingriff gefragt ist (Servicegrad).")

settings = settings_from_state()
sync_query_params(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
if settings.x == settings.y:
    st.error("x und y müssen verschiedene Knoten sein.")
    st.stop()
a = _analysis(settings)

(c1, c2), (c3, c4) = st.columns(2), st.columns(2)
c1.metric("ID-Algorithmus", "bestimmbar" if a.identified else "nicht bestimmbar", help="Entscheidet vollständig, ob P(y | do(x)) aus der Beobachtungsverteilung folgt.")
c2.metric("Hedge-Aufzählung", "kein Hedge" if a.hedge is None else "Hedge gefunden", help="Zweiter Weg zum selben Satz: ein Hedge existiert genau dann, wenn die Wirkung nicht bestimmbar ist.")
c3.metric("Lineares Modell", "bestimmbar" if a.linear else "nicht bestimmbar", help="Generische lokale Bestimmbarkeit der Gesamtwirkung im linear-gaußschen Modell.")
c4.metric("Einordnung", KIND_SHORT[a.kind], help="Welche Tür der Linie die Wirkung löst, falls eine es tut.")
if not a.consistent:
    st.error("ID-Algorithmus und Hedge-Aufzählung widersprechen sich: Das darf nicht vorkommen.")

left, right = st.columns([1.1, 1])
with left:
    st.plotly_chart(build_graph(a), width="stretch", key="graph_chart")
    st.caption("Durchgezogen: gerichtete Pfeile. Gestrichelt rot: verborgene gemeinsame Ursachen. Grüner Rand: x, orange gefüllt: y. Bei „nicht bestimmbar“ sind die Knoten des Hedges markiert (rot: F′, orange: F).")
with right:
    st.markdown("**Spur des ID-Algorithmus**")
    for i, line in enumerate(trace_text(a.trace), 1):
        st.markdown(f"{i}. {line}")
    if a.hedge:
        st.markdown("**Hedge (der Beweis der Verneinung)**")
        st.markdown(hedge_text(a.hedge))
verdict(verdict_graph(a))
st.dataframe(build_methods_table(a), hide_index=True, width="stretch")

if st.button("📄 PDF der aktuellen Auswertung erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(a))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="identifizierbarkeit.pdf", mime="application/pdf", key="pdf_download")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1 und 2: Alle Graphen mit drei und vier Knoten")
st.caption("Alle 64 Graphen mit drei und alle 4 096 Graphen mit vier Knoten (gerichtete Pfeile von links nach rechts, jede Kante auch als verborgene Ursache möglich) und jedes Paar (x, y) mit gerichtetem Pfad "
           "von x nach y. Die Anteile gelten für diese Aufzählung, nicht für die Häufigkeit in der Praxis.")
if st.button("▶ Experiment 1 und 2 rechnen (etwa 20 Sekunden)", key="exhaustive_run"):
    st.session_state["exhaustive_ready"] = True
if st.session_state.get("exhaustive_ready"):
    res3, res4 = _exhaustive()
    st.markdown("**Experiment 1: Wie viel verborgene Ursache verträgt die Bestimmbarkeit?**")
    st.plotly_chart(build_share_chart(res3, res4), width="stretch", key="share_chart")
    verdict(verdict_exhaustive(res3, res4))
    st.dataframe(build_share_table(res3, res4), hide_index=True, width="stretch")
    st.markdown("**Experiment 2: Wer löst die bestimmbaren Fälle?**")
    st.plotly_chart(build_kinds_chart(res4), width="stretch", key="kinds_chart")
    verdict(verdict_kinds(res4))
    st.dataframe(build_kinds_table(res4), hide_index=True, width="stretch")
    st.caption("Einige Beispiele für Fälle, die nur der ID-Algorithmus findet (unter anderem das Napkin; bestimmbar ohne Backdoor-Menge, Frontdoor-Menge und Instrument), die kleinsten zuerst:")
    st.dataframe(build_examples_table(res4), hide_index=True, width="stretch")

st.subheader("🔬 Experiment 3: Fünf Knoten, zufällige Graphen")
res5 = _random()
st.caption(f"Je Zahl verborgener Ursachen {C.RANDOM_PER} zufällige Graphen mit fünf Knoten (jeder mögliche Pfeil mit Wahrscheinlichkeit {de(C.RANDOM_P_DIR, 1)}), x und y zufällig unter den Paaren mit gerichtetem Pfad.")
st.plotly_chart(build_random_chart(res5), width="stretch", key="random_chart")
verdict(verdict_random(res5))
st.dataframe(build_random_table(res5), hide_index=True, width="stretch")

st.subheader("🔬 Experiment 4: Zwei Welten, gleiche Daten")
w = two_worlds()
st.caption(f"Bow-Arc (A → B mit verborgener Ursache) mit binären Variablen und der beobachteten Verteilung P(x = 1) = {de(C.WORLD_PX, 1)}, P(y = 1 | x = 1) = {de(C.WORLD_P1, 1)}, P(y = 1 | x = 0) = {de(C.WORLD_P0, 1)}. "
           "Welt A: Eine verborgene Ursache bestimmt x und y, es gibt keinen Pfeil von x auf y. Welt B: Es gibt den Pfeil, aber keine verborgene Ursache.")
st.dataframe(build_worlds_table(w), hide_index=True, width="stretch")
st.plotly_chart(build_worlds_chart(w), width="stretch", key="worlds_chart")
verdict(verdict_worlds(w))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Diagramm ist bekannt** | Alle Urteile gelten nur für den vorausgesetzten Graphen; ein falsches Diagramm gibt ein sicheres, aber falsches Urteil. | Wie falsch darf das Diagramm sein? |
| **Ein Eingriff und ein Ziel** | Mehrere Eingriffe, bedingte Wirkungen und Wirkungen auf Teilgruppen sind nicht gebaut. | nicht gebaut |
| **Keine Modellannahme** | Jede Annahme (Linearität, ein Instrument) macht mehr bestimmbar; Experiment 1 zeigt den Unterschied. | Sensitivität und Falsifikation |
| **Bestimmbar heißt gut schätzbar** | Auch bestimmbare Fälle brauchen genug Daten, Überlappung und ein gutes Modell. | Schätzen (Stück 6) |
| **Nicht bestimmbar heißt wertlos** | Ohne Annahme bleiben nur Schranken (Experiment 4); wie weit eine Annahme falsch sein darf, ist eine eigene Frage. | Sensitivität und Falsifikation |
| **Keine Selektion, kein Transport** | Wirkungen in einer anderen Gruppe oder bei verzerrter Stichprobe sind eigene Fragen. | Übertragbarkeit |
| **Die Anteile sind Häufigkeiten** | Sie gelten für alle Graphen dieser Größe oder für zufällige Graphen, nicht für Diagramme aus der Praxis. | nicht gebaut |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Diagramm mit verborgenen Ursachen (ADMG).** Gerichtete Pfeile $i \to j$ und bidirektionale Kanten $i \leftrightarrow j$ für eine unbeobachtete gemeinsame Ursache. Die **C-Komponenten** sind die
zusammenhängenden Komponenten der bidirektionalen Kanten.

**Identifizierbarkeit.** $P(y \mid \mathrm{do}(x))$ ist bestimmbar, wenn alle Modelle mit dem Diagramm und derselben Beobachtungsverteilung $P(V)$ dieselbe Verteilung unter dem Eingriff ergeben.

**ID-Algorithmus** (fünf Zeilen, hier nur als Entscheidung): (1) kein Eingriff übrig: Randverteilung; (2) nur Vorfahren von $Y$ zählen; (3) Eingriffe auf Knoten ohne Weg zu $Y$ im Graphen ohne Pfeile in
$X$ ändern nichts; (4) zerfällt $G \setminus X$ in mehrere C-Komponenten, zerfällt die Wirkung in ein Produkt; (5) bei genau einer C-Komponente $S$: (a) ist $G$ selbst eine C-Komponente, gibt es einen Hedge,
(b) ist $S$ eine C-Komponente von $G$, ist die Wirkung bestimmbar, (c) liegt $S$ in einer größeren C-Komponente $S'$, wird im Teilgraphen $G_{S'}$ weitergerechnet.

**Hedge.** Zwei C-Wälder $F' \subseteq F$ (jeder Knoten höchstens ein Kind) mit derselben Wurzelmenge $R \subseteq \mathrm{An}(Y)$ im Graphen ohne Pfeile in $X$, wobei $F$ Knoten von $X$ enthält und $F'$ keinen.
Die Wirkung ist genau dann nicht bestimmbar, wenn ein Hedge existiert.

**Lineares Modell.** $\Sigma(\theta) = (I-B)^{-1}\Omega(I-B)^{-\top}$ mit einem Koeffizienten je Pfeil, einer Kovarianz je verborgener Ursache und einer Varianz je Knoten. Die Gesamtwirkung ist generisch
bestimmbar, wenn ihr Gradient im Zeilenraum der Jacobi-Matrix von $\Sigma$ liegt.

**Do-Kalkül.** Drei Regeln (Einfügen und Löschen von Beobachtungen, Austausch von Eingriff und Beobachtung, Einfügen und Löschen von Eingriffen), jede mit einer d-Separation-Bedingung im Graphen mit
abgeschnittenen Pfeilen; der ID-Algorithmus findet eine Ableitung, wenn eine existiert. Die Regeln sind hier nicht einzeln gebaut.

**Schranken ohne Annahme** (Manski, binäres $x$ und $y$): $E[Y(1)] \in [P(1,1),\, P(1,1) + P(x=0)]$, $E[Y(0)] \in [P(0,1),\, P(0,1) + P(x=1)]$; die Wirkung liegt in einem Intervall der Breite 1.

**Literatur.** J. Tian, J. Pearl, *A general identification condition for causal effects*, AAAI 2002; I. Shpitser, J. Pearl, *Identification of joint interventional distributions in recursive semi-Markovian
causal models*, AAAI 2006; Y. Huang, M. Valtorta, *Pearl's calculus of intervention is complete*, UAI 2006; C. Manski, *Nonparametric bounds on treatment effects*, American Economic Review 80, 1990
(alle aus dem Gedächtnis, nicht geprüft; die Definition des Hedge wurde in Zusammenfassungen gelesen, nicht im Volltext).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Kausale Diagramme: von Konfundierung bis Wahl](https://sebastianhanisch.net/konzepte-kausale-diagramme.html)."
)
