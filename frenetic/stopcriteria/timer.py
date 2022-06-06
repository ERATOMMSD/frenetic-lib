import time


class TimeStop(object):
    """All timing is in seconds"""

    def __init__(self, random_time: int, total_time: int):
        self.random_time = random_time
        self.total_time = total_time
        self.reset()

    def reset(self):
        self.start_time = time.time()

    @property
    def is_over(self) -> bool:
        return self.remaining_time <= 0

    @property
    def is_random_phase(self) -> bool:
        return self.elapsed_time <= self.random_time

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    @property
    def remaining_time(self) -> float:
        return self.total_time - self.elapsed_time

    def execute_test(self, test):
        pass

    def __str__(self):
        return f"Start {self.start_time}, Elapsed: {self.elapsed_time}; Remaining: {self.remaining_time}"