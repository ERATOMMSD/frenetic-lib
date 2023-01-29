import abc

from freneticlib.core.core import TestIndividual


class StopCriterion(abc.ABC):
    @property
    @abc.abstractmethod
    def is_random_phase(self) -> bool:
        """Returns ``True`` when random generation should be performed.

        Returns:
            (bool): If the random phase is still ongoing.
        """
        pass

    @property
    @abc.abstractmethod
    def is_over(self) -> bool:
        """Returns ``True`` when the search is over.

        Return
            (bool): If the search is over.
        """
        pass

    @abc.abstractmethod
    def execute_test(self, test: TestIndividual):
        """Informs the stop criterion that a test will be executed.

        Args:
            test (TestIndividual): The test (road & execution data) that has been executed.
        """
        pass
