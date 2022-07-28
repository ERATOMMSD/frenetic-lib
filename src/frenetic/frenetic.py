import logging

from frenetic.core.core import FreneticCore
from frenetic.executors.abstract_executor import Executor
from frenetic.stopcriteria.abstract import StopCriterion

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
        if filename is not None:
            logger.info(f"Storing the all the experiment results in file {filename}.")
            self.core.df.to_json(filename, indent=4)

