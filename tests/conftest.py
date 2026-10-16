"""Gemeinsame Fixtures: die Mini-Graphen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b), und die einmal berechneten Aufzählungen aller Graphen."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def graph(directed=(), hidden=(), x=0, y=1, n=4):
    """(n, D, Bi, x, y) mit Mengen von Paaren (i, j), i < j."""
    return n, frozenset(directed), frozenset(hidden), x, y


@pytest.fixture
def bow():
    """Bow-Arc: A -> B, A <-> B, x = A, y = B. Eine einzige C-Komponente {A, B}: Zeile 5(a) des ID, nicht bestimmbar. Hedge F = {A, B} mit A -> B, F' = {B}, Wurzel {B}."""
    return graph([(0, 1)], [(0, 1)], 0, 1)


@pytest.fixture
def backdoor():
    """A -> B, A -> C, B -> C ohne verborgene Ursache, x = B, y = C: bestimmbar, Backdoor-Menge {A}."""
    return graph([(0, 1), (0, 2), (1, 2)], [], 1, 2)


@pytest.fixture
def frontdoor():
    """A -> B -> C mit A <-> C, x = A, y = C: bestimmbar, Frontdoor-Menge {B}."""
    return graph([(0, 1), (1, 2)], [(0, 2)], 0, 2)


@pytest.fixture
def instrument():
    """A -> B -> C mit B <-> C, x = B, y = C: ohne Annahme nicht bestimmbar, linear bestimmbar, Instrument A."""
    return graph([(0, 1), (1, 2)], [(1, 2)], 1, 2)


@pytest.fixture
def napkin():
    """A -> B -> C -> D mit A <-> C und A <-> D, x = C, y = D: bestimmbar, ohne Backdoor-Menge, Frontdoor-Menge und Instrument."""
    return graph([(0, 1), (1, 2), (2, 3)], [(0, 2), (0, 3)], 2, 3)


@pytest.fixture(scope="session")
def exh3():
    import idf_evaluation as ev

    return ev.exhaustive(3)


@pytest.fixture(scope="session")
def exh4():
    import idf_evaluation as ev

    return ev.exhaustive(4)
