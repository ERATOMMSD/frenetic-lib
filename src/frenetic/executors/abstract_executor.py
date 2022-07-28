import abc
import enum

from frenetic.core.objective import AbstractObjective
from frenetic.executors.normalizers.abstract_normalizer import AbstractNormalizer

import logging
logger = logging.getLogger(__name__)


class Outcome(object):  # enum makes things complicated
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class AbstractExecutor(abc.ABC):

    def __init__(self, representation, objective: AbstractObjective, normalizer: AbstractNormalizer = None):
        self.representation = representation
        self.normalizer = normalizer
        self.objective = objective
        self.exec_counter = -1  # counts how many executions have been

    def execute_test(self, test_dict: dict) -> dict:
        logger.debug(f"Execution of a test (generation method: {test_dict['method']})")
        self.exec_counter += 1  # counts how many executions have been

        test = test_dict["test"]
        if self.normalizer:
            test = self.normalizer.normalize(test_dict["test"])

        cartesian = self.representation.to_cartesian(test)

        test_dict.update(self._execute(cartesian))
        return test_dict

    @abc.abstractmethod
    def _execute(self, test) -> dict:
        pass


