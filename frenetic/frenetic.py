

import logging

from frenetic.core.core import FreneticCore
from frenetic.core.representations.abstract import RoadGenerator
from frenetic.executors.abstract import Executor
from frenetic.stopcriteria.abstract import StopCriterion
from frenetic.utils.random import seeded_rng

logger = logging.getLogger(__name__)


class Frenetic(object):
    """Main class for Frenetic-based ADS testing."""

    def __init__(self,
                 core: FreneticCore,
                 executor: Executor,
                 stop_criterion: StopCriterion):

        self.core = core
        self.executor = executor
        self.stop_criterion = stop_criterion

    def start(self):
        logger.info("Starting Initial Random Generation Phase...")
        logger.info("-------------------------------------------")
        while self.stop_criterion.is_random_phase:
            test_dict = self.core.ask_random()
            # result_dict.update(dict(elapsed_time=self.timer.elapsed_time))
            self.stop_criterion.execute_test(test_dict)
            result_dict = self.executor.execute_test(test_dict)
            self.core.tell(result_dict)
        logger.info("--------------------------------------------")
        logger.info("Finishing Initial Random Generation Phase...")

        logger.info("Starting Mutation Phase...")
        logger.info("--------------------------")
        mutation_gen = self.core.ask()
        while not self.stop_criterion.is_over:
            test_dict = next(mutation_gen)
            self.stop_criterion.execute_test(test_dict)
            result_dict = self.executor.execute_test(test_dict)
            self.core.tell(result_dict)
        else:
            logger.info("---------------------------")
            logger.info("Finishing Mutation Phase...")

        logger.info("The END.")
        logger.info("--------")

    def store_results(self, filename: str = None):
        logger.info("Storing the all the experiment results in a file.")
        self.core.df.to_json(filename, indent=4)


class FreneticVerbose(object):
    """Main class for Frenetic-based ADS testing."""

    def __init__(self,
                 time_budget: int = 100,
                 executor: Executor = None,
                 generator: RoadGenerator = None,
                 result_filename: str = None,

                 map_size=None,
                 mutator=None, exploiter=None, crossover=None,
                 strict_father=True, random_budget=3600, random_budget_percentage=None,
                 min_oob_threshold=0.0, dynamic_threshold=False,

                 normalizer=None):

        # Only considering tests with a min_oob_distance < threshold for mutation (2.0 is the max_value)
        self.dynamic_threshold = dynamic_threshold
        self.min_oobd_threshold = min_oob_threshold
        self.min_length_to_mutate = 5
        self.max_visits = 10

        self.timer = FreneticTimer(time_budget)
        self.core = FreneticCore(generator, mutator, exploiter, crossover, normalizer)
        self.executor = executor

        self.result_filename = result_filename

        # Getting the time budget from the executors
        time_budget = executor.time_budget.time_budget if executor.time_budget.time_budget is not None else executor.time_budget.generation_budget
        self.random_gen_budget = random_budget_percentage * time_budget if random_budget_percentage else random_budget

