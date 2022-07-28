from .abstract import StopCriterion


class CountingStop(StopCriterion):

    def __init__(self, n_total, n_random):
        self.n_total = n_total
        self.n_random = n_random

        self.exec_count = 0

    @property
    def is_over(self) -> bool:
        return self.exec_count >= self.n_total


    @property
    def is_random_phase(self) -> bool:
        return self.exec_count < self.n_random


    def execute_test(self, test):
        self.exec_count += 1

