import abc
import logging
from typing import Dict, List

import numpy as np

from freneticlib.executors.outcome import Outcome
from freneticlib.representations import abstract_representation
from freneticlib.utils.random import seeded_rng

logger = logging.getLogger(__name__)


def calculate_test_similarity(parent_1, parent_2) -> float:
    """Calculate the similarity of two roads.

    Args:
        parent_1: First operand.
        parent_2: Second operand.

    Returns:
        (float): The similarity factor.
    """
    min_len = min(len(parent_1), len(parent_2))
    same_count = 0
    for i in range(min_len):
        if parent_1[i] == parent_2[i]:
            same_count += 1
    return 0.0 if min_len == 0 else same_count / min_len


def combine_parents_info(parent_1_info, parent_2_info) -> Dict:
    """Combine the information of two roads, so we can trace where crossover offspring was generated from.

    Args:
        parent_1_info: First parent's information-dict.
        parent_2_info: Second parent's information-dict.

    Returns:
        (Dict): The combined information of both parents.
    """
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
    """Abstract parent of all crossover operators."""
    def __init__(self):
        pass

    @abc.abstractmethod
    def __call__(self, representation: abstract_representation.RoadRepresentation, parent_1, parent_2):
        """
        Create a new road by combining road points from two parents.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            parent_1: The first operand for the crossover.
            parent_2: The second operand for the crossover.

        Returns:
            The offspring, i.e. combination of both parent roads.
        """
        pass

    def __str__(self):
        return self.__class__.__name__

    def is_applicable(self, representation: abstract_representation.RoadRepresentation, parent_1, parent_2) -> bool:
        """
        Check if test can be mutated.

        Args:
            test: The road (in a given representation).

        Returns:
            (bool): Whether the mutation operator is applicable.
        """
        return True


class ChromosomeCrossover(AbstractCrossoverOperator):
    """
    Crossover operator that creates two new roads by randomly selecting roads from both parents.
    """
    def __call__(self, representation: abstract_representation.RoadRepresentation, parent_1, parent_2) -> List:
        min_len = min(len(parent_1), len(parent_2))
        np_arr = np.array([parent_1[:min_len], parent_2[:min_len]])  # crop to min_len and make to numpy array
        children = seeded_rng().permuted(np_arr)  # permutate along axis using numpy
        return [children[0].tolist(), children[1].tolist()]


class SinglePointCrossover(AbstractCrossoverOperator):
    """
    Crossover operator that creates two new roads by (roughly) splitting both roads in half,
    and combining each "head" with the respective other tail.

    For example, given that
    ``R1 = [A, B, C, D, E, F, G]`` and
    ``R2 = [1, 2, 3, 4, 5, 6, 7]``

    then ``R1 x R2`` yields, eg.
    ``C1 = [A, B, C, D, 5, 6, 7]`` and
    ``C2 = [1, 2, 3, 4, E, F, G]``
    """
    def __call__(self, representation: abstract_representation.RoadRepresentation, parent_1, parent_2) -> List:
        # more or less in the middle
        amount = min(len(parent_1) // 2 - 2, len(parent_2) // 2 - 2)
        variability = seeded_rng().integers(-amount, amount)
        middle_parent_1 = len(parent_1) // 2 + variability
        middle_parent_2 = len(parent_2) // 2 + variability

        child_1 = parent_1[middle_parent_1:] + parent_2[:middle_parent_2]
        child_2 = parent_2[middle_parent_2:] + parent_1[:middle_parent_1]
        return [child_1, child_2]


class AbstractCrossover(abc.ABC):
    """A container class for the crossover operators, selection strategy is implemented in :meth:`__call__`"""

    def __init__(self, operators: List[AbstractCrossoverOperator] = None):
        self.operators = operators

    @abc.abstractmethod
    def __call__(self, representation: abstract_representation.RoadRepresentation, parent_candidates: List) -> List:
        """
        Apply crossover to a list of parent candidates.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            parent_candidates (List): The parents that we take into consideration for producing offspring.

        Returns:
            (List): A list of offspring roads that were created by mating parent_candidates.
        """
        pass

    def is_applicable(self, parent_candidates: List) -> bool:
        """
        Check if it is possible to mate the parent_candidates.
        Args:
            parent_candidates (List): The parents that we take into consideration for producing offspring.

        Returns:
            (bool): If it is possible to mate those parents, or if there is an issue.
        """
        return True


class ChooseRandomCrossoverOperator(AbstractCrossover):
    """A container class that randomly chooses between a list of crossover operators.

    By default, the operator is chosen randomly from :class:`ChromosomeCrossover` and :class:`SinglePointCrossover`.
    """

    def __init__(self, operators: List[AbstractCrossoverOperator] = None, size: int = 20, similarity_threshold: float = 0.95):
        """
        Args:
            operators (List[AbstractCrossoverOperator]): The list of crossover operators to choose from.
            size (int): Maximum limit of offspring to create (practically it will be it's ``min(size, len(parent_candidates)``)
            similarity_threshold (float): Don't create crossovers of parents whose similarity exceeds this threshold.
        """
        operators = operators or [ChromosomeCrossover(), SinglePointCrossover()]  # default crossovers
        super().__init__(operators)
        self.similarity_threshold = similarity_threshold

        self.size = size
        self.min_number_candidates_for_crossover = 4

    def __call__(self, representation: abstract_representation.RoadRepresentation, parent_candidates: List) -> List:
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
                if chosen_operator.is_applicable(representation, parent_1, parent_2):
                    newborns = chosen_operator(representation, parent_1, parent_2)
                    new_children = [(child, method, parents_info) for child in newborns]
                    children.extend(new_children)
            else:
                logger.info("Discarding parents combination due to genetic similarity")

        return children

    def is_applicable(self, parent_candidates: list) -> bool:
        """
        Only apply crossover if there are enough parent_candidates available.

        Args:
            parent_candidates: The parent_candidates to check.

        Returns:
            (bool): Evaluates ``len(parent_candidates) >= self.min_number_candidates_for_crossover``
        """
        return len(parent_candidates) >= self.min_number_candidates_for_crossover
