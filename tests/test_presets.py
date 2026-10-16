"""Presets, Masken, Permalink-Raster und Konstanten."""

import pytest

import idf_constants as C
import idf_evaluation as ev
import idf_presets as P


def test_masks_round_trip_and_follow_the_pair_order():
    assert C.PAIRS == ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)) and C.MASK_MAX == 63
    assert C.mask_of({(0, 1)}) == 1 and C.mask_of({(2, 3)}) == 32 and C.mask_of({(0, 1), (1, 2)}) == 1 + 8 and C.mask_of(set()) == 0
    for m in range(64):
        assert C.mask_of(C.edges_of(m)) == m
    assert C.edges_of(0b101) == frozenset({(0, 1), (0, 3)})


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, p in C.PRESETS.items():
        assert set(p) == {"d", "b", "x", "y"} and C.PRESET_HELP[name], name
        assert 0 <= p["d"] <= C.MASK_MAX and 0 <= p["b"] <= C.MASK_MAX and p["x"] != p["y"] and 0 <= p["x"] < C.N_NODES and 0 <= p["y"] < C.N_NODES, name


def test_first_preset_is_the_default_setting():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings() == ev.Settings(**first) and P.DEFAULT_PRESET is first and next(iter(C.PRESETS)) == "Instrument (Voreinstellung)"


def test_presets_are_different_and_each_has_a_path_from_x_to_y():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)
    for name, p in C.PRESETS.items():
        assert not ev.analyse(ev.Settings(**p)).trivial, name


def test_presets_cover_every_kind_of_verdict():
    kinds = {ev.analyse(ev.Settings(**p)).kind for p in C.PRESETS.values()}
    assert kinds == {"linear_iv", "none", "backdoor", "frontdoor", "napkin"}


def test_state_keys_are_unique_and_cover_all_pairs():
    assert len(set(P.DIR_KEYS.values()) | set(P.BI_KEYS.values())) == 2 * len(C.PAIRS) and set(P.DIR_KEYS) == set(C.PAIRS) == set(P.BI_KEYS)


def test_clamp():
    assert P._clamped(70, 0, 63) == 63 and P._clamped(-4, 0, 63) == 0 and P._clamped(5, 0, 63) == 5


def test_constants_are_consistent():
    assert len(C.NODE_LETTERS) == C.N_NODES == 4 and C.RANDOM_PER >= 500 and C.RANDOM_MAX_BI <= len(C.PAIRS) * 0 + 10 and C.RANDOM_NODES == 5
    assert 0 < C.WORLD_PX < 1 and 0 < C.WORLD_P0 < C.WORLD_P1 < 1
