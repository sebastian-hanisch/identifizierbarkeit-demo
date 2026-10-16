# Wann geht es gar nicht? Identifizierbarkeit – Streamlit-Demo

Zehntes Stück der Linie **Kausale Diagramme und Adjustierung** in der „Konzepte“-Reihe im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning). Nachfolger von [instrumente-demo](https://github.com/sebastian-hanisch/instrumente-demo): Backdoor, Frontdoor und Instrument sind drei Türen, und jede war nur manchmal offen. Hier die Frage dahinter: Gibt es für ein Diagramm mit verborgenen gemeinsamen Ursachen **überhaupt** ein Verfahren, das die Wirkung aus Beobachtungsdaten bestimmt, und wenn nicht, was ist der Beweis?

## Kernfrage

Wann ist P(y | do(x)) aus der Beobachtungsverteilung bestimmbar, und wann gibt es zwei Welten mit denselben Daten und verschiedener Wirkung? Der ID-Algorithmus entscheidet vollständig, die Hedge-Aufzählung liefert den Beweis der Verneinung, und der lineare Jacobi-Rang zeigt, wie viel eine Modellannahme kauft.

## Modell

- **Vehikel:** kein Datenstrom, sondern ein **Diagramm zum Bauen**: vier beobachtete Größen A bis D (gerichtete Pfeile nur von links nach rechts), sechs mögliche Pfeile, sechs mögliche **verborgene gemeinsame Ursachen** (bidirektionale Kanten, ein Diagramm mit verborgenen Ursachen heißt ADMG), und die Wahl von x (Regel B) und y (Servicegrad).
- **Presets:** Instrument (Voreinstellung), Bow-Arc, Backdoor, Frontdoor, Napkin, viele verborgene Ursachen.
- **Experimente** sind Aufzählungen **aller** Graphen mit drei und vier Knoten (ganzzahlig, exakt), zufällige Graphen mit fünf Knoten über feste `SplitMix64`-Ströme (Generator `kausal_generator.py`, wortgleich in allen Stücken der Linie) und eine exakte Rechnung mit zwei Welten.

## Methodik

- **ID-Algorithmus** (`idf_identify.py`): die fünf Zeilen als Entscheidung, rekursiv auf Teilgraphen, mit **Spur** der angewendeten Zeilen. Ohne Formelausgabe.
- **Hedge-Aufzählung** (`idf_identify.py`): zwei C-Wälder F ⊇ F′ mit gleicher Wurzelmenge aus der Definition (Teilgraphen, in denen Pfeile wegfallen dürfen, damit jeder Knoten höchstens ein Kind hat); liefert den Beweis der Verneinung (F und F′).
- **Linear** (`idf_linear.py`): generische lokale Bestimmbarkeit der Gesamtwirkung im linear-gaußschen Modell über den Rang der Jacobi-Matrix der Kovarianz.
- **Zuordnung** (`idf_methods.py`): welche Tür der Linie die Wirkung löst (Backdoor-Menge, Frontdoor-Menge, Instrument); verborgene Ursachen werden dazu als verborgene Knoten mit zwei Kindern übersetzt und mit `dsep_graph.py`, `bdr_backdoor.py` und `ins_criterion.py` (wortgleich aus den Vorgängern) geprüft.
- **Zwei Welten** und die Schranken ohne Annahme (Manski, binäres x und y) für den Bow-Arc.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Die Anteile gelten für die **Aufzählung** (alle Graphen, alle Paare (x, y) mit gerichtetem Pfad) bzw. das Ensemble der Zufallsgraphen, nicht für die Häufigkeit in der Praxis.

| Frage | Befund | Test |
|---|---|---|
| Benannte Graphen | **Bow-Arc** (A → B, A ↔ B): nicht bestimmbar, auch nicht linear. **Backdoor**, **Frontdoor**, **Napkin** (A → B → C → D mit A ↔ C, A ↔ D): bestimmbar. **Instrument** (A → B → C, B ↔ C): ohne Modellannahme **nicht** bestimmbar, im linearen Modell mit dem Instrument A schon. Napkin hat weder Backdoor-Menge noch Frontdoor-Menge noch Instrument. | `test_named_graphs` |
| Wie viel verborgene Ursache verträgt die Bestimmbarkeit? (alle Graphen mit drei Knoten, 104 Fälle) | Ohne Modellannahme bestimmbar **45 (43,3 %)**, linear **50 (48,1 %)**; die 5 Differenzfälle sind alle Instrumente. Nach Zahl der verborgenen Ursachen 0 / 1 / 2 / 3: **100 / 64 / 18 / 0 %**. | `test_experiment_1_three_nodes` |
| Und bei vier Knoten? (alle 4 096 Graphen, 14 272 Fälle) | Bestimmbar **5 169 (36,2 %)**, linear **6 683 (46,8 %)**. Nach 0 / 1 / 2 / 3 / 4 / 5 / 6 verborgenen Ursachen: **100 / 81 / 57 / 31 / 15 / 5 / 0 %** (linear 100 / 83 / 65 / 48 / 27 / 10 / 0 %). Nicht ohne Annahme bestimmbar, aber linear: 1 514. Ohne Annahme bestimmbar, aber nicht linear: **0**. | `test_experiment_1_four_nodes` |
| Stimmen die Verfahren überein? | ID-Algorithmus und Hedge-Aufzählung widersprechen sich in **0 von 14 376** Fällen (drei und vier Knoten). Eine erste Fassung der Hedge-Aufzählung mit nur induzierten Teilgraphen widersprach in 289 Fällen: Ein Hedge braucht Wälder, in denen Pfeile wegfallen dürfen. | `test_id_and_hedge_agree_everywhere_and_id_implies_linear` |
| Wer löst die bestimmbaren Fälle? (vier Knoten) | Backdoor-Menge **4 956**, Frontdoor zusätzlich **176**, **37 (0,7 %)** nur durch den ID-Algorithmus (die Napkin-Familie). Nur linear: 888 durch ein Instrument, 626 anders. Nicht bestimmbar, auch nicht linear: 7 589 (53,2 %). | `test_experiment_2_kinds` |
| Wie fällt es bei fünf Knoten und zufälligen Graphen? (je 800 Graphen, Pfeile mit Wahrscheinlichkeit 0,5) | Bestimmbar bei 0 / 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 verborgenen Ursachen: **100 / 86 / 72 / 58 / 40 / 28 / 20 / 12 / 6 %**. | `test_experiment_3_random_graphs` |
| Was heißt „nicht bestimmbar“? (Bow-Arc, binär: P(x = 1) = 0,5, P(y = 1 \| x = 1) = 0,7, P(y = 1 \| x = 0) = 0,3) | Welt A: verborgene Ursache, kein Pfeil, Wirkung **0,00**; Welt B: Pfeil, keine verborgene Ursache, Wirkung **0,40**; Zellen in beiden 0,35 / 0,15 / 0,15 / 0,35, also **identische Daten**. Ohne jede Annahme liegt die Wirkung in **[−0,30; 0,70]**, Breite 1,00. | `test_experiment_4_two_worlds` |

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Diagramm ist bekannt** | Alle Urteile gelten nur für den vorausgesetzten Graphen; ein falsches Diagramm gibt ein sicheres, aber falsches Urteil. | Wie falsch darf das Diagramm sein? |
| **Ein Eingriff und ein Ziel** | Mehrere Eingriffe, bedingte Wirkungen und Wirkungen auf Teilgruppen sind nicht gebaut. | nicht gebaut |
| **Keine Modellannahme** | Jede Annahme (Linearität, ein Instrument) macht mehr bestimmbar; Experiment 1 zeigt den Unterschied. | Sensitivität und Falsifikation |
| **Bestimmbar heißt gut schätzbar** | Auch bestimmbare Fälle brauchen genug Daten, Überlappung und ein gutes Modell. | Schätzen (Stück 6) |
| **Nicht bestimmbar heißt wertlos** | Ohne Annahme bleiben nur Schranken (Experiment 4); wie weit eine Annahme falsch sein darf, ist eine eigene Frage. | Sensitivität und Falsifikation |
| **Keine Selektion, kein Transport** | Wirkungen in einer anderen Gruppe oder bei verzerrter Stichprobe sind eigene Fragen. | Übertragbarkeit |
| **Die Anteile sind Häufigkeiten** | Sie gelten für alle Graphen dieser Größe oder für zufällige Graphen, nicht für Diagramme aus der Praxis. | nicht gebaut |

Die lineare Aussage gilt **generisch** (fast überall im Parameterraum) und ist von der Wahl des Parameterpunktes unabhängig (getestet mit mehreren Punkten). Die Definition des Hedge und der Zeilen des ID-Algorithmus ist aus dem Gedächtnis geschrieben und in Zusammenfassungen gegengelesen, nicht im Volltext der Quelle geprüft; die Kreuzprüfung (zwei Wege zum selben Satz, ein dritter über das lineare Modell als einseitige Probe) fängt Tippfehler, nicht einen gemeinsamen Irrtum. Die Quellen im 📐-Expander sind aus dem Gedächtnis, nicht geprüft.

## Bezug zu den Nachbarn im Portfolio

- [backdoor-demo](https://github.com/sebastian-hanisch/backdoor-demo), [frontdoor-demo](https://github.com/sebastian-hanisch/frontdoor-demo), [instrumente-demo](https://github.com/sebastian-hanisch/instrumente-demo): die drei Türen. Ihre Prüfungen (Backdoor-Kriterium, Frontdoor-Kriterium, Instrument-Kriterium) laufen hier wortgleich mit; das Stück fragt, ob es **irgendeine** Tür gibt.
- [d-separation-demo](https://github.com/sebastian-hanisch/d-separation-demo): die d-Separation (`dsep_graph.py`) rechnet hier die Diagramme mit verborgenen Knoten.
- [adjustierungsmenge-demo](https://github.com/sebastian-hanisch/adjustierungsmenge-demo): wählt unter mehreren gültigen Mengen; hier ist die Frage, ob es eine gibt.
- **Abgrenzung zur Sensitivität:** Wenn nicht bestimmbar, wie sehr darf die Annahme falsch sein? Das ist die Frage des folgenden Stücks der Linie; hier nur die Schranken ohne Annahme.

## Tests

Mini-Graphen von Hand (Bow-Arc, Backdoor, Frontdoor, Instrument, Napkin mit Spur und Hedge), C-Komponenten und Vorfahren von Hand, Monotonie (eine zusätzliche verborgene Ursache macht nie bestimmbar, was vorher nicht bestimmbar war), ID gegen Hedge-Aufzählung auf **allen** Graphen mit drei und vier Knoten, ID ⇒ linear, ein hinreichendes Kriterium (kein bidirektionaler Pfad von x zu einem Kind) auf allen Dreiergraphen, Backdoor- und Frontdoor-Mengen ⇒ bestimmbar, ein explizites Paar linearer Modelle mit gleicher Kovarianz und verschiedener Wirkung im Bow-Arc, jede README-Zahl in `test_claims.py`, AppTest (Presets, jedes Kästchen, Permalink, PDF, der schwere Versuch auf Knopfdruck), Footer und Laufzeit-Importe.

```bash
python -m pytest tests -q
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `kausal_generator.py` | gemeinsamer Generator der Linie (SplitMix64, Normalverteilung, Strukturmodell) |
| `dsep_graph.py`, `bdr_backdoor.py`, `ins_criterion.py` | d-Separation, Backdoor, Instrument- und Frontdoor-Kriterium (wortgleich aus Stück 2, 3 und 9) |
| `idf_identify.py` | C-Komponenten, ID-Algorithmus mit Spur, Hedge-Aufzählung |
| `idf_linear.py` | generische lineare Bestimmbarkeit (Jacobi-Rang) |
| `idf_methods.py` | Zuordnung zu Backdoor, Frontdoor und Instrument über verborgene Knoten |
| `idf_evaluation.py` | Analyse eines Graphen, vier Experimente, Verdikte |
| `idf_visualization.py`, `idf_pdf_export.py` | Figuren, Tabellen, PDF |
| `idf_constants.py`, `idf_presets.py` | Knoten, Masken, Presets, Permalink |
| `tests/` | Mini-Graphen, Orakel, Claims, App |

## Bewusst nicht umgesetzt

- **Do-Kalkül als eigener Ableiter** (Regel wählen, Mengen wählen, Formel ausgeben): die Spur des ID-Algorithmus ist die Ableitung, die Regeln stehen im Expander.
- **Formelausgabe der Wirkung:** nur die Entscheidung und die Zuordnung; die Formeln für Backdoor und Frontdoor stehen in Stück 3 und 8.
- **Bedingte Instrumente, mehrere Eingriffe, bedingte Wirkungen:** ein Eingriff, ein Ziel, nur unbedingte Instrumente.
- **Schranken mit Annahmen (Balke und Pearl), Sensitivitätsanalyse:** nur die Schranken ohne Annahme für den Bow-Arc.
- **Mehr als vier Knoten im Diagramm zum Bauen:** vier Knoten, damit alle 4 096 Graphen aufzählbar sind; fünf Knoten nur zufällig.
- **Praxisdaten:** nicht gebaut; es gibt keine Daten, nur Diagramme.

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python 3.12.

Gebaut mit Streamlit, Plotly, numpy, pandas und fpdf2.

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
