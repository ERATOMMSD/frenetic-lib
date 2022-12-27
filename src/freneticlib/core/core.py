import ast
import logging
from typing import Dict, Iterator, List

import pandas as pd

from freneticlib.core.mutation import abstract_operators
from freneticlib.core.objective import Objective
from freneticlib.executors.outcome import Outcome
from freneticlib.representations.abstract_representation import RoadRepresentation

logger = logging.getLogger(__name__)


class FreneticCore(object):
    """The core module of frenetic-lib. It handles the representation"""

    history: pd.DataFrame = None
    """Stores the history including road, execution outcome and parent info."""

    def __init__(
        self,
        representation: RoadRepresentation,
        objective: Objective,
        mutator=None,
        exploiter=None,
        crossover=None,
    ):
        self._mutant_generator = None
        self.representation = representation
        self.objective = objective

        self.mutator = mutator
        self.exploiter = exploiter
        self.crossover = crossover

        # Warnings when operators are None
        self._warn_if_none(crossover, "crossover")
        self._warn_if_none(mutator, "mutator")
        self._warn_if_none(exploiter, "exploiter")

        self.crossover_max_visits = 10

    def _warn_if_none(self, var, name):
        if not var:
            logger.warning(f"No {name} operator was chosen.")

    def ask_random(self) -> Dict:
        test = self.representation.generate()
        assert self.representation.is_valid(test), "The newly generated test should be valid."
        return dict(test=test, method="random", visited=0, generation=0)

    def tell(self, record: Dict):
        logger.debug(f"Tell: {record}")  # {road} -> {result}")
        if self.history is None:
            self.history = pd.DataFrame([record])
        else:
            # self.df = self.df.append(record, ignore_index=True)
            self.history = pd.concat([self.history, pd.DataFrame([record])], ignore_index=True)

    def ask(self) -> Dict:
        if self._mutant_generator is None:
            self._mutant_generator = self._ask()
        return next(self._mutant_generator)

    def _ask(self) -> Iterator[Dict]:
        """This is actually a generator, it will produce roads as long as we ask it.

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

            self.objective.recalculate_dynamic_threshold(self.history)

    def get_mutated_tests(self) -> List:
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
        self.history.at[parent.name, "visited"] = 1

        if self.exploiter and parent.outcome == Outcome.FAIL:
            return self._perform_modifications(self.exploiter, parent, stop_reproduction=True)
        elif self.mutator and parent.outcome == Outcome.PASS:
            return self._perform_modifications(self.mutator, parent)
        else:
            logger.warning("No modification was applied because there is neither an exploiter nor a mutator defined.")
            return []

    def _perform_modifications(self, mutator: abstract_operators.AbstractMutator, parent, stop_reproduction=False) -> list:
        if parent.test is None:
            return []

        test_info = self.get_parent_info(parent.name)
        test_info["visited"] = 1 if stop_reproduction else 0

        modified_tests = []
        for operator in mutator.get_all():
            try:
                mutated_test = operator(self.representation, parent.test)
                if not self.representation.is_valid(mutated_test):
                    logger.debug(f"Mutation operator {str(operator)} produced an invalid test. Attempting to fix it.")
                    mutated_test = self.representation.fix(mutated_test)
                    if not self.representation.is_valid(mutated_test):
                        logger.warning("Couldn't fix the test.")
                        import pdb; pdb.set_trace()
                        continue
                modified_tests.append(dict(test=mutated_test, method=str(operator), **test_info))

            except Exception:
                logger.error(f"Error during modification of test {test_info} during function {str(operator)}", exc_info=True)

        return modified_tests

    def _get_best_mutation_parent(self) -> pd.Series:
        if self.history is None or len(self.history) <= 0:
            logger.warning("Empty history. Cannot get best parent.")
            return None

        assert self.objective.feature in self.history.columns, "Target feature is recorded in history records."

        # we take the best parent that hasn't been visited yet, whose feature is below/above the threshold
        selection = self._select_by_maxvisits_and_threshold(max_visits=0)

        # only use those parents where all mutation operators are applicable
        operator_filter = selection.apply(lambda x: True, axis=1)
        # note, this weird loop form is required, because pandas removes columns when selecting on an empty selection...
        for op in self.mutator.get_all():
            operator_filter = operator_filter & selection.test.apply(op.is_applicable)

        selection = selection[operator_filter]

        return self.objective.get_best(selection)

    def _select_by_maxvisits_and_threshold(self, max_visits=0):
        pass_fail_filter = self.history.outcome.isin(
            [Outcome.PASS, Outcome.FAIL]
        )  # TODO: this is domain-specific and needs to be dropped
        max_visit_filter = self.history.visited <= max_visits
        return self.objective.filter_by_threshold(self.history[pass_fail_filter & max_visit_filter])

    def get_parent_info(self, p_index) -> Dict:
        parent = self.history.iloc[p_index]
        return {
            "parent_1_index": p_index,
            "parent_1_outcome": parent["outcome"],
            "parent_1_" + self.objective.feature: parent[self.objective.feature],
            "generation": parent["generation"] + 1,
        }

    def get_crossover_tests(self) -> List:
        if self.crossover is None:
            logger.info("No crossover defined. Skipping.")
            return []

        # parents_recombination
        candidates = self._select_crossover_candidates()
        if len(candidates) <= 0:
            logger.warning("No candidates for crossover.")
            return []

        child_tests = []
        for child, method, info in self.crossover(self.representation, candidates):
            self.history.at[info["parent_1_index"], "visited"] = self.history.iloc[info["parent_1_index"]]["visited"] + 1
            self.history.at[info["parent_2_index"], "visited"] = self.history.iloc[info["parent_2_index"]]["visited"] + 1
            child_tests.append(dict(test=child, method=method, **info))
        return child_tests

    def _select_crossover_candidates(self) -> List:
        if len(self.history) <= 0:
            logger.warning("Empty history. Cannot get best parent.")
            return []

        assert self.objective.feature in self.history.columns, "Target feature is recorded in history records."

        selection = self._select_by_maxvisits_and_threshold(self.crossover_max_visits)
        if not self.crossover.is_applicable(selection):
            logger.warning(
                "Couldn't select enough tests to generate crossover candidates. "
                + f"Select: {len(selection)}, Crossover min size: {self.crossover.min_number_candidates_for_crossover}"
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
