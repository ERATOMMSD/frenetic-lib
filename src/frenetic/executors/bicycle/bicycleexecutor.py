import numpy as np
from frenetic.executors.abstract_executor import AbstractExecutor, Outcome


class BicycleExecutor(AbstractExecutor):
    pass


    def _execute(self, cartesian: list) -> dict:


        return dict(outcome=Outcome.ERROR)
