import abc


class StopCriterion(abc.ABC):
    @property
    @abc.abstractmethod
    def is_random_phase(self) -> bool:
        """Returns True when random generation should be performed."""
        pass

    @property
    @abc.abstractmethod
    def is_over(self) -> bool:
        """Returns True when it's time to stop."""
        pass

    @abc.abstractmethod
    def execute_test(self, test):
        """Informs the stop criterion that a test will be executed."""
        pass
