import logging
import random
import time

from freneticlib.executors.abstract_executor import AbstractExecutor
from freneticlib.utils.random import seeded_rng

logger = logging.getLogger(__name__)


class MockExecutor(AbstractExecutor):
    """Inspired by SBST pipeline"""

    def _execute(self, the_test) -> dict:
        test_outcome = seeded_rng().choice(["FAIL"] * 3 + ["PASS"] * 5 + ["ERROR"])
        description = "Mocked test results"

        simulation_result = dict(
            outcome=test_outcome,
            description=description,
            timer=3.0,
            pos=[0.0, 0.0, 1.0],
            dir=[0.0, 0.0, 1.0],
            vel=[0.0, 0.0, 1.0],
            steering=0.0,
            steering_input=0.0,
            brake=0.0,
            brake_input=0.0,
            throttle=0.0,
            throttle_input=0.0,
            wheelspeed=0.0,
            vel_kmh=0.0,
            is_oob=False,
            oob_counter=0,
            max_oob_percentage=random.random(),
            oob_distance=0.0,
            oob_percentage=50.0,
        )

        time.sleep(0.1)

        return simulation_result
