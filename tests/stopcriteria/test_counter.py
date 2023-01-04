import pytest

from freneticlib.executors.outcome import Outcome
from freneticlib.stopcriteria.counter import CountingStop


class TestCountingStop(object):
    def test_counter_complete(self):
        n_random = 5
        n_total = 10
        stop = CountingStop(n_total=n_total, n_random=n_random)
        # check initial conditions
        assert not stop.is_over
        assert stop.is_random_phase

        # execute 5 tests and make sure that it's still random
        for _ in range(n_random):
            assert stop.is_random_phase
            assert not stop.is_over
            stop.execute_test({"outcome": Outcome.PASS})

        # execute until it's over
        for _ in range(n_total - n_random):
            assert not stop.is_random_phase
            assert not stop.is_over
            stop.execute_test({"outcome": Outcome.FAIL})

        # what if we do more?
        for _ in range(5):
            assert not stop.is_random_phase
            assert stop.is_over
            stop.execute_test({"outcome": Outcome.PASS})

    @pytest.mark.parametrize("exec_count", [None, 0, 1, 4])
    def test_is_over_returns_False(self, exec_count):
        stop = CountingStop(n_total=5, n_random=5)
        if exec_count is not None:
            stop.exec_count = exec_count
        assert not stop.is_over

    @pytest.mark.parametrize("exec_count", [5, 6, 10, 100])
    def test_is_over_returns_True(self, exec_count):
        stop = CountingStop(n_total=5, n_random=5)
        if exec_count is not None:
            stop.exec_count = exec_count
        assert stop.is_over

    @pytest.mark.parametrize("exec_count", [None, 0, 1, 4])
    def test_is_random_phase_returns_False(self, exec_count):
        stop = CountingStop(n_total=5, n_random=5)
        if exec_count is not None:
            stop.exec_count = exec_count
        assert stop.is_random_phase

    @pytest.mark.parametrize("exec_count", [5, 6, 10, 100])
    def test_is_random_phase_returns_True(self, exec_count):
        stop = CountingStop(n_total=5, n_random=5)
        if exec_count is not None:
            stop.exec_count = exec_count
        assert not stop.is_random_phase

    @pytest.mark.parametrize("exec_count,expected", [(0, 1), (1, 2), (10, 11)])
    def test_execute_test(self, exec_count, expected):
        stop = CountingStop(n_total=5, n_random=5)
        if exec_count is not None:
            stop.exec_count = exec_count
        stop.execute_test({"outcome": Outcome.PASS})
        assert stop.exec_count == expected

    def test_random_higher_than_total(self):
        stop = CountingStop(n_total=5, n_random=10)
        for _ in range(6):
            stop.execute_test({"outcome": Outcome.FAIL})
        assert stop.is_over
        assert stop.is_random_phase
