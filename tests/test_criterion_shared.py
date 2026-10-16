"""Die wortgleich übernommenen Kriterien (Stück 9): Eingaben, Reihenfolge der Ergebnisse und Ausnahmen, soweit die Zuordnung dieses Stücks sich darauf stützt."""

import pytest

import ins_criterion as K


def test_instrument_check_rejects_equal_nodes(instrument):
    n, D, Bi, x, y = instrument
    parents = ((), (0,), (1,), ())
    for args in ((1, 1, 0), (1, 2, 1), (1, 2, 2)):
        with pytest.raises(ValueError):
            K.instrument_check(parents, *args)
    assert K.instrument_check(parents, 1, 2, 0)["relevant"] is True


def test_frontdoor_check_rejects_overlapping_nodes():
    parents = ((), (0,), (1,), (0, 2))
    for args in ((1, 1, (2,)), (1, 3, (1,)), (1, 3, (3,))):
        with pytest.raises(ValueError):
            K.frontdoor_check(parents, *args)


def test_instruments_are_listed_in_ascending_order():
    parents = ((), (), (), (0, 1, 2), (0, 3))                    # Z1 = 1 und Z2 = 2 beide -> x = 3 -> y = 4, U = 0 verborgen
    assert K.instruments(parents, 3, 4, [2, 1, 0]) == [1, 2]


def test_frontdoor_sets_are_listed_by_size_and_in_ascending_order():
    chain = ((), (0,), (1,), (2,), (0, 3))                       # U -> X -> M1 -> M2 -> Y mit U -> Y
    assert K.frontdoor_sets(chain, 1, 4, [3, 2]) == [(2,), (3,), (2, 3)]
