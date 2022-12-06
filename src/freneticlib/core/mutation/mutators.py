from typing import Dict, List, Tuple, Union

import numpy as np

from freneticlib.representations import abstract_representation
from freneticlib.utils.random import seeded_rng

from .abstract_operators import AbstractMutationOperator, AbstractMutator


def get_test(parent_info: Union[Dict, List[float]]) -> List[Union[float, Tuple[float, float]]]:
    """Return the (numeric) test from a parent_info dict."""
    if isinstance(parent_info, Dict):
        test = parent_info["test"]
    else:
        test = parent_info
    return test


class RemoveFront(AbstractMutationOperator):
    def __init__(self, remove_at_least: int = 1, remove_at_most: int = 5, min_length_for_operator: int = 10):
        self.remove_at_least = remove_at_least
        self.remove_at_most = remove_at_most
        self.min_length_for_operator = min_length_for_operator

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        assert self.is_applicable(test)
        return test[seeded_rng().integers(self.remove_at_least, self.remove_at_most) :]

    def is_applicable(self, test) -> bool:
        return len(test) >= self.min_length_for_operator


class RemoveBack(AbstractMutationOperator):
    def __init__(self, remove_at_least: int = 1, remove_at_most: int = 5, min_length_for_operator: int = 10):
        self.remove_at_least = remove_at_least
        self.remove_at_most = remove_at_most
        self.min_length_for_operator = min_length_for_operator

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        assert len(test) >= self.min_length_for_operator
        return test[: -seeded_rng().integers(self.remove_at_least, self.remove_at_most)]

    def is_applicable(self, test) -> bool:
        return len(test) >= self.min_length_for_operator


class RemoveRandom(AbstractMutationOperator):
    def __init__(self, remove_at_least: int = 1, remove_at_most: int = 5, min_length_for_operator: int = 10):
        self.remove_at_least = remove_at_least
        self.remove_at_most = remove_at_most
        self.min_length_for_operator = min_length_for_operator

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        assert len(test) >= self.min_length_for_operator
        # number of test to be removed
        k = seeded_rng().integers(self.remove_at_least, self.remove_at_most)
        modified_test = test[:]
        while k > 0 and len(modified_test) > 5:
            # Randomly remove a kappa
            i = seeded_rng().integers(len(modified_test))
            del modified_test[i]
            k -= 1
        return modified_test

    def is_applicable(self, test) -> bool:
        return len(test) >= self.min_length_for_operator


class AddBack(AbstractMutationOperator):
    def __init__(self, add_at_least: int = 1, add_at_most: int = 5):
        self.add_at_least = add_at_least
        self.add_at_most = add_at_most

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        modified_test = test[:]
        for i in range(seeded_rng().integers(self.add_at_least, self.add_at_most)):
            modified_test.append(representation.get_value(modified_test))
        return modified_test


class ReplaceRandom(AbstractMutationOperator):
    def __init__(self, replace_at_least: int = 1, replace_at_most: int = 5):
        self.replace_at_least = replace_at_least
        self.replace_at_most = replace_at_most

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        # Randomly replace values
        indices = seeded_rng().choice(
            len(test), seeded_rng().integers(self.replace_at_least, self.replace_at_most), replace=False
        )
        modified_test = test[:]

        for i in sorted(indices):
            modified_test[i] = representation.get_value(modified_test[:i])
        return modified_test


class AlterValues(AbstractMutationOperator):
    def __init__(self, mutation_factor_low: float = 0.9, mutation_factor_high: float = 1.1, mutation_chance: float = 0.1):
        self.mutation_factor_low = mutation_factor_low
        self.mutation_factor_high = mutation_factor_high
        self.mutation_chance = mutation_chance

    def _alter_once(self, test):
        mutated = test.copy()
        # for each element, set a mutation factor
        factors = seeded_rng().uniform(self.mutation_factor_low, self.mutation_factor_high, size=test.shape)
        # random values to identify which ones to mutate
        chances = seeded_rng().uniform(size=test.shape)
        mask = chances < self.mutation_chance
        # mutate
        mutated[mask] = mutated[mask] * factors[mask]
        return mutated

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        test = np.array(test)  # force convert test to numpy array
        mutated = test.copy()

        while (mutated == test).all():  # until we have a mutation
            mutated = self._alter_once(test)

        return mutated.tolist()


class KappaStepAlterValues(AlterValues):
    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        test = np.array(test)  # force convert test to numpy array
        mutated = test.copy()

        # we need to ignore the last step, because it is unused!
        all_except_last_mask = np.ones(shape=mutated.shape, dtype=np.bool)
        all_except_last_mask[-1, 1] = False

        while (mutated == test)[all_except_last_mask].all():  # until we have a mutation, but not in the place of mask
            mutated = self._alter_once(test)

        return mutated.tolist()


class FreneticMutator(AbstractMutator):
    def __init__(self, operators: List[AbstractMutationOperator] = None):
        operators = operators or [  # default mutators
            RemoveFront(),
            RemoveBack(),
            RemoveRandom(),
            AddBack(),
            ReplaceRandom(),
            AlterValues(),
        ]
        super().__init__(operators)
