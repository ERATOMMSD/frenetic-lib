import abc
from typing import List

import numpy as np

from freneticlib.utils.random import seeded_rng

from .abstract_representation import RoadRepresentation


def thetas_to_cartesian(x0, y0, theta0, ss_deltas, delta_thetas):
    xs = np.zeros(len(delta_thetas) + 1)
    ys = np.zeros(len(delta_thetas) + 1)
    thetas = np.zeros(len(delta_thetas) + 1)
    xs[0] = x0
    ys[0] = y0
    thetas[0] = theta0
    for i in range(thetas.shape[0] - 1):
        ss_diff_half = ss_deltas[i] / 2.0
        thetas[i + 1] = thetas[i] + delta_thetas[i]
        xs[i + 1] = xs[i] + (np.cos(thetas[i + 1]) + np.cos(thetas[i])) * ss_diff_half
        ys[i + 1] = ys[i] + (np.sin(thetas[i + 1]) + np.sin(thetas[i])) * ss_diff_half
    return list(zip(xs, ys))


class AbstractThetaRepresentation(RoadRepresentation, abc.ABC):
    def __init__(self, length: int, variation: int = 0, bound: float = np.pi / 12, delta: float = np.pi / 36):
        self.bound = bound
        self.delta = delta
        super().__init__(length=length, variation=variation)

    def get_theta(self, previous: List = None):
        last_value = 0
        if previous:
            last_value = previous[-1]
        return seeded_rng().uniform(max(-self.bound, last_value - self.delta), min(self.bound, last_value + self.delta))


# TODO: Consider adding the rest of the default parameters used in the transformation as part of the constructor
class FixStepThetaRepresentation(AbstractThetaRepresentation):
    def __init__(
        self, length: int, variation: int = 0, step: float = 10, bound: float = np.pi / 12, delta: float = np.pi / 36
    ):
        self.step = step
        super().__init__(length=length, variation=variation, bound=bound, delta=delta)

    def get_value(self, previous: List = None):
        return self.get_theta(previous)

    def to_cartesian(self, test):
        ss = [self.step] * len(test)
        return thetas_to_cartesian(x0=0, y0=0, theta0=1.57, ss_deltas=ss, delta_thetas=test)


class ThetaRepresentation(AbstractThetaRepresentation):
    def __init__(
        self,
        length: int,
        variation: int = 0,
        low_step: float = 5.0,
        high_step: float = 15.0,
        bound: float = 0.07,
        delta: float = np.pi / 36,
    ):
        self.low_step = low_step
        self.high_step = high_step
        super().__init__(length=length, variation=variation, bound=bound, delta=delta)

    def get_step(self):
        return seeded_rng().uniform(self.low_step, self.high_step)

    def get_value(self, previous: List = None):
        previous_thetas = None
        if previous:
            previous_thetas, _ = zip(*previous)
        return self.get_theta(previous_thetas), self.get_step()

    def to_cartesian(self, test):
        delta_thetas, ss_deltas = zip(*test)
        return thetas_to_cartesian(x0=0, y0=0, theta0=1.57, ss_deltas=ss_deltas, delta_thetas=delta_thetas)
