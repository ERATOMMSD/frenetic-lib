from roadsearch.generators.normalizers.kappa_normalizer import KappaNormalizer
from roadsearch.generators.virtual_road_generator import VirtualRoadsGenerator
from roadsearch.generators.representations.kappa_generator import FixStepKappaGenerator
from roadsearch.generators.mutators.mutations import GaussianPushMutator
from roadsearch.generators.exploiters.exploiters import SingleVariableExploiter
from roadsearch.generators.crossovers.crossovers import Crossover

# Crossover setup
CROSS_FREQ = 30
CROSS_SIZE = 20


class FreneticPush(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=40, variation=0, step=5)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget_percentage=0.1,
                         strict_father=False,
                         generator=generator,
                         mutator=GaussianPushMutator(generator=generator),
                         normalizer=KappaNormalizer(global_bound=generator.global_bound,
                                                    local_bound=generator.local_bound),
                         exploiter=SingleVariableExploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ))


class FreneticPush20(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=20, variation=5, step=10)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget=3600,
                         strict_father=False,
                         generator=generator,
                         mutator=GaussianPushMutator(generator=generator),
                         normalizer=KappaNormalizer(global_bound=generator.global_bound,
                                                    local_bound=generator.local_bound),
                         exploiter=SingleVariableExploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ))
