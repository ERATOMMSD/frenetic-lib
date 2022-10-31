import abc
import logging
from typing import List

import numpy as np

from freneticlib.executors.outcome import Outcome
from freneticlib.representations import abstract_generator
from freneticlib.utils.random import seeded_rng

logger = logging.getLogger(__name__)


def calculate_test_similarity(parent_1, parent_2) -> float:
    min_len = min(len(parent_1), len(parent_2))
    same_count = 0
    for i in range(min_len):
        if parent_1[i] == parent_2[i]:
            same_count += 1
    return 0.0 if min_len == 0 else same_count / min_len


def combine_parents_info(parent_1_info, parent_2_info) -> dict:
    info = {}
    info.update(parent_1_info)
    for k, v in parent_2_info.items():
        if k == "generation":
            info["generation"] = max(parent_2_info["generation"], info["generation"])
        else:
            p2_label = k.replace("1", "2")
            info[p2_label] = v
    # if one of the two parents already failed we do not revisit this test
    info["visited"] = parent_1_info["parent_1_outcome"] == Outcome.FAIL or parent_2_info["parent_1_outcome"] == Outcome.FAIL
    return info


class AbstractCrossoverOperator(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def __call__(self, generator: abstract_generator.RoadGenerator, parent_1, parent_2):
        pass

    def __str__(self):
        return self.__class__.__name__

    def is_applicable(self, generator: abstract_generator.RoadGenerator, parent_1, parent_2) -> bool:
        return True


class ChromosomeCrossover(AbstractCrossoverOperator):
    def __call__(self, generator: abstract_generator.RoadGenerator, parent_1, parent_2):
        min_len = min(len(parent_1), len(parent_2))
        np_arr = np.array([parent_1[:min_len], parent_2[:min_len]])  # crop to min_len and make to numpy array
        children = seeded_rng().permuted(np_arr)  # permutate along axis using numpy
        return [children[0].tolist(), children[1].tolist()]


class SinglePointCrossover(AbstractCrossoverOperator):
    def __call__(self, generator: abstract_generator.RoadGenerator, parent_1, parent_2):
        # more or less in the middle
        amount = min(len(parent_1) // 2 - 2, len(parent_2) // 2 - 2)
        variability = seeded_rng().integers(-amount, amount)
        middle_parent_1 = len(parent_1) // 2 + variability
        middle_parent_2 = len(parent_2) // 2 + variability

        child_1 = parent_1[middle_parent_1:] + parent_2[:middle_parent_2]
        child_2 = parent_2[middle_parent_2:] + parent_1[:middle_parent_1]
        return [child_1, child_2]


class AbstractCrossover(abc.ABC):

    def __init__(self, operators: List[AbstractCrossoverOperator] = None):
        self.operators = operators

    @abc.abstractmethod
    def __call__(self, generator: abstract_generator.RoadGenerator, parent_candidates: list) -> list:
        pass

    def is_applicable(self, parent_candidates: list) -> bool:
        return True


class ChooseRandomCrossoverOperator(AbstractCrossover):
    def __init__(self, operators: List[AbstractCrossoverOperator] = None, size: int = 20, similarity_threshold: float = 0.95):
        operators = operators or [  # default exploiters
            ChromosomeCrossover(),
            SinglePointCrossover()
        ]
        super().__init__(operators)
        self.similarity_threshold = similarity_threshold

        self.size = size
        self.min_number_candidates_for_crossover = 4

    def __call__(self, generator: abstract_generator.RoadGenerator, parent_candidates: list) -> list:
        """
        Args:
            candidates (list): A list of candidate tests to be chosen as parents

        Returns:
            (list) A list of children of (almost) same size
        """
        if not self.is_applicable(parent_candidates):
            return []

        children = []
        attemps = 0
        target_children = min(self.size, len(parent_candidates))
        while len(children) < target_children and attemps < target_children * 2:
            (parent_1, parent_1_info), (parent_2, parent_2_info) = seeded_rng().choice(
                np.asarray(parent_candidates, dtype=object), 2
            )
            if calculate_test_similarity(parent_1, parent_2) < self.similarity_threshold:
                chosen_operator = seeded_rng().choice(self.operators)
                method = str(chosen_operator)
                parents_info = combine_parents_info(parent_1_info, parent_2_info)
                if chosen_operator.is_applicable(generator, parent_1, parent_2):
                    newborns = chosen_operator(generator, parent_1, parent_2)
                    new_children = [(child, method, parents_info) for child in newborns]
                    children.extend(new_children)
            else:
                logger.info("Discarding parents combination due to genetic similarity")

        return children

    def generate(self, *args, **kwargs):
        return self(*args, **kwargs)

    def is_applicable(self, parent_candidates: list) -> bool:
        return len(parent_candidates) >= self.min_number_candidates_for_crossover