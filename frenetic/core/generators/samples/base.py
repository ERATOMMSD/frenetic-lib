from roadsearch.generators.normalizers.kappa_normalizer import KappaNormalizer
from roadsearch.generators.virtual_road_generator import VirtualRoadsGenerator
from roadsearch.generators.representations.kappa_generator import FixStepKappaGenerator
from roadsearch.generators.mutators.mutations import ValueAlterationMutator, FreneticMutator
from roadsearch.generators.exploiters.exploiters import SingleVariableExploiter
from roadsearch.generators.crossovers.crossovers import Crossover
import numpy as np

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
BOUND = np.pi/6
DELTA = np.pi/8


# Generators that are represented with single variable arrays
class Frenetic(VirtualRoadsGenerator):
    def __init__(self, time_budget=3600, executor=None, map_size=None):
        step_size = 10.0
        max_length = 30
        length = int(min(map_size // step_size, max_length))
        generator = FixStepKappaGenerator(length=length, variation=5, step=step_size)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget=int(time_budget * 0.1),
                         strict_father=False,
                         generator=generator,
                         mutator=FreneticMutator(generator),
                         exploiter=SingleVariableExploiter(),
                         min_oob_threshold=1.0,
                         normalizer=KappaNormalizer(global_bound=generator.global_bound,
                                                    local_bound=generator.local_bound),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ))


# Generators that are represented with single variable arrays
class FreneticFine(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=40, variation=0, step=5)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget_percentage=0.1,
                         strict_father=False,
                         generator=generator,
                         mutator=ValueAlterationMutator(),
                         exploiter=SingleVariableExploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ))


