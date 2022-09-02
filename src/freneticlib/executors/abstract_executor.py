import abc
import logging
from pathlib import Path
from typing import Union

from freneticlib.core.objective import AbstractObjective
from freneticlib.executors.normalizers.abstract_normalizer import AbstractNormalizer
from freneticlib.representations.abstract_generator import RoadGenerator

logger = logging.getLogger(__name__)


class AbstractExecutor(abc.ABC):
    def __init__(
        self,
        representation: RoadGenerator,
        objective: AbstractObjective,
        normalizer: AbstractNormalizer = None,
        results_path: Union[str, Path] = None,
    ):
        self.representation = representation
        self.normalizer = normalizer
        self.objective = objective
        self.results_path = Path(results_path) if results_path else None
        self.exit_on_error = True

        if results_path:
            logger.debug("Creating folder for storing simulation results.")
            self.results_path.mkdir(parents=True, exist_ok=True)

        self.exec_counter = -1  # counts how many executions have been

    def execute_test(self, test_dict: dict) -> dict:
        logger.debug(f"Execution of a test #{self.exec_counter} (generation method: {test_dict['method']})")
        self.exec_counter += 1  # counts how many executions have been

        test = test_dict["test"]
        if self.normalizer:
            test = self.normalizer.normalize(test_dict["test"])

        try:
            test_dict.update(self._execute(test))
        except Exception:
            logger.error("Error during execution of test.", exc_info=True)
            test_dict.update({self.objective.feature: None, "outcome": Outcome.ERROR})
            if self.exit_on_error:
                raise

        return test_dict

    @abc.abstractmethod
    def _execute(self, test) -> dict:
        pass
