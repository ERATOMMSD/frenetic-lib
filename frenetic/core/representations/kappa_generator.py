import numpy as np
import abc
from .abstract import RoadGenerator
from frenetic.utils.trapezoidal_integration import frenet_to_cartesian
from frenetic.utils.random import seeded_rng


class AbstractKappaGenerator(RoadGenerator, abc.ABC):

    def __init__(self, length: int, variation: int = 0,
                 global_bound: float = 0.07, local_bound: float = 0.05):
        self.global_bound = global_bound
        self.local_bound = local_bound
        super().__init__(length, variation)

    def get_kappa(self, last_kappa):
        return seeded_rng().uniform(max(-self.global_bound, last_kappa - self.local_bound),
                                 min(self.global_bound, last_kappa + self.local_bound))


class FixStepKappaGenerator(AbstractKappaGenerator):

    def __init__(self, length: int, variation: int = 0, step: float = 10.0,
                 global_bound: float = 0.0698, local_bound: float = 0.05):
        self.step = step
        super().__init__(length=length, variation=variation, global_bound=global_bound, local_bound=local_bound)

    def get_value(self, previous):
        last_kappa = 0
        if previous:
            last_kappa = previous[-1]
        return self.get_kappa(last_kappa)

    def to_cartesian(self, test):
        ss = np.cumsum([self.step] * len(test)) - self.step
        return frenet_to_cartesian(x0=0, y0=0, theta0=1.57, ss=ss, kappas=test)


class KappaGenerator(AbstractKappaGenerator):

    def __init__(self, length: int, variation: int = 0, low_step: float = 5.0, high_step: float = 15.0,
                 global_bound: float = 0.07, local_bound: float = 0.05):
        self.low_step = low_step
        self.high_step = high_step
        super().__init__(length=length, variation=variation, global_bound=global_bound, local_bound=local_bound)

    def get_step(self):
        return seeded_rng().uniform(self.low_step, self.high_step)

    def get_value(self, previous):
        last_kappa = 0
        if previous:
            last_kappa = previous[-1][0]
        return self.get_kappa(last_kappa), self.get_step()

    def to_cartesian(self, test):
        kappas, ss_deltas = zip(*test)
        ss = np.zeros(len(kappas))
        ss[1:] = np.cumsum(ss_deltas[0:-1])
        return frenet_to_cartesian(x0=0, y0=0, theta0=1.57, ss=ss, kappas=kappas)
