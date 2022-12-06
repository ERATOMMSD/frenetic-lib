import abc
from typing import List, Tuple

import numpy as np

from freneticlib.utils.random import seeded_rng

from .abstract_representation import RoadRepresentation


def frenet_to_cartesian(x0, y0, theta0, ss, kappas) -> List:
    xs = np.zeros(len(kappas))
    ys = np.zeros(len(kappas))
    thetas = np.zeros(len(kappas))
    xs[0] = x0
    ys[0] = y0
    thetas[0] = theta0
    for i in range(thetas.shape[0] - 1):
        ss_diff_half = (ss[i + 1] - ss[i]) / 2.0
        thetas[i + 1] = thetas[i] + (kappas[i + 1] + kappas[i]) * ss_diff_half
        xs[i + 1] = xs[i] + (np.cos(thetas[i + 1]) + np.cos(thetas[i])) * ss_diff_half
        ys[i + 1] = ys[i] + (np.sin(thetas[i + 1]) + np.sin(thetas[i])) * ss_diff_half
    return list(zip(xs, ys))


class AbstractKappaRepresentation(RoadRepresentation, abc.ABC):
    def __init__(self, length: int, variation: int = 0, global_bound: float = 0.07, local_bound: float = 0.05):
        self.global_bound = global_bound
        self.local_bound = local_bound
        super().__init__(length, variation)

    def get_kappa(self, last_kappa) -> float:
        return seeded_rng().uniform(
            max(-self.global_bound, last_kappa - self.local_bound), min(self.global_bound, last_kappa + self.local_bound)
        )


class FixStepKappaRepresentation(AbstractKappaRepresentation):
    def __init__(
        self, length: int, variation: int = 0, step: float = 10.0, global_bound: float = 0.0698, local_bound: float = 0.05
    ):
        self.step = step
        super().__init__(length=length, variation=variation, global_bound=global_bound, local_bound=local_bound)

    def get_value(self, previous: List = None) -> float:
        last_kappa = 0 if (previous is None or len(previous) == 0) else previous[-1]
        return self.get_kappa(last_kappa)

    def to_cartesian(self, test) -> List:
        ss = np.cumsum([self.step] * len(test)) - self.step
        return frenet_to_cartesian(x0=0, y0=0, theta0=1.57, ss=ss, kappas=test)

    def is_valid(self, test) -> bool:
        np_arr = np.array(test)

        # check global bounds
        if (abs(np_arr) > self.global_bound).any():
            return False

        # check global bounds
        diffs = np_arr[1:] - np_arr[:-1]
        if (abs(diffs) > self.local_bound).any():
            return False
        return True

    def fix(self, test):
        test[0] = max(min(test[0], self.global_bound), -self.global_bound)
        for i in range(1, len(test)):
            previous = test[i - 1]
            min_bound = max(-self.global_bound, previous - self.local_bound)
            max_bound = min(self.global_bound, previous + self.local_bound)
            test[i] = max(min(test[i], max_bound), min_bound)
        return test


class KappaRepresentation(AbstractKappaRepresentation):
    def __init__(
        self,
        length: int,
        variation: int = 0,
        low_step: float = 5.0,
        high_step: float = 15.0,
        global_bound: float = 0.07,
        local_bound: float = 0.05,
    ):
        self.low_step = low_step
        self.high_step = high_step
        super().__init__(length=length, variation=variation, global_bound=global_bound, local_bound=local_bound)

    def get_step(self) -> float:
        return seeded_rng().uniform(self.low_step, self.high_step)

    def get_value(self, previous: List = None) -> Tuple[float, float]:
        last_kappa = 0 if previous is None else previous[-1][0]
        return self.get_kappa(last_kappa), self.get_step()

    def to_cartesian(self, test: List) -> List:
        kappas, ss_deltas = zip(*test)
        ss = np.zeros(len(kappas))
        ss[1:] = np.cumsum(ss_deltas[0:-1])
        return frenet_to_cartesian(x0=0, y0=0, theta0=1.57, ss=ss, kappas=kappas)

    def is_valid(self, test) -> bool:
        np_arr = np.array(test)

        # check global bounds
        if (abs(np_arr[:, 0]) >= self.global_bound).any():
            return False

        # check global bounds
        diffs = np_arr[1:, 0] - np_arr[:-1, 0]
        if (abs(diffs) >= self.local_bound).any():
            return False

        # check step sizes
        if (np_arr[:, 1] <= self.low_step).any() or (np_arr[:, 1] >= self.high_step).any():
            return False

        return True

    def fix(self, test):
        test[0, 0] = max(min(test[0, 0], self.global_bound), -self.global_bound)
        for i in range(1, len(test)):
            previous = test[i - 1][0]
            min_bound = max(-self.global_bound, previous - self.local_bound)
            max_bound = min(self.global_bound, previous + self.local_bound)
            test[i, 0] = max(min(test[i, 0], max_bound), min_bound)
        return test
