import abc
import logging
from pathlib import Path
from typing import Dict, Union

from freneticlib.core.objective import Objective
from freneticlib.executors.outcome import Outcome
from freneticlib.executors.road_validator import RoadValidator
from freneticlib.representations.abstract_representation import RoadRepresentation

logger = logging.getLogger(__name__)


class Executor(abc.ABC):
    def __init__(
        self,
        representation: RoadRepresentation,
        objective: Objective,
        results_path: Union[str, Path] = None,
        road_validator: RoadValidator = None,
    ):
        self.representation = representation
        self.objective = objective
        self.results_path = Path(results_path) if results_path else None
        self.road_validator = road_validator
        self.exit_on_error = True

        if results_path:
            logger.debug("Creating folder for storing simulation results.")
            self.results_path.mkdir(parents=True, exist_ok=True)

        self.exec_counter = -1  # counts how many executions have been

    def execute_test(self, test_dict: Dict) -> Dict:
        logger.debug(f"Execution of a test #{self.exec_counter} (generation method: {test_dict['method']})")
        self.exec_counter += 1  # counts how many executions have been

        test = test_dict["test"]

        if self.road_validator:
            valid, invalid_info = self.road_validator.is_valid(test)
            if not valid:
                logger.debug("The generated road is invalid")
                test_dict.update({self.objective.feature: None, "outcome": Outcome.INVALID, "info": invalid_info})
                return test_dict

        try:
            test_dict.update(self._execute(test))
        except Exception:
            logger.error("Error during execution of test.", exc_info=True)
            test_dict.update({self.objective.feature: None, "outcome": Outcome.ERROR})
            if self.exit_on_error:
                raise

        return test_dict

    @abc.abstractmethod
    def _execute(self, test) -> Dict:
        pass
