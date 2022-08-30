import numpy as np
from roadsearch.generators.representations.cartesian_generator import (
    CatmullRomGenerator,
)
from roadsearch.generators.representations.kappa_generator import (
    FixStepKappaGenerator,
    KappaGenerator,
)
from roadsearch.generators.representations.theta_generator import (
    FixStepThetaGenerator,
    ThetaGenerator,
)
from roadsearch.generators.virtual_road_generator import VirtualRoadsGenerator

# Crossover setup
CROSS_FREQ = 30
CROSS_SIZE = 20

# Step sizes: distance between two nodes
FIX_STEP = 10.0
LOW_STEP = 5.0
HIGH_STEP = 15.0

# Number of nodes and variation in the length of the random generation
LENGTH = 20
VARIATION = 0

# Bounds for theta generation
BOUND = np.pi / 6
DELTA = np.pi / 8


# Generators that are represented with single variable arrays
class FreneticRandom20(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=20, variation=0, step=10.0)
        super().__init__(
            executor=executor, map_size=map_size, random_budget_percentage=1.0, strict_father=False, generator=generator
        )


# Generators that are represented with single variable arrays
class FreneticRandom40(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=40, variation=0, step=5.0)
        super().__init__(
            executor=executor, map_size=map_size, random_budget_percentage=1.0, strict_father=False, generator=generator
        )


# Generators that are purely random


class RandomGenerator(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None, generator=None):
        super().__init__(
            executor=executor, map_size=map_size, random_budget_percentage=1.0, strict_father=False, generator=generator
        )


class RandomFrenetic(RandomGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=LENGTH, variation=VARIATION, step=FIX_STEP)
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class RandomFreneticStep(RandomGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = KappaGenerator(length=LENGTH, variation=VARIATION, low_step=LOW_STEP, high_step=HIGH_STEP)
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class RandomTheTic(RandomGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepThetaGenerator(length=LENGTH, variation=VARIATION, step=FIX_STEP, bound=BOUND, delta=DELTA)
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class RandomTheTicStep(RandomGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = ThetaGenerator(
            length=LENGTH, variation=VARIATION, low_step=LOW_STEP, high_step=HIGH_STEP, bound=BOUND, delta=DELTA
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class RandomDJGenerator(RandomGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = CatmullRomGenerator(control_nodes=LENGTH, variation=VARIATION)
        super().__init__(executor=executor, map_size=map_size, generator=generator)
