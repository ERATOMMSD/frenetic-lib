import ast
import logging
from typing import Iterator

import pandas as pd

from freneticlib.core.objective import AbstractObjective
from freneticlib.executors.outcome import Outcome
from freneticlib.representations.abstract_generator import RoadGenerator

logger = logging.getLogger(__name__)


class FreneticCore(object):
    """The core module of frenetic-lib. It handles the representation"""

    def __init__(
        self,
        representation: RoadGenerator,
        objective: AbstractObjective,
        mutator=None,
        exploiter=None,
        crossover=None,
    ):
        self.representation = representation
        self.objective = objective

        self.mutator = mutator
        self.exploiter = exploiter
        self.crossover = crossover

        self.df = None

        # Warnings when operators are None
        self._warn_if_none(crossover, "crossover")
        self._warn_if_none(mutator, "mutator")
        self._warn_if_none(exploiter, "exploiter")

        self.crossover_max_visits = 10

    def _warn_if_none(self, var, name):
        if not var:
            logger.warning(f"No {name} operator was chosen.")

    def ask_random(self) -> dict:
        return dict(test=self.representation.generate(), method="random", visited=0, generation=0)

    def tell(self, record: dict):
        logger.debug("Tell:")  # {road} -> {result}")
        if self.df is None:
            self.df = pd.DataFrame([record])
        else:
            # self.df = self.df.append(record, ignore_index=True)
            self.df = pd.concat([self.df, pd.DataFrame([record])], ignore_index=True)

    def ask(self) -> Iterator[dict]:
        """This is actually a python generator, it will produce roads as long as we ask it.

        Specifically, it will first create a list of mutants based on the best known individual.
        Then, using the history and the mutants, it will create the crossover children and yield those.

        Yields:
            dict: A dictionary containing a road and additional information of the test.
        """
        while True:
            # First we mutate (or generate random)
            mutated_tests = self.get_mutated_tests()
            if len(mutated_tests) == 0:
                logger.debug("No mutations. Generating a random test.")
                yield self.ask_random()

            for idx, test in enumerate(mutated_tests):
                # stop mutating if one of the mutants already produced a failure
                if idx > 0 and "outcome" in mutated_tests[idx - 1] and mutated_tests[idx - 1]["outcome"] == Outcome.FAIL:
                    break  # break on first fail
                else:
                    yield test

            # then we crossover
            crossover_tests = self.get_crossover_tests()
            yield from crossover_tests

            # TODO: I don't understand this code here. Check with Ezequiel.
            # if self.crossover and 0 < self.crossover.frequency <= self.executed_count:
            #     logger.info('Entering recombination phase.')
            #     self.parents_recombination()
            #     self.executed_count = 0

            self.objective.recalculate_dynamic_threshold(self.df)

    def get_mutated_tests(self) -> list:
        """Returns a list of tests"""
        parent = self._get_best_mutation_parent()  # returns a row
        if parent is None:
            logger.warning("Couldn't find a good parent. Skipping.")
            return []

        # TODO: why isn't this in the filter?
        #  Shouldn't we get the best parent of min_length?
        # if len(parent.test.item()) < self.min_length_to_mutate:
        #     logger.debug("Best parent's test is too short.")
        #     return []

        logger.debug(f"Best unvisited parent for mutation is {parent.index[0]}")
        self.df.at[parent.name, "visited"] = 1

        if self.exploiter and parent.outcome == Outcome.FAIL:
            return self._perform_modifications(self.exploiter.get_all(), parent, stop_reproduction=True)
        elif self.mutator and parent.outcome == Outcome.PASS:
            return self._perform_modifications(self.mutator.get_all(), parent)
        else:
            logger.warning("No modification was applied because there is no exploiter nor mutator defined.")
            return []

    def _perform_modifications(self, functions, parent, stop_reproduction=False) -> list:
        if parent.test is None:
            return []

        test_info = self.get_parent_info(parent.name)
        test_info["visited"] = 1 if stop_reproduction else 0

        modified_tests = []
        for name, function in functions:
            try:
                modified_tests.append(dict(test=function(parent.test), method=name, **test_info))
            except Exception:
                logger.error(f"Error during modification of test {test_info} during function {name}", exc_info=True)

        return modified_tests

    def _get_best_mutation_parent(self) -> pd.Series:
        if self.df is None or len(self.df) <= 0:
            logger.warning("Empty history. Cannot get best parent.")
            return None

        assert self.objective.feature in self.df.columns, "Target feature is recorded in history records."

        # we take the best parent that hasn't been visited yet, whose feature is below/above the threshold
        selection = self._select_by_maxvisits_and_threshold(max_visits=0)
        if hasattr(self.mutator, "min_length"):  # filter by min_length, if needed
            selection = selection[selection.test.apply(len) >= self.mutator.min_length]
        return self.objective.get_best(selection)

    def _select_by_maxvisits_and_threshold(self, max_visits=0):
        pass_fail_filter = self.df.outcome.isin(
            [Outcome.PASS, Outcome.FAIL]
        )  # TODO: this is domain-specific and needs to be dropped
        max_visit_filter = self.df.visited <= max_visits
        return self.objective.filter_by_threshold(self.df[pass_fail_filter & max_visit_filter])

    def get_parent_info(self, p_index) -> dict:
        parent = self.df.iloc[p_index]
        return {
            "parent_1_index": p_index,
            "parent_1_outcome": parent["outcome"],
            "parent_1_" + self.objective.feature: parent[self.objective.feature],
            "generation": parent["generation"] + 1,
        }

    def get_crossover_tests(self) -> list:
        if self.crossover is None:
            logger.info("No crossover defined. Skipping.")
            return []

        # parents_recombination
        candidates = self._select_crossover_candidates()
        if len(candidates) > 0:
            child_tests = []
            for child, method, info in self.crossover.generate(candidates):
                self.df.at[info["parent_1_index"], "visited"] = self.df.iloc[info["parent_1_index"]]["visited"] + 1
                self.df.at[info["parent_2_index"], "visited"] = self.df.iloc[info["parent_2_index"]]["visited"] + 1
                child_tests.append(dict(test=child, method=method, **info))
            return child_tests
        else:
            logger.warning("No candidates for crossover.")
            return []

    def _select_crossover_candidates(self) -> list:
        if len(self.df) <= 0:
            logger.warning("Empty history. Cannot get best parent.")
            return []

        assert self.objective.feature in self.df.columns, "Target feature is recorded in history records."

        selection = self._select_by_maxvisits_and_threshold(self.crossover_max_visits)
        if len(selection) < self.crossover.min_size:
            logger.warning(
                "Couldn't select enough tests to generate crossover candidates. "
                + f"Select: {len(selection)}, Crossover min size: {self.crossover.min_size}"
            )
            return []

        candidates = []
        for index, candidate in selection.iterrows():
            test = candidate["test"]
            if type(test) == str:
                logger.warning("Test was stored as a string value in the data frame.")
                test = ast.literal_eval(test)
            candidates.append((test, self.get_parent_info(index)))

        return candidates
