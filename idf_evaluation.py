"""Auswertung: ein Graph mit allen Verfahren, die vier Experimente und die Verdikte. Nur numpy und die Module der Linie, kein Streamlit."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np

import idf_constants as C
import idf_identify as I
import idf_linear as L
import idf_methods as M
from kausal_generator import SplitMix64


def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def signed(x: float, digits: int = 2) -> str:
    x = 0.0 if abs(x) < 0.5 * 10 ** -digits * 1e-3 else x
    return ("+" if x >= 0 else "−") + de(abs(x), digits)


def names_of(nodes) -> str:
    return "{" + ", ".join(C.NODE_LETTERS[v] for v in sorted(nodes)) + "}"


def edge_text(edges, arrow: str) -> str:
    return ", ".join(f"{C.NODE_LETTERS[i]} {arrow} {C.NODE_LETTERS[j]}" for i, j in sorted(edges)) or "keine"


@dataclass(frozen=True)
class Settings:
    d: int = C.PRESETS["Instrument (Voreinstellung)"]["d"]
    b: int = C.PRESETS["Instrument (Voreinstellung)"]["b"]
    x: int = C.PRESETS["Instrument (Voreinstellung)"]["x"]
    y: int = C.PRESETS["Instrument (Voreinstellung)"]["y"]

    @property
    def directed(self) -> frozenset:
        return C.edges_of(self.d)

    @property
    def hidden(self) -> frozenset:
        return C.edges_of(self.b)


KIND_TEXT = {
    "trivial": "Kein gerichteter Pfad von x nach y: Die Wirkung ist null und trivial bestimmbar.",
    "backdoor": "bestimmbar durch Backdoor-Adjustierung",
    "frontdoor": "bestimmbar durch die Frontdoor-Formel (ohne Backdoor-Menge)",
    "napkin": "bestimmbar, aber weder durch Backdoor, Frontdoor noch ein Instrument: nur der ID-Algorithmus findet den Weg",
    "linear_iv": "nicht ohne Modellannahme bestimmbar; im linearen Modell mit einem Instrument",
    "linear_other": "nicht ohne Modellannahme bestimmbar; im linearen Modell bestimmbar, aber nicht durch ein einzelnes Instrument",
    "none": "nicht bestimmbar, auch nicht im linearen Modell",
}


@dataclass
class Analysis:
    settings: Settings
    trivial: bool
    identified: bool
    trace: list
    hedge: dict | None
    linear: bool
    rank: int
    params: int
    kind: str
    methods: dict = field(default_factory=dict)

    @property
    def consistent(self) -> bool:
        """ID-Algorithmus und Hedge-Aufzählung sagen dasselbe (ein Hedge existiert genau dann, wenn der ID scheitert)."""
        return self.identified == (self.hedge is None)


def classify(n: int, D, Bi, x: int, y: int, identified: bool, linear: bool) -> str:
    """Welche Tür löst den Fall? Nur so viel rechnen, wie die Einordnung braucht."""
    if not I.has_directed_path(x, y, D, n):
        return "trivial"
    if identified:
        m = M.methods(n, D, Bi, x, y)
        return "backdoor" if m["backdoor"] is not None else "frontdoor" if m["frontdoor"] is not None else "napkin"
    if linear:
        return "linear_iv" if M.methods(n, D, Bi, x, y)["instruments"] else "linear_other"
    return "none"


def analyse(s: Settings) -> Analysis:
    n, D, Bi = C.N_NODES, s.directed, s.hidden
    if s.x == s.y:
        raise ValueError("x und y müssen verschiedene Knoten sein")
    V = frozenset(range(n))
    trivial = not I.has_directed_path(s.x, s.y, D, n)
    trace: list = []
    identified = I.identify({s.y}, {s.x}, V, D, Bi, trace)
    hedge = I.find_hedge(s.x, s.y, V, D, Bi)
    lin, rank, params = L.linear_identified(n, D, Bi, [(s.x, s.y)])
    kind = classify(n, D, Bi, s.x, s.y, identified, lin[(s.x, s.y)])
    return Analysis(s, trivial, identified, trace, hedge, lin[(s.x, s.y)], rank, params, kind, M.methods(n, D, Bi, s.x, s.y))


def trace_text(trace: list) -> list[str]:
    out = []
    for entry in trace:
        line, y = entry[0], entry[1]
        if line == "1":
            out.append("Zeile 1: Es ist kein Eingriff übrig, die Wirkung ist eine Randverteilung.")
        elif line == "2":
            out.append(f"Zeile 2: Nur die Vorfahren von {names_of(y)} zählen: {names_of(entry[2])}.")
        elif line == "3":
            out.append(f"Zeile 3: Zusätzliche Eingriffe auf {names_of(entry[2])} ändern die Wirkung auf {names_of(y)} nicht.")
        elif line == "4":
            out.append(f"Zeile 4: Ohne x zerfällt der Graph in {len(entry[2])} C-Komponenten {', '.join(names_of(c) for c in entry[2])}; die Wirkung ist ein Produkt über sie.")
        elif line == "5a":
            out.append(f"Zeile 5(a): Hedge: Der Graph ist eine einzige C-Komponente, die Wirkung auf {names_of(y)} ist nicht bestimmbar.")
        elif line == "5b":
            out.append(f"Zeile 5(b): {names_of(entry[2])} ist selbst eine C-Komponente: bestimmbar.")
        elif line == "5c":
            out.append(f"Zeile 5(c): {names_of(entry[1])} liegt in der größeren C-Komponente {names_of(entry[2])}: weiter im Teilgraphen.")
    return out


def hedge_text(hedge: dict) -> str:
    f_edges = edge_text(hedge["F_edges"], "→")
    fp_edges = edge_text(hedge["Fp_edges"], "→")
    return (f"F = {names_of(hedge['F'])} mit den Pfeilen {f_edges}; F′ = {names_of(hedge['Fp'])} mit den Pfeilen {fp_edges}; gemeinsame Wurzelmenge {names_of(hedge['R'])}. "
            f"F enthält x, F′ nicht; beide hängen über verborgene Ursachen zusammen.")


# ----------------------------------------------------------------------------- Experiment 1 und 2: alle Graphen mit n Knoten

def pairs_of(n: int) -> list:
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def exhaustive(n: int) -> dict:
    """Alle Graphen mit n Knoten (gerichtete Pfeile i → j für i < j und bidirektionale Kanten i ↔ j) und alle (x, y) mit gerichtetem Pfad: nicht-parametrisch (ID) und linear bestimmbar,
    die Einordnung nach Tür und die Kreuzprüfung der Verfahren (ID gegen Hedge-Aufzählung; ID bestimmbar, aber linear nicht)."""
    pairs = pairs_of(n)
    V = frozenset(range(n))
    by_bi: dict = {}
    kinds: dict = {}
    cases = mismatch = id_not_linear = 0
    neither = []
    for dmask in range(2 ** len(pairs)):
        D = frozenset(pairs[k] for k in range(len(pairs)) if dmask >> k & 1)
        targets = [(x, y) for (x, y) in pairs if I.has_directed_path(x, y, D, n)]
        if not targets:
            continue
        for bmask in range(2 ** len(pairs)):
            Bi = frozenset(pairs[k] for k in range(len(pairs)) if bmask >> k & 1)
            lin, _, _ = L.linear_identified(n, D, Bi, targets)
            for (x, y) in targets:
                ident = I.identify({y}, {x}, V, D, Bi)
                hedge_free = I.find_hedge(x, y, V, D, Bi) is None
                cases += 1
                mismatch += ident != hedge_free
                id_not_linear += ident and not lin[(x, y)]
                kind = classify(n, D, Bi, x, y, ident, lin[(x, y)])
                kinds[kind] = kinds.get(kind, 0) + 1
                row = by_bi.setdefault(len(Bi), [0, 0, 0])
                row[0] += 1
                row[1] += ident
                row[2] += lin[(x, y)]
                if kind == "napkin":
                    neither.append((len(D) + len(Bi), sorted(D), sorted(Bi), x, y))
    neither.sort()
    return {"n": n, "cases": cases, "by_bi": {b: {"cases": c, "identified": i, "linear": l} for b, (c, i, l) in sorted(by_bi.items())}, "kinds": kinds, "mismatch": mismatch,
            "id_not_linear": id_not_linear, "identified": sum(r[1] for r in by_bi.values()), "linear": sum(r[2] for r in by_bi.values()), "neither_examples": neither[:6]}


# ----------------------------------------------------------------------------- Experiment 3: zufällige Graphen mit fünf Knoten

def random_experiment(n: int = C.RANDOM_NODES, per: int = C.RANDOM_PER, max_bi: int = C.RANDOM_MAX_BI, p_dir: float = C.RANDOM_P_DIR) -> list[dict]:
    """Je Zahl verborgener Kanten `per` zufällige Graphen mit gerichtetem Pfad von x nach y (x, y zufällig unter den möglichen Paaren): Anteil bestimmbar."""
    rng = SplitMix64(C.SEED_BASE + 300)
    pairs = pairs_of(n)
    V = frozenset(range(n))
    out = []
    for nb in range(max_bi + 1):
        ok = done = 0
        while done < per:
            u = rng.uniform(2 * len(pairs) + 1)
            D = frozenset(pairs[k] for k in range(len(pairs)) if u[k] < p_dir)
            order = np.argsort(u[len(pairs):2 * len(pairs)])
            Bi = frozenset(pairs[int(k)] for k in order[:nb])
            targets = [(x, y) for (x, y) in pairs if I.has_directed_path(x, y, D, n)]
            if not targets:
                continue
            x, y = targets[min(int(u[-1] * len(targets)), len(targets) - 1)]
            ok += I.identify({y}, {x}, V, D, Bi)
            done += 1
        out.append({"hidden": nb, "per": per, "share": ok / per})
    return out


# ----------------------------------------------------------------------------- Experiment 4: zwei Welten für den Bow-Arc

def joint_of(px: float, p1: float, p0: float) -> dict:
    return {(1, 1): px * p1, (1, 0): px * (1 - p1), (0, 1): (1 - px) * p0, (0, 0): (1 - px) * (1 - p0)}


def manski_bounds(joint: dict) -> tuple[float, float]:
    """Schranken der durchschnittlichen Wirkung ohne jede Annahme (binäres x und y): E[Y(1)] in [P(1,1), P(1,1) + P(x=0)], E[Y(0)] in [P(0,1), P(0,1) + P(x=1)]."""
    px1 = joint[(1, 1)] + joint[(1, 0)]
    return joint[(1, 1)] - joint[(0, 1)] - px1, joint[(1, 1)] + (1 - px1) - joint[(0, 1)]


def two_worlds(px: float = C.WORLD_PX, p1: float = C.WORLD_P1, p0: float = C.WORLD_P0) -> dict:
    """Bow-Arc mit binären Variablen. Welt B: keine Konfundierung, x wirkt mit p1 − p0 auf y. Welt A: eine verborgene Ursache U (P(U=1) = px) bestimmt x = U und y (P(Y=1 | U) = p1 bzw. p0),
    kein Pfeil x → y: Wirkung 0. Beide Welten haben dieselbe Beobachtungsverteilung P(x) P(y | x)."""
    joint_b = joint_of(px, p1, p0)
    joint_a = {(u, y): (px if u == 1 else 1 - px) * ((p1 if u == 1 else p0) if y == 1 else 1 - (p1 if u == 1 else p0)) for u in (0, 1) for y in (0, 1)}
    lo, hi = manski_bounds(joint_b)
    return {"joint_a": joint_a, "joint_b": joint_b, "effect_a": 0.0, "effect_b": p1 - p0, "same": all(abs(joint_a[k] - joint_b[k]) < 1e-12 for k in joint_a), "lower": lo, "upper": hi,
            "naive": p1 - p0}


# ----------------------------------------------------------------------------- Verdikte: (Art, Text)

def verdict_graph(a: Analysis) -> tuple[str, str]:
    s = a.settings
    x, y = C.NODE_LETTERS[s.x], C.NODE_LETTERS[s.y]
    if a.trivial:
        return "info", f"Es gibt keinen gerichteten Pfad von {x} nach {y}: Die Wirkung ist null, trivial bestimmbar."
    head = f"Die Wirkung von {x} auf {y} ist "
    if a.identified:
        door = KIND_TEXT[a.kind]
        return "success", head + "**bestimmbar** (ID-Algorithmus und Hedge-Aufzählung stimmen überein): " + door[0].lower() + door[1:] + "."
    if a.linear:
        return "warning", (head + "**ohne Modellannahme nicht bestimmbar** (ein Hedge existiert), im linearen Modell (generisch) aber schon" +
                           (f" (Instrument {names_of(a.methods['instruments'])})." if a.methods["instruments"] else ", wenn auch nicht durch ein einzelnes Instrument."))
    return "error", head + "**nicht bestimmbar, auch nicht im linearen Modell**: Es gibt ein Paar zweier Welten mit denselben Daten und verschiedener Wirkung."


def verdict_exhaustive(res3: dict, res4: dict) -> tuple[str, str]:
    z = res4["by_bi"]
    return "info", (f"Bei vier Knoten sind {de(100 * res4['identified'] / res4['cases'], 1)} % der {res4['cases']} Fälle ohne Modellannahme bestimmbar, im linearen Modell {de(100 * res4['linear'] / res4['cases'], 1)} %. "
                    f"Ohne verborgene Ursache sind es {de(100 * z[0]['identified'] / z[0]['cases'], 0)} %, mit einer {de(100 * z[1]['identified'] / z[1]['cases'], 0)} %, mit drei {de(100 * z[3]['identified'] / z[3]['cases'], 0)} %, "
                    f"mit sechs {de(100 * z[6]['identified'] / z[6]['cases'], 0)} %. Der ID-Algorithmus und die Hedge-Aufzählung widersprechen sich in {res3['mismatch'] + res4['mismatch']} von {res3['cases'] + res4['cases']} Fällen.")


def verdict_kinds(res4: dict) -> tuple[str, str]:
    k = res4["kinds"]
    ident = res4["identified"]
    return "info", (f"Von {ident} bestimmbaren Fällen löst eine Backdoor-Menge {k.get('backdoor', 0)}, die Frontdoor zusätzlich {k.get('frontdoor', 0)}; "
                    f"{k.get('napkin', 0)} ({de(100 * k.get('napkin', 0) / ident, 1)} %) brauchen unter den drei Türen den ID-Algorithmus. Nur im linearen Modell bestimmbar sind {k.get('linear_iv', 0) + k.get('linear_other', 0)} Fälle, "
                    f"davon {k.get('linear_iv', 0)} durch ein Instrument.")


def verdict_random(rows: list) -> tuple[str, str]:
    return "info", (f"Bei {rows[0]['hidden']} verborgenen Ursachen sind {de(100 * rows[0]['share'], 0)} % der zufälligen Graphen bestimmbar, bei {rows[1]['hidden']} {de(100 * rows[1]['share'], 0)} %, "
                    f"bei {rows[4]['hidden']} {de(100 * rows[4]['share'], 0)} %, bei {rows[-1]['hidden']} nur noch {de(100 * rows[-1]['share'], 0)} %.")


def verdict_worlds(w: dict) -> tuple[str, str]:
    return "info", (f"Beide Welten erzeugen dieselben Daten; die Wirkung ist in der einen {de(w['effect_a'], 2)}, in der anderen {de(w['effect_b'], 2)}. Ohne jede Annahme liegt sie nur in "
                    f"[{de(w['lower'], 2)}; {de(w['upper'], 2)}]: eine Breite von {de(w['upper'] - w['lower'], 2)}.")
