import abc

from freneticlib.utils.random import seeded_rng


class RoadRepresentation(abc.ABC):
    def __init__(self, length: int, variation: int = 0):
        if length <= 0:
            raise ValueError("Cannot specify test length of zero")
        self.length = length
        self.variation = variation

    def get_length(self) -> int:
        return self.length + (0 if self.variation == 0 else seeded_rng().integers(-self.variation, self.variation + 1))

    def generate(self) -> list:
        """Generate a test of length `self.length` using the function get_value(previous points).
        Returns:
            (np.array) a list of delta values.
        """
        test_length = self.get_length()
        test = [self.get_value()]
        while len(test) < test_length:
            test.append(self.get_value(test))
        return test

    @abc.abstractmethod
    def get_value(self, previous: list = None):
        pass

    @abc.abstractmethod
    def to_cartesian(self, test):
        pass

    def is_valid(self, test) -> bool:
        return True

    def fix(self, test):
        return test
