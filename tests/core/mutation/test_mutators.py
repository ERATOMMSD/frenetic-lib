from unittest.mock import MagicMock

import numpy as np
import pytest

from freneticlib.core.mutation.mutators import FreneticMutator
from freneticlib.executors.outcome import Outcome
from freneticlib.utils.random import seeded_rng


DUMMY_TEST = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


class TestMutation(object):
    def test_value_alteration(self):
        test = np.random.random((1, 2))
        while len(test) < 10:
            test = np.append(test, np.random.random((1, 2)), axis=0)


class TestFreneticMutator(object):

    def test_get_mutated_tests__PASS_calls_mutator(self):
        mutator = FreneticMutator(
            mutation_operators=None,
            exploitation_operators=None,
        )
        mutator.mutator = MagicMock(name="mutator")
        mutator.exploiter = MagicMock(name="exploiter")

        mutator.mutator.return_value = []
        mutator._perform_modifications = MagicMock(name="_perform_modifications")

        mutants = mutator(representation=None, parent={"acceleration": 0.15, "break": 0.0, "velocity": 22, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST})

        assert mutator.mutator.called
        assert not mutator.exploiter.called

    def test_get_mutated_tests__FAIL_calls_exploiter(self):
        mutator = FreneticMutator(
            mutation_operators=None,
            exploitation_operators=None,
        )
        mutator.mutator = MagicMock(name="mutator")
        mutator.exploiter = MagicMock(name="exploiter")

        mutator.exploiter.return_value = []

        mutator._perform_modifications = MagicMock(name="_perform_modifications")
        mutants = mutator(representation=None, parent={"acceleration": 0.14, "break": 0.0, "velocity": 23, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST})

        assert mutator.exploiter.called
        assert not mutator.mutator.called
