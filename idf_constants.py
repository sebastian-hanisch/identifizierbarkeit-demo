"""Konstanten: Knoten, Presets, feste Experimente und Farben."""

N_NODES = 4
NODE_LETTERS = ("A", "B", "C", "D")
PAIRS = tuple((i, j) for i in range(N_NODES) for j in range(i + 1, N_NODES))     # Bit k einer Maske gehört zum Paar PAIRS[k]
MASK_MAX = 2 ** len(PAIRS) - 1

# Experimente: feste Ströme (Seeds aus SEED_BASE), nie ein einzelner Seed als Befund.
SEED_BASE = 1000000
LINEAR_SEED = 20261016                                                            # Parameterwahl der linearen Prüfung (das Ergebnis ist generisch, nicht vom Seed abhängig)
RANDOM_NODES, RANDOM_P_DIR, RANDOM_PER = 5, 0.5, 800                              # Experiment 3: zufällige Graphen mit fünf Knoten
RANDOM_MAX_BI = 8

# Experiment 4: zwei Welten für den Bow-Arc (binär)
WORLD_PX = 0.5                                                                    # P(X = 1)
WORLD_P1, WORLD_P0 = 0.7, 0.3                                                     # P(Y = 1 | X = 1), P(Y = 1 | X = 0)

COLOR_TRUTH = "#D68A2E"
COLOR_GOOD = "#2F6B65"
COLOR_BAD = "#c0392b"
COLOR_NEUTRAL = "#8a8a8a"
COLOR_HIDDEN = "#cfcfcf"
COLOR_CONTROL = "#4c78a8"


def mask_of(edges) -> int:
    return sum(1 << k for k, e in enumerate(PAIRS) if e in edges)


def edges_of(mask: int) -> frozenset:
    return frozenset(e for k, e in enumerate(PAIRS) if mask >> k & 1)


def preset(directed=(), hidden=(), x=0, y=1) -> dict:
    return dict(d=mask_of(set(directed)), b=mask_of(set(hidden)), x=x, y=y)


PRESETS = {
    "Instrument (Voreinstellung)": preset(directed=[(0, 1), (1, 2)], hidden=[(1, 2)], x=1, y=2),
    "Bow-Arc": preset(directed=[(0, 1)], hidden=[(0, 1)], x=0, y=1),
    "Backdoor": preset(directed=[(0, 1), (0, 2), (1, 2)], x=1, y=2),
    "Frontdoor": preset(directed=[(0, 1), (1, 2)], hidden=[(0, 2)], x=0, y=2),
    "Napkin": preset(directed=[(0, 1), (1, 2), (2, 3)], hidden=[(0, 2), (0, 3)], x=2, y=3),
    "Viele verborgene Ursachen": preset(directed=[(0, 1), (1, 2), (2, 3)], hidden=[(0, 1), (1, 2), (2, 3), (0, 3)], x=1, y=3),
}
PRESET_HELP = {
    "Instrument (Voreinstellung)": "A → B → C mit einer verborgenen Ursache von B und C: B wirkt auf C, aber beide haben eine gemeinsame verborgene Ursache. Ohne Annahme über die Form ist die Wirkung nicht bestimmbar; im linearen Modell mit A als Instrument schon.",
    "Bow-Arc": "A → B mit einer verborgenen gemeinsamen Ursache von A und B: der kleinste nicht bestimmbare Fall. Zwei Welten mit denselben Daten und verschiedener Wirkung (Experiment 4).",
    "Backdoor": "A wirkt auf B und C, B auf C; alles beobachtet. Die Backdoor-Menge {A} genügt: bestimmbar.",
    "Frontdoor": "A → B → C mit einer verborgenen gemeinsamen Ursache von A und C: die Wirkung läuft über den beobachteten Mediator B; bestimmbar (Stück 8).",
    "Napkin": "Vier Knoten, bestimmbar, aber ohne Backdoor-, Frontdoor-Menge und ohne Instrument: nur der ID-Algorithmus findet den Weg.",
    "Viele verborgene Ursachen": "Vier verborgene gemeinsame Ursachen entlang einer Kette: x und y hängen über Umwege zusammen, die sich nicht blockieren lassen.",
}
