import abc
from typing import Callable, List

from freneticlib.representations import abstract_representation


class AbstractMutationOperator(abc.ABC):
    """Abstract parent of all mutation operators."""

    @abc.abstractmethod
    def __call__(self, representation: abstract_representation.RoadRepresentation, test):
        """
        Returns a new road by altering the original.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test:  The road to be mutated (in an acceptable representation).

        Returns:
            The mutated road.
        """
        pass

    def __str__(self):
        return self.__class__.__name__

    def is_applicable(self, test) -> bool:
        """
        Check if test can be mutated.

        Args:
            test: The road (in a given representation).

        Returns:
            (bool): Whether the mutation operator is applicable.
        """
        return True


class AbstractMutator(abc.ABC):
    """A container class for the mutation operators."""

    def __init__(self, operators: List[Callable]):
        self.operators = operators

    @abc.abstractmethod
    def __call__(self, representation: abstract_representation.RoadRepresentation, test) -> List:
        """
        Create a new road by combining road points from two parents.

        Args:
            representation (RoadRepresentation): The road representation used in this search.
            test: The parent to be mutated.

        Returns:
            (List) The mutated tests.
        """
        pass

    def get_all(self):
        """Return all operators."""
        return self.operators
