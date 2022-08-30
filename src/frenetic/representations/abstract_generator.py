import abc
from frenetic.utils.random import seeded_rng


class RoadGenerator(abc.ABC):
    def __init__(self, length: int, variation: int = 0):
        self.length = length
        self.variation = variation

    def get_length(self) -> int:
        return self.length + (0 if self.variation == 0 else seeded_rng().integers(-self.variation, self.variation + 1))

    def generate(self) -> list[int]:
        """Generates a test of x points using the function get_value(previous points).
        Returns:
            a list of delta values.
        """
        test_length = self.get_length()
        test = []
        for i in range(test_length):
            test.append(self.get_value(test[:i]))
        return test

    @abc.abstractmethod
    def get_value(self, previous) -> int:
        pass

    @abc.abstractmethod
    def to_cartesian(self, test) -> list:
        pass
