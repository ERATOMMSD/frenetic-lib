import logging

import matplotlib.pyplot as plt
import pandas as pd

from freneticlib.core.core import FreneticCore
from freneticlib.executors.executor import Executor
from freneticlib.stopcriteria.abstract import StopCriterion

logger = logging.getLogger(__name__)


class Frenetic(object):
    """Main class for Frenetic-based ADS testing."""

    def __init__(self, core: FreneticCore, executor: Executor, stop_criterion: StopCriterion):
        """Constructor.

        Args:
            core (FreneticCore): The core instance that handles the ask/tell interface, mutation
            executor (Executor): Specifies the executor (e.g. Bicycle executor).
            stop_criterion (StopCriterion): Specification of when to stop random phase and completely.
        """
        self.core = core
        self.executor = executor
        self.stop_criterion = stop_criterion

    def start(self):
        """Start the search.

        First triggers simulation of random roads followed by the mutation phase."""
        logger.info("Starting Initial Random Generation Phase...")
        logger.info("-------------------------------------------")
        while self.stop_criterion.is_random_phase:
            test_dict = self.core.ask_random()
            self.stop_criterion.execute_test(test_dict)
            result_dict = self.executor.execute_test(test_dict)
            self.core.tell(result_dict)
        logger.info("--------------------------------------------")
        logger.info("Finishing Initial Random Generation Phase...")

        logger.info("Starting Mutation Phase...")
        logger.info("--------------------------")

        while not self.stop_criterion.is_over:
            test_dict = self.core.ask()
            self.stop_criterion.execute_test(test_dict)
            result_dict = self.executor.execute_test(test_dict)
            self.core.tell(result_dict)
        else:
            logger.info("---------------------------")
            logger.info("Finishing Mutation Phase...")

        logger.info("The END.")
        logger.info("--------")

    def store_results(self, filename: str):
        """Store the results in a CSV file."""
        logger.info(f"Storing the all the experiment results in file {filename}.")
        self.core.history.to_csv(filename)  # , indent=4)

    def load_history(self, filename: str):
        """Load an execution history from a CSV file."""
        logger.info(f"Reading {filename} into the history.")
        self.core.history = pd.read_csv(filename)

    def plot(self, filename: str = None):
        """Very simple plotting facility.

        Creates a line plot showing the objective feature's value for each simulation.
        Random generations are shown in gray, the mutated values in blue.
        Args:
            filename (str, optional): If a filename is specified, plot will be stored on disk. Otherwise, it will be shown on screen. Defaults to None.

        """
        feature = self.core.objective.feature

        # plot random part
        ax = self.core.history[self.core.history.method == "random"].plot(y=feature, color="gray", grid=True, ylabel=feature)
        ax = self.core.history[self.core.history.method != "random"].plot(ax=ax, y=feature, color="blue", grid=True, ylabel=feature)
        ax.legend(["random", "mutation"])
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
