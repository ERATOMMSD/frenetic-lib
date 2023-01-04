from .abstract import StopCriterion
from ..executors.outcome import Outcome


class CountingStop(StopCriterion):
    def __init__(self, n_total, n_random, count_invalid=False):
        self.n_total = n_total
        self.n_random = n_random
        self.count_invalid = count_invalid

        self.exec_count = 0


    @property
    def is_over(self) -> bool:
        return self.exec_count >= self.n_total

    @property
    def is_random_phase(self) -> bool:
        return self.exec_count < self.n_random

    def execute_test(self, test):
        if self.count_invalid or test["outcome"] != Outcome.INVALID:
            self.exec_count += 1
