from abc import ABC, abstractmethod

from frenetic.utils.random import seeded_rng


class RoadGenerator(ABC):

    def __init__(self, length: int, variation: int = 0):
        self.length = length
        self.variation = variation

    def get_length(self) -> int:
        return self.length + seeded_rng().integers(-self.variation, self.variation)

    def generate(self) -> list[int]:
        """ Generates a test of x points using the function get_value(previous points).
        Returns:
            a list of delta values.
        """
        test_length = self.length + seeded_rng().integers(-self.variation, self.variation)
        test = []
        for i in range(test_length):
            test.append(self.get_value(test[:i]))
        return test

    @abstractmethod
    def get_value(self, previous) -> int:
        pass

    @abstractmethod
    def to_cartesian(self, test):
        pass
