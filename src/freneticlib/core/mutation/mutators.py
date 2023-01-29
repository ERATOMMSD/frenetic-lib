import logging
from typing import List

import numpy as np

from freneticlib.representations import abstract_representation
from freneticlib.utils.random import seeded_rng
from . import exploiters

from .abstract_operators import AbstractMutationOperator, AbstractMutator
from ...executors.outcome import Outcome

logger = logging.getLogger(__name__)


class RemoveFront(AbstractMutationOperator):
    """
    Mutation operator for removing a range of road points from the front of the test

    Args:
        remove_at_least (int): Minimum number of road points to remove.
        remove_at_most (int): Maximum number of road points to remove.
        min_length_for_operator (int): Minimum number of road points required for  application.
    """
    def __init__(self, remove_at_least: int = 1, remove_at_most: int = 5, min_length_for_operator: int = 10):
        self.remove_at_least = remove_at_least
        self.remove_at_most = remove_at_most
        self.min_length_for_operator = min_length_for_operator

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a copy of the road by removing a range of road points from the front of the road.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
        assert self.is_applicable(test)
        return test[seeded_rng().integers(self.remove_at_least, self.remove_at_most) :]

    def is_applicable(self, test) -> bool:
        """
        Check if test can be mutated.

        Args:
            test: The road (in a given representation).

        Returns:
            (bool): Whether the mutation operator is applicable.
        """
        return len(test) >= self.min_length_for_operator


class RemoveBack(AbstractMutationOperator):
    """
    Mutation operator for removing a range of road points from the back of the road.

    Args:
        remove_at_least (int): Minimum number of road points to remove.
        remove_at_most (int): Maximum number of road points to remove.
        min_length_for_operator (int): Minimum number of road points required for  application.
    """
    def __init__(self, remove_at_least: int = 1, remove_at_most: int = 5, min_length_for_operator: int = 10):
        self.remove_at_least = remove_at_least
        self.remove_at_most = remove_at_most
        self.min_length_for_operator = min_length_for_operator

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a copy of the road by removing a range of road points from the back of the road.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
        assert len(test) >= self.min_length_for_operator
        return test[: -seeded_rng().integers(self.remove_at_least, self.remove_at_most)]

    def is_applicable(self, test) -> bool:
        """
        Check if test can be mutated.

        Args:
            test: The road (in a given representation).

        Returns:
            (bool): Whether the mutation operator is applicable.
        """
        return len(test) >= self.min_length_for_operator


class RemoveRandom(AbstractMutationOperator):
    """
    Mutation operator for removing a random road points of the road.

    Args:
        remove_at_least (int): Minimum number of road points to remove.
        remove_at_most (int): Maximum number of road points to remove.
        min_length_for_operator (int): Minimum number of road points required for application.
    """
    def __init__(self, remove_at_least: int = 1, remove_at_most: int = 5, min_length_for_operator: int = 10):
        self.remove_at_least = remove_at_least
        self.remove_at_most = remove_at_most
        self.min_length_for_operator = min_length_for_operator

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a copy of the road by removing random road points.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
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
        """
        Check if test can be mutated.

        Args:
            test: The road (in a given representation).

        Returns:
            (bool): Whether the mutation operator is applicable.
        """
        return len(test) >= self.min_length_for_operator


class AddBack(AbstractMutationOperator):
    """
    Mutation operator for adding random road points at the end of the road.

    Args:
        add_at_least (int): Minimum number of road points to add.
        add_at_most (int): Maximum number of road points to add.
    """
    def __init__(self, add_at_least: int = 1, add_at_most: int = 5):
        self.add_at_least = add_at_least
        self.add_at_most = add_at_most

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a copy of the road with new road points added at the back of the road.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
        modified_test = test[:]
        for i in range(seeded_rng().integers(self.add_at_least, self.add_at_most)):
            modified_test.append(representation.get_value(modified_test))
        return modified_test


class ReplaceRandom(AbstractMutationOperator):
    """
    Mutation operator for replacing random road points replaced with new ones.

    Args:
        replace_at_least (int): Minimum number of road points to add.
        replace_at_most (int): Maximum number of road points to add.
    """
    def __init__(self, replace_at_least: int = 1, replace_at_most: int = 5):
        self.replace_at_least = replace_at_least
        self.replace_at_most = replace_at_most

    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a copy of the road with random road points replaced with new ones.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
        # Randomly replace road points
        indices = seeded_rng().choice(
            len(test), seeded_rng().integers(self.replace_at_least, self.replace_at_most), replace=False
        )
        modified_test = test[:]

        for i in sorted(indices):
            modified_test[i] = representation.get_value(modified_test[:i])
        return modified_test


class AlterValues(AbstractMutationOperator):
    """
    Mutation operator for altering random road points by multiplying with a factor.

    Args:
        mutation_factor_low (float): Minimum factor to apply to a road point.
        mutation_factor_high (float): Maximum factor to apply to a road point.
        mutation_chance (float): The mutation chance for each road point.
    """
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
        """
        Returns a copy of the road with random road points altered by a random factor.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
        test = np.array(test)  # force convert test to numpy array
        mutated = test.copy()

        while (mutated == test).all():  # until we have a mutation
            mutated = self._alter_once(test)

        return mutated.tolist()


class KappaStepAlterValues(AlterValues):
    """
    Value mutation operator for the :class:`.KappaRepresentation`.
    It alters random road points and the steps by multiplying with a factor.

    Args:
        mutation_factor_low (float): Minimum factor to apply to a road point.
        mutation_factor_high (float): Maximum factor to apply to a road point.
        mutation_chance (float): The mutation chance for each road point.
    """
    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a copy of the road with random road points altered by a random factor.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road (in a given representation).

        Returns:
            The mutated road.
        """
        test = np.array(test)  # force convert test to numpy array
        mutated = test.copy()

        # we need to ignore the last step, because it is unused!
        all_except_last_mask = np.ones(shape=mutated.shape, dtype=np.bool)
        all_except_last_mask[-1, 1] = False

        while (mutated == test)[all_except_last_mask].all():  # until we have a mutation, but not in the place of mask
            mutated = self._alter_once(test)

        return mutated.tolist()


class StandardMutator(AbstractMutator):
    """Default Mutator, applies all operators approach."""

    def __init__(self, mutation_operators: List[AbstractMutationOperator] = None):
        """
        Args:
            mutation_operators (List[AbstractMutationOperator]): The operators used for mutation.
        """
        self.mutation_operators = mutation_operators or [  # default mutators
            RemoveFront(),
            RemoveBack(),
            RemoveRandom(),
            AddBack(),
            ReplaceRandom(),
            AlterValues(),
        ]
        super().__init__(self.mutation_operators)

    def __call__(self, representation: abstract_representation.RoadRepresentation, parent):
        # check if the parent test drove off the road (Outcome.FAIL) or remained on the road (Outcome.PASS)
        if parent.test is None:
            return []

        # test_info = self.get_parent_info(parent.name)
        test_info = {"visited": 0}

        modified_tests = []
        for operator in self.mutation_operators:
            try:
                mutated_test = operator(representation, parent.test)
                if not representation.is_valid(mutated_test):
                    logger.debug(f"Mutation operator {str(operator)} produced an invalid test. Attempting to fix it.")
                    mutated_test = representation.fix(mutated_test)
                    if not representation.is_valid(mutated_test):
                        logger.warning("Couldn't fix the test.")
                        continue
                modified_tests.append(dict(test=mutated_test, method=str(operator), **test_info))
            except Exception:
                logger.error(f"Error during modification of test {test_info} during function {str(operator)}", exc_info=True)

        return modified_tests

    def get_all(self):
        return self.mutation_operators


class FreneticMutator(AbstractMutator):
    """The default mutator which implements the Frenetic approach.

     It distinguishes between exploration and exploitation."""

    def __init__(self, mutation_operators: List[AbstractMutationOperator] = None,
                 exploitation_operators: List[AbstractMutationOperator] = None):
        """
        Args:
            mutation_operators (List[AbstractMutationOperator]): The operators used for mutation.
            exploitation_operators (List[AbstractMutationOperator]): The operators used for exploration
        """
        self.mutation_operators = mutation_operators or [  # default mutators
            RemoveFront(),
            RemoveBack(),
            RemoveRandom(),
            AddBack(),
            ReplaceRandom(),
            AlterValues(),
        ]
        self.mutator = StandardMutator(self.mutation_operators)

        self.exploitation_operators = exploitation_operators or [  # default exploiters
            exploiters.ReverseTest(),
            exploiters.SplitAndSwap(),
            exploiters.FlipSign(),
        ]
        self.exploiter = StandardMutator(self.mutation_operators)

        super().__init__(self.mutation_operators + self.exploitation_operators)

    def __call__(self, representation: abstract_representation.RoadRepresentation, parent):
        # check if the parent test drove off the road (Outcome.FAIL) or remained on the road (Outcome.PASS)
        if self.exploitation_operators and parent["outcome"] == Outcome.FAIL:
            mutants = self.exploiter(representation, parent)
            for m in mutants:  # set stop reproduction!
                m["visited"] = 1
            return mutants
        elif self.mutation_operators and parent["outcome"] == Outcome.PASS:
            return self.mutator(representation, parent)
