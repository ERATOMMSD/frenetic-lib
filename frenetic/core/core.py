from typing import Generator, Iterator

import pandas as pd
from frenetic.core.representations.abstract import RoadGenerator

import logging
logger = logging.getLogger(__name__)


class FreneticCore(object):

    def __init__(self, representation: RoadGenerator, mutator=None, exploiter=None, crossover=None,
                 feature_threshold=0.0, dynamic_threshold=False):
        self.representation = representation

        self.mutator = mutator
        self.exploiter = exploiter
        self.crossover = crossover

        self.df = None

        self.search_feature = "max_oob_percentage"

        # Warnings when operators are None
        self._warn_if_none(crossover, "crossover")
        self._warn_if_none(mutator, "mutator")
        self._warn_if_none(exploiter, "exploiter")

        # Only considering tests with a min_oob_distance < threshold for mutation (2.0 is the max_value)

        self.min_length_to_mutate = 5
        self.crossover_max_visits = 10

        # quality filters for mutation / crossover parents
        self.target_feature = "max_oob_percentage"
        self.goal = max # min
        self.minimize = self.goal is min

        self.feature_threshold = feature_threshold
        self.dynamic_threshold = dynamic_threshold

    def _warn_if_none(self, var, name):
        if not var:
            logger.warning(f"No {name} operator was chosen.")

    def ask_random(self) -> dict:
        return dict(test=self.representation.generate(), method='random', visited=0, generation=0)

    def tell(self, record: dict):
        logger.debug(f"Tell:") # {road} -> {result}")
        if self.df is None:
            self.df = pd.DataFrame([record])
        else:
            self.df = pd.concat([self.df, pd.DataFrame([record])], ignore_index=True)

    def ask(self) -> Iterator[dict]:
        """This is actually a python generator, it will produce roads as long as we ask it"""
        while True:
            # First we mutate (or generate random)
            mutated_tests = self.get_mutated_tests()
            if len(mutated_tests) == 0:
                logger.debug("No mutations. Generating a random test.")
                yield self.ask_random()

            yield from mutated_tests

            # TODO: we first execute all mutations (without re-selecting best parent)
            #  But then we do crossovers _using_ the new mutations, right?

            # then we crossover
            crossover_tests = self.get_crossover_tests()
            yield from crossover_tests

            # TODO: I don't understand this code here. Check with Ezequiel.
            # if self.crossover and 0 < self.crossover.frequency <= self.executed_count:
            #     logger.info('Entering recombination phase.')
            #     self.parents_recombination()
            #     self.executed_count = 0
            #     if self.dynamic_threshold:
            #         self.recalculate_threshold()

    def get_mutated_tests(self) -> list:
        """Returns a list of tests"""
        parent = self._get_best_parent()  # returns a row
        if parent is None:
            logger.warning("Couldn't find a good parent. Skipping.")
            return []

        # TODO: why isn't this in the filter?
        #  Shouldn't we get the best parent of min_length?
        if len(parent.test.item()) < self.min_length_to_mutate:
            logger.debug("Best parent's test is too short.")
            return []

        logger.debug(f"Best unvisited parent for mutation is {parent.index[0]}")
        self.df.at[parent.index[0], 'visited'] = 1

        if self.exploiter and parent.outcome.item() == 'FAIL':
            return self._perform_modifications(self.exploiter.get_all(), parent, stop_reproduction=True)
        elif self.mutator and parent.outcome.item() == 'PASS':
            return self._perform_modifications(self.mutator.get_all(), parent)
        else:
            logger.warning("No modification was applied because there is no exploiter nor mutator defined.")
            return []

    def _perform_modifications(self, functions, parent, stop_reproduction=False) -> list:
        test = parent.test.item()
        if test is None:
            return []

        test_info = self.get_parent_info(parent.index.item())
        test_info["visited"] = 1 if stop_reproduction else 0

        modified_tests = [dict(test=function(test), method=name, **test_info) for name, function in functions]

        # TODO: There's stuff in here that I don't understand. Why is suggestions a dict?
        #   Why do we store standard in "parameter"?

        return modified_tests

    # def perform_modifications_original(self, functions, parent, stop_reproduction=False) -> list:
    #     # Only considering paths with more than 10 values for mutations
    #     # test might be empty if the parent was obtained from reversing road points
    #     test = parent.test.item()
    #     if test and len(test) >= self.min_length_to_mutate:
    #         i = 0
    #         while self.is_time_available() and i < len(functions):
    #             name, function = functions[i]
    #             logger.info(f'Mutation function: {name}')
    #             modified_versions = function(test)
    #             if isinstance(modified_versions, dict):
    #                 suggestions = modified_versions
    #             else:
    #                 suggestions = {'standard': modified_versions}
    #
    #             outcome = None
    #             for k, modified_test in suggestions.items():
    #                 info = self.get_parent_info(parent.index.item())
    #                 info['visited'] = 1 if stop_reproduction else 0
    #                 info['parameter'] = k
    #                 outcome = self.execute_test(modified_test, method=name, info=info)
    #
    #             i += 1
    #             if outcome == 'FAIL':
    #                 # Stop mutating this parent when one of the children already produced a failure
    #                 break

    # def mutator_defined(self, outcome):
    #     return (outcome == 'FAIL' and self.executor is not None) or (outcome == 'PASS' and self.mutator is not None)

    def _get_best_parent(self):
        if len(self.df) <= 0:
            logger.warning("Empty history. Cannot get best parent.")
            return

        assert self.target_feature in self.df.columns, "Target feature is recorded in history records."

        # we take the best parent that hasn't been visited yet, whose feature is below/above the threshold
        selection = self._select_by_maxvisits_and_threshold(max_visits=0)

        if len(selection) > 0:
            parent = selection.sort_values(self.target_feature, ascending=self.minimize).head(1)
            return parent

    def _select_by_maxvisits_and_threshold(self, max_visits=0):
        pass_fail_filter = self.df.outcome.isin(["PASS", "FAIL"])
        max_visit_filter = self.df.visited <= max_visits
        threshold_filter = self.df[self.target_feature] <= self.feature_threshold if self.minimize else self.df[self.target_feature] >= self.feature_threshold

        return self.df[pass_fail_filter & max_visit_filter & threshold_filter]

    def get_parent_info(self, p_index) -> dict:
        parent = self.df.iloc[p_index]
        return {'parent_1_index': p_index,
                'parent_1_outcome': parent['outcome'],
                'parent_1_'+self.target_feature: parent[self.target_feature],
                'generation': parent['generation'] + 1}

    def get_crossover_tests(self) -> list:
        if self.crossover is None:
            logger.info("No crossover defined. Skipping.")
            return []

        # parents_recombination
        candidates = self._select_crossover_candidates()
        if len(candidates) > 0:
            generated_children = self.crossover.generate(candidates)
            child_tests = []
            for child, method, info in generated_children:
                self.df.at[info['parent_1_index'], 'visited'] = self.df.iloc[info['parent_1_index']]['visited'] + 1
                self.df.at[info['parent_2_index'], 'visited'] = self.df.iloc[info['parent_2_index']]['visited'] + 1
                child_tests.append(dict(test=child, method=method, **info))
            return child_tests
        else:
            logger.warning("No candidates for crossover.")
            return []

    # def mutate_test(self, parent):
    #     # Applying different operators depending on the outcome
    #     if self.exploiter and parent.outcome.item() == 'FAIL':
    #         self.perform_modifications_original(self.exploiter.get_all(), parent, stop_reproduction=True)
    #     elif self.mutator and parent.outcome.item() == 'PASS':
    #         self.perform_modifications_original(self.mutator.get_all(), parent)
    #     else:
    #         logger.warning("No modification was applied because there is no exploiter nor mutator defined.")

    def _select_crossover_candidates(self) -> list:
        if len(self.df) <= 0:
            logger.warning("Empty history. Cannot get best parent.")
            return []

        assert self.target_feature in self.df.columns, "Target feature is recorded in history records."

        selection = self._select_by_maxvisits_and_threshold(self.crossover_max_visits)
        if len(selection) < self.crossover.min_size:
            logger.warning(f"Couldn't select enough tests to generate crossover candidates. Select: {len(selection)}, Crossover min size: {self.crossover.min_size}")
            return []

        candidates = []
        for index, candidate in selection.iterrows():
            test = candidate['test']
            if type(test) == str:
                logger.warning('Test was stored as a string value in the data frame.')
                test = ast.literal_eval(test)
            candidates.append( (test, self.get_parent_info(index)) )

        return candidates

    # def parents_recombination(self):
    #     candidates = self._select_crossover_candidates()
    #     if candidates:
    #         children = self.crossover.generate(candidates)
    #         while self.is_time_available() and len(children) > 0:
    #             child, method, info = children.pop()
    #             self.df.at[info['parent_1_index'], 'visited'] = self.df.iloc[info['parent_1_index']]['visited'] + 1
    #             self.df.at[info['parent_2_index'], 'visited'] = self.df.iloc[info['parent_2_index']]['visited'] + 1
    #             self.execute_test(child, method=method, info=info)

