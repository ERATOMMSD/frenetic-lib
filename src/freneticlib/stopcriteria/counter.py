from .abstract import StopCriterion
from ..core.core import TestIndividual
from ..executors.outcome import Outcome


class CountingStop(StopCriterion):
    """A concrete `.StopCriterion` based on execution counts."""

    exec_count = 0
    """Keeps track of the number of executions."""

    def __init__(self, n_total, n_random, count_invalid=False):
        """
        Args:
            n_total (int): How many total simulations to allow.
            n_random (int): How many simulations to do before the random phase ends.
            count_invalid (bool): Whether invalid roads (``test["outcome"] = :attr:`Outcome.INVALID` ``)
                that have not been simulated should also be counted towards the budget or ignored.
        """
        self.n_total = n_total
        self.n_random = n_random
        self.count_invalid = count_invalid

        self.exec_count = 0

    @property
    def is_over(self) -> bool:
        """
        Returns:
            (bool): States whether there is any total execution budget left or not.
        """
        return self.exec_count >= self.n_total

    @property
    def is_random_phase(self) -> bool:
        """
        Returns:
             (bool): States whether there is any random budget is still available.
        """
        return self.exec_count < self.n_random

    def execute_test(self, test: TestIndividual):
        """Inform the stop criterion that a test has been executed.
        Increases :attr:`.exec_count`, but only if ``self.count_invalid`` is ``True``
            and the ``test["outcome"]`` is not :attr:`.Outcome.INVALID`.

        Args:
            test (TestIndividual): The test that has been executed.
        """
        if self.count_invalid or test["outcome"] != Outcome.INVALID:
            self.exec_count += 1
