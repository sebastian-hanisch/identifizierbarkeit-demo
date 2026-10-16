"""Lineare Bestimmbarkeit: Kovarianz und Wirkung von Hand, Rang der Jacobi-Matrix, ein explizites Paar von Modellen mit gleicher Kovarianz und verschiedener Wirkung."""

import itertools

import numpy as np
import pytest

import idf_linear as L


def test_covariance_and_effect_by_hand():
    """A -> B ohne verborgene Ursache: θ = (λ, ω_AA, ω_BB); Σ = [[ω_A, λ ω_A], [λ ω_A, λ² ω_A + ω_B]]."""
    theta = np.array([0.7, 2.0, 1.5])
    cov = L.covariance(theta, 2, [(0, 1)], [])
    assert cov == pytest.approx(np.array([[2.0, 1.4], [1.4, 0.49 * 2.0 + 1.5]])) and L.total_effect(theta, 2, [(0, 1)], [], 0, 1) == pytest.approx(0.7)


def test_covariance_with_a_hidden_cause_by_hand():
    """Bow-Arc: θ = (λ, ω_AB, ω_AA, ω_BB); Σ_AB = λ ω_AA + ω_AB, Σ_BB = λ² ω_AA + 2 λ ω_AB + ω_BB."""
    theta = np.array([0.7, 0.3, 2.0, 1.5])
    cov = L.covariance(theta, 2, [(0, 1)], [(0, 1)])
    assert cov[0, 0] == pytest.approx(2.0) and cov[0, 1] == pytest.approx(0.7 * 2.0 + 0.3) and cov[1, 1] == pytest.approx(0.49 * 2.0 + 2 * 0.7 * 0.3 + 1.5)


def test_total_effect_is_the_sum_of_path_products():
    theta = np.array([0.5, 0.4, 0.3] + [1.0] * 3)                 # A -> B 0,5; A -> C 0,4; B -> C 0,3
    assert L.total_effect(theta, 3, [(0, 1), (0, 2), (1, 2)], [], 0, 2) == pytest.approx(0.4 + 0.5 * 0.3) and L.total_effect(theta, 3, [(0, 1), (0, 2), (1, 2)], [], 2, 0) == pytest.approx(0.0)


def test_random_parameters_are_deterministic_and_in_range():
    D, Bi = [(0, 1), (1, 2)], [(1, 2)]
    t = L.random_parameters(3, D, Bi)
    assert (t == L.random_parameters(3, D, Bi)).all() and (t != L.random_parameters(3, D, Bi, seed=5)).any() and len(t) == 2 + 1 + 3
    assert all(0.5 <= abs(v) <= 1.2 for v in t[:2]) and 0.2 <= abs(t[2]) <= 0.5 and all(1.5 <= v <= 2.5 for v in t[3:])


def test_jacobian_against_the_closed_form_of_the_two_node_chain():
    theta = np.array([0.7, 2.0, 1.5])                              # Σ-Einträge (AA, AB, BB) = (ω_A, λ ω_A, λ² ω_A + ω_B)
    jac = L.jacobian(theta, 2, [(0, 1)], [])
    expected = np.array([[0.0, 1.0, 0.0], [2.0, 0.7, 0.0], [2 * 0.7 * 2.0, 0.49, 1.0]])         # Zeilen: Σ_AA, Σ_AB, Σ_BB; Spalten: λ, ω_A, ω_B
    assert jac == pytest.approx(expected, abs=1e-6)


def test_rank_and_identification_of_the_named_graphs(bow, backdoor, frontdoor, instrument, napkin):
    out = {}
    for name, g in (("bow", bow), ("backdoor", backdoor), ("frontdoor", frontdoor), ("instrument", instrument), ("napkin", napkin)):
        n, D, Bi, x, y = g
        lin, rank, m = L.linear_identified(n, D, Bi, [(x, y)])
        out[name] = (lin[(x, y)], rank, m)
    assert out["bow"] == (False, 5, 6) and out["instrument"][0] is True and out["backdoor"][0] is True and out["frontdoor"][0] is True and out["napkin"][0] is True


def test_result_does_not_depend_on_the_parameter_point():
    for g in itertools.islice(((3, {(0, 1), (1, 2)}, {(1, 2)}, 1, 2), (3, {(0, 1), (1, 2)}, {(0, 2)}, 0, 2), (3, {(0, 1)}, {(0, 1)}, 0, 1), (4, {(0, 1), (1, 2), (2, 3)}, {(0, 2), (0, 3)}, 2, 3)), 4):
        n, D, Bi, x, y = g
        results = {L.linear_identified(n, D, Bi, [(x, y)], seed=s)[0][(x, y)] for s in (1, 2, 3, 4)}
        assert len(results) == 1


def test_bow_arc_has_two_linear_models_with_the_same_covariance_and_different_effects():
    """Zweites Modell mit λ' = λ + δ: ω_AB' = ω_AB − δ ω_AA gleicht Σ_AB aus, ω_BB' gleicht Σ_BB aus; die Wirkung ist λ bzw. λ'."""
    lam, om_ab, om_aa, om_bb, delta = 0.7, 0.3, 2.0, 1.5, 0.4
    t1 = np.array([lam, om_ab, om_aa, om_bb])
    lam2, om_ab2 = lam + delta, om_ab - delta * om_aa
    om_bb2 = om_bb + lam ** 2 * om_aa + 2 * lam * om_ab - lam2 ** 2 * om_aa - 2 * lam2 * om_ab2
    t2 = np.array([lam2, om_ab2, om_aa, om_bb2])
    D, Bi = [(0, 1)], [(0, 1)]
    assert L.covariance(t1, 2, D, Bi) == pytest.approx(L.covariance(t2, 2, D, Bi), abs=1e-12)
    assert L.total_effect(t1, 2, D, Bi, 0, 1) != pytest.approx(L.total_effect(t2, 2, D, Bi, 0, 1)) and abs(L.total_effect(t2, 2, D, Bi, 0, 1) - L.total_effect(t1, 2, D, Bi, 0, 1)) == pytest.approx(delta)


def test_instrument_graph_has_no_such_pair():
    """Im Instrument-Graphen (A -> B -> C, B <-> C) legt die Kovarianz die Wirkung fest: β = Σ_AC / Σ_AB für alle Parameter."""
    D, Bi = [(0, 1), (1, 2)], [(1, 2)]
    for seed in (1, 2, 3):
        t = L.random_parameters(3, D, Bi, seed)
        cov = L.covariance(t, 3, D, Bi)
        assert cov[0, 2] / cov[0, 1] == pytest.approx(L.total_effect(t, 3, D, Bi, 1, 2))


def test_direction_without_a_path_has_zero_gradient_and_counts_as_identified():
    lin, _, _ = L.linear_identified(3, {(0, 1)}, set(), [(1, 0), (0, 2)])
    assert lin[(1, 0)] is True and lin[(0, 2)] is True
