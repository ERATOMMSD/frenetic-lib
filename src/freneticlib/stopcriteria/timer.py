import time


class TimeStop(object):
    """All timing is in seconds"""

    def __init__(self, random_time: int, total_time: int):
        """
        Args:
            random_time (int): How many seconds of random search time to allow.
            total_time (int): How many seconds of total search time to allow.
        """
        self.random_time = random_time
        self.total_time = total_time
        self.reset()

    def reset(self):
        self.start_time = time.time()

    @property
    def is_over(self) -> bool:
        """
        Returns:
            (bool): States whether the search budget has been used up.
        """
        return self.remaining_time <= 0

    @property
    def is_random_phase(self) -> bool:
        """
        Returns:
            (bool): States whether there is random search budget remaining.
        """
        return self.elapsed_time <= self.random_time

    @property
    def elapsed_time(self) -> float:
        """
        Returns:
            (float): How much time has passed since starting the timer.
        """
        return time.time() - self.start_time

    @property
    def remaining_time(self) -> float:
        """
        Returns:
            (float): How much time there is left.
        """
        return self.total_time - self.elapsed_time

    def execute_test(self, test):
        """Inform the stop criterion that a test has been executed.

        Does nothing.
        """
        pass

    def __str__(self) -> str:
        """
        Returns:
            (str): Return a string containing Start, Elapsed and Remaining time.
        """
        return f"Start {self.start_time}, Elapsed: {self.elapsed_time}; Remaining: {self.remaining_time}"
