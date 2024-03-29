from unittest.mock import MagicMock

import pandas as pd
import pytest

from freneticlib.core.core import FreneticCore
from freneticlib.core.mutation.mutators import FreneticMutator
from freneticlib.core.objective import MaxObjective
from freneticlib.executors.outcome import Outcome


class TestFreneticCore_AskTell(object):
    def test_ask_random(self):
        test_value = [1, 2, 3]
        representation = MagicMock(name="representation")
        representation.generate.return_value = test_value
        core = FreneticCore(representation=representation, objective=None)
        test = core.ask_random()

        assert representation.generate.called
        assert test["test"] == [1, 2, 3]
        assert test["generation"] == 0
        assert test["visited"] == 0
        assert test["method"] == "random"

    def test_ask__no_mutated_tests__calls_ask_random(self):
        core = FreneticCore(representation=None, objective=None)
        core.get_mutated_tests = MagicMock(name="get_mutated_tests", return_value=[])

        random_test = dict(test=[1, 2, 3], method="random", visited=0, generation=0)
        core.ask_random = MagicMock(name="ask_random", return_value=random_test)

        core.get_crossover_tests = MagicMock(name="get_crossover_tests")

        test_dict = core.ask()

        assert core.get_mutated_tests.called
        assert core.ask_random.called
        assert not core.get_crossover_tests.called
        assert test_dict == random_test

    def test_ask__has_mutated_tests__no_call_to_ask_random(self):
        core = FreneticCore(representation=None, objective=None)

        tests = [dict(test=[1, 2, 3]), dict(test=(11, 12, 13))]
        core.get_mutated_tests = MagicMock(name="get_mutated_tests", return_value=tests)
        core.ask_random = MagicMock(name="ask_random")
        core.get_crossover_tests = MagicMock(name="get_crossover_tests")

        test1 = core.ask()
        test2 = core.ask()

        assert core.get_mutated_tests.call_count == 1
        assert not core.ask_random.called
        assert not core.get_crossover_tests.called

        assert test1 == tests[0]
        assert test2 == tests[1]

    def test_ask__has_mutated_tests__breaks_mutated_after_fail(self):
        core = FreneticCore(representation=None, objective=None)

        tests = [dict(test=[1, 2, 3], outcome=Outcome.PASS), dict(test=(11, 12, 13), outcome=Outcome.FAIL)]
        core.get_mutated_tests = MagicMock(name="get_mutated_tests", return_value=tests)
        core.ask_random = MagicMock(name="ask_random")
        core.get_crossover_tests = MagicMock(name="get_crossover_tests", return_value=["CROSSOVER_TEST"])

        test1 = core.ask()
        test2 = core.ask()  # this is the FAIL one.
        test3 = core.ask()

        assert core.get_mutated_tests.call_count == 1
        assert not core.ask_random.called
        assert core.get_crossover_tests.called

        assert test1 == tests[0]
        assert test2 == tests[1]
        assert test3 == "CROSSOVER_TEST"

    def test_ask__has_mutated_tests_and_crossover_tests__no_call_to_ask_random(self):
        core = FreneticCore(representation=None, objective=None)

        tests = [dict(test=[1, 2, 3]), dict(test=(11, 12, 13))]
        core.get_mutated_tests = MagicMock(name="get_mutated_tests", return_value=[tests[0]])
        core.ask_random = MagicMock(name="ask_random")
        core.get_crossover_tests = MagicMock(name="get_crossover_tests", return_value=[tests[1]])

        test1 = core.ask()
        test2 = core.ask()

        assert core.get_mutated_tests.call_count == 1
        assert not core.ask_random.called
        assert core.get_crossover_tests.call_count == 1

        assert test1 == tests[0]
        assert test2 == tests[1]

    def test_tell_insert(self):
        core = FreneticCore(representation=None, objective=None)
        core.tell(record={"acceleration": 0.15, "break": 0.0, "velocity": 22})
        assert len(core.history) == 1

    def test_tell_insert_twice(self):
        core = FreneticCore(representation=None, objective=None)
        core.tell(record={"acceleration": 0.15, "break": 0.0, "velocity": 22})
        core.tell(record={"acceleration": 0.14, "break": 0.0, "velocity": 23})
        assert len(core.history) == 2

    def test_get_best_parent_None_df(self):
        core = FreneticCore(representation=None, objective=None)
        assert core._get_best_mutation_parent() is None

    def test_get_best_parent_empty_df(self):
        core = FreneticCore(representation=None, objective=None)
        core.history = pd.DataFrame(columns=["acceleration", "break", "velocity"])
        assert core._get_best_mutation_parent() is None


@pytest.fixture
def core():
    return FreneticCore(
        representation=None,
        objective=MaxObjective("acceleration", per_simulation_aggregator="max"),
        mutator=FreneticMutator(None),
    )


DUMMY_TEST = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


class TestFreneticCore_Mutation(object):
    def test_get_best_parent(self, core):
        core.min_length_to_mutate = 3
        records = [
            {"acceleration": 0.15, "break": 0.0, "velocity": 22, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.14, "break": 0.0, "velocity": 23, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
        ]
        for rec in records:
            core.tell(rec)

        assert core._get_best_mutation_parent().to_dict() == records[0]

    def test_get_best_parent_two_candidates(self, core):
        records = [
            {"acceleration": 0.15, "break": 0.0, "velocity": 22, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.14, "break": 0.0, "velocity": 23, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.14, "break": 0.0, "velocity": 25, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.15, "break": 0.0, "velocity": 20, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
        ]
        for rec in records:
            core.tell(rec)

        assert core._get_best_mutation_parent().to_dict() == records[0]

    def test_get_best_parent_all_too_short(self, core):
        core.mutator.min_length_to_mutate = 10
        records = [
            {
                "acceleration": 0.15,
                "break": 0.0,
                "velocity": 22,
                "outcome": Outcome.PASS,
                "visited": 0,
                "test": [1, 2, 3, 4, 5],
            },
            {
                "acceleration": 0.14,
                "break": 0.0,
                "velocity": 23,
                "outcome": Outcome.FAIL,
                "visited": 0,
                "test": [1, 2, 3, 4, 5],
            },
            {
                "acceleration": 0.14,
                "break": 0.0,
                "velocity": 25,
                "outcome": Outcome.FAIL,
                "visited": 0,
                "test": [1, 2, 3, 4, 5],
            },
            {
                "acceleration": 0.15,
                "break": 0.0,
                "velocity": 20,
                "outcome": Outcome.PASS,
                "visited": 0,
                "test": [1, 2, 3, 4, 5],
            },
        ]
        for rec in records:
            core.tell(rec)

        assert core._get_best_mutation_parent() is None

    def test_get_best_parent_best_too_short(self, core):
        core.mutator.min_length_to_mutate = 7
        records = [
            {
                "acceleration": 0.15,
                "break": 0.0,
                "velocity": 22,
                "outcome": Outcome.PASS,
                "visited": 0,
                "test": DUMMY_TEST[:8],
            },
            {
                "acceleration": 0.14,
                "break": 0.0,
                "velocity": 23,
                "outcome": Outcome.FAIL,
                "visited": 0,
                "test": DUMMY_TEST[:9],
            },
            {
                "acceleration": 0.13,
                "break": 0.0,
                "velocity": 25,
                "outcome": Outcome.FAIL,
                "visited": 0,
                "test": DUMMY_TEST[:11],
            },
            {
                "acceleration": 0.15,
                "break": 0.0,
                "velocity": 20,
                "outcome": Outcome.PASS,
                "visited": 0,
                "test": DUMMY_TEST[:8],
            },
        ]
        for rec in records:
            core.tell(rec)

        assert core._get_best_mutation_parent().to_dict() == records[2]

    def test_get_best_parent_with_threshold(self, core):
        core.objective.threshold = 0.2
        core.mutator.min_length_to_mutate = 5
        records = [
            {"acceleration": 0.15, "break": 0.0, "velocity": 22, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.14, "break": 0.0, "velocity": 23, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.13, "break": 0.0, "velocity": 25, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.15, "break": 0.0, "velocity": 20, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
        ]
        for rec in records:
            core.tell(rec)

        assert core._get_best_mutation_parent() is None

    def test_get_mutated_tests__no_parent_no_tests(self):
        core = FreneticCore(
            representation=None, objective=None, mutator=MagicMock(name="mutator")
        )
        core._get_best_mutation_parent = MagicMock(name="get_best_parent", return_value=None)
        core._perform_modifications = MagicMock(name="_perform_modifications")

        assert core.get_mutated_tests() == []
        assert not core.mutator.called


class TestFreneticCore_Crossover(object):
    def test_get_crossover_tests__no_crossover(self):
        core = FreneticCore(representation=None, objective=None, crossover=None)
        core._select_crossover_candidates = MagicMock(name="_select_crossover_candidates")

        assert core.get_crossover_tests() == []
        assert not core._select_crossover_candidates.called

    def test_get_crossover_tests__no_crossover_candidates(self):
        core = FreneticCore(representation=None, objective=None, crossover=MagicMock(name="crossover"))
        core._select_crossover_candidates = MagicMock(name="_select_crossover_candidates", return_value=[])

        assert core.get_crossover_tests() == []
        assert core._select_crossover_candidates.called
        assert not core.crossover.called

    def test_get_crossover_tests__no_generated_children(self):
        core = FreneticCore(representation=None, objective=None, crossover=MagicMock(name="crossover"))
        core._select_crossover_candidates = MagicMock(
            name="_select_crossover_candidates", return_value=[1, 2, 3]
        )  # just a non-empty list
        core.crossover.return_value = []  # return empty list

        assert core.get_crossover_tests() == []
        assert core._select_crossover_candidates.called
        assert core.crossover.called

    def test_get_crossover_tests__with_generated_children(self):
        core = FreneticCore(representation=None, objective=None, crossover=MagicMock(name="crossover"))
        core._select_crossover_candidates = MagicMock(
            name="_select_crossover_candidates", return_value=[1, 2, 3]
        )  # just a non-empty list

        #  fill df
        for rec in [
            {"acceleration": 0.15, "break": 0.0, "velocity": 22, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.14, "break": 0.0, "velocity": 23, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.13, "break": 0.0, "velocity": 25, "outcome": Outcome.FAIL, "visited": 0, "test": DUMMY_TEST},
            {"acceleration": 0.15, "break": 0.0, "velocity": 20, "outcome": Outcome.PASS, "visited": 0, "test": DUMMY_TEST},
        ]:
            core.tell(rec)

        # create a dummy child with parent-info
        test = [12, 13, 14, 15]
        method = "test method"
        info = dict(parent_1_index=1, parent_2_index=3)
        core.crossover.return_value = [(test, method, info)]  # return  empty list

        assert core.get_crossover_tests() == [dict(test=test, method=method, **info)]

        #  assert that the parent's indices were increased
        assert core.history.loc[1].visited == 1
        assert core.history.loc[3].visited == 1

        assert core._select_crossover_candidates.called
        assert core.crossover.called

    # TODO: Test _select_crossover_candidates
