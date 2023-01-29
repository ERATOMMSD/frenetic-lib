import ast
import logging
from typing import Dict, Iterator, List

import pandas as pd

from freneticlib.core.mutation import abstract_operators
from freneticlib.core.mutation.crossovers import AbstractCrossover
from freneticlib.core.objective import Objective
from freneticlib.executors.outcome import Outcome
from freneticlib.representations.abstract_representation import RoadRepresentation

logger = logging.getLogger(__name__)

TestIndividual = Dict
"""The type that contains a road and its execution data."""


class FreneticCore(object):
    """The core module of freneticlib, implementing the genetic algorithm."""

    history: pd.DataFrame = None
    """Stores the history including road, execution outcome and parent info."""

    crossover_max_visits = 10
    """How many times an individual road can be selected as crossover parent, before it is "retired'."""

    def __init__(
        self,
        representation: RoadRepresentation,
        objective: Objective,
        mutator: abstract_operators.AbstractMutator = None,
        crossover: AbstractCrossover = None,
    ):
        """
        Args:
            representation (RoadRepresentation): The selected road representation.
            objective (Objective): The search objective. (Make sure it's the same as the one passed to the Executor).
            mutator (AbstractMutator): Holds the mutation operators for roads with :attr:`.Outcome.PASS`.
            exploiter (AbstractMutator): Special treatment to differently mutate roads with :attr:`.Outcome.FAIL`.
            crossover (AbstractCrossover): Defines which crossover operator(s) to apply.
        """
        self._mutant_generator = None
        self.representation = representation
        self.objective = objective

        self.mutator = mutator
        self.crossover = crossover

        # Warnings when operators are None
        if not mutator:
            logger.warning("No mutator was chosen.")
        if not crossover:
            logger.warning("No crossover was chosen.")

    def ask_random(self) -> TestIndividual:
        """Returns a random road in the specific road representation.

        Returs:
            (TestIndividual): A new, randomly generated road from :attr:`.representation`.
        """
        test = self.representation.generate()
        assert self.representation.is_valid(test), "The newly generated test should be valid."
        return dict(test=test, method="random", visited=0, generation=0)

    def tell(self, record: TestIndividual):
        """
        Register the result of an execution.

        Args:
            record (TestIndividual): A dict containing the road and execution data (outcome, feature value, ...).
        """

        logger.debug(f"Tell: {record}")  # {road} -> {result}")
        if self.history is None:
            self.history = pd.DataFrame([record])
        else:
            # self.df = self.df.append(record, ignore_index=True)
            self.history = pd.concat([self.history, pd.DataFrame([record])], ignore_index=True)

    def ask(self) -> TestIndividual:
        """Create """
        if self._mutant_generator is None:
            self._mutant_generator = self._ask()
        return next(self._mutant_generator)

    def _ask(self) -> Iterator[Dict]:
        """This is actually a generator, it will produce roads as long as we ask it.

        Specifically, it will first create a list of mutants based on the best known individual.
        Then, using the history and the mutants, it will create the crossover children and yield those.

        Yields:
            (dict): A dictionary containing a road and additional information of the test.
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

    def get_mutated_tests(self) -> List[TestIndividual]:
        """
        Searches for the best mutation parent, then performs a mutation depending on the parent's
        simulation outcome. :attr:`self.exploiter` will be applied if :attr:`.Outcome.FAIL`,
        :attr:`.Outcome.PASS` will trigger the :attr:`self.mutator`

        Returns:
            (List[TestIndividual]): The mutated test individuals.
        """
        parent = self._get_best_mutation_parent()  # returns a row
        if parent is None:
            logger.warning("Couldn't find a good parent. Skipping.")
            return []

        # TODO: why isn't this in the filter?
        #  Shouldn't we get the best parent of min_length?
        # if len(parent.test.item()) < self.min_length_to_mutate:
        #     logger.debug("Best parent's test is too short.")
        #     return []

        logger.debug(f"Best unvisited parent for mutation is {parent.name}")
        self.history.at[parent.name, "visited"] = 1

        parent_info = self.get_parent_info(parent.name)

        mutants = self.mutator(self.representation, parent)
        for m in mutants:
            m.update(parent_info)

        return mutants

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

    def get_crossover_tests(self) -> List[TestIndividual]:
        """
        Creates new tests by pairwise "mating" of
        simulation outcome. :attr:`self.exploiter` will be applied if :attr:`.Outcome.FAIL`,
        :attr:`.Outcome.PASS` will trigger the :attr:`self.mutator`

        Returns:
            (List[TestIndividual]): The mutated test individuals.
        """
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

    def _select_crossover_candidates(self) -> List[TestIndividual]:
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
