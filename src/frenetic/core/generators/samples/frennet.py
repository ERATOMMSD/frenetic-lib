from roadsearch.generators.virtual_road_generator import VirtualRoadsGenerator
from roadsearch.generators.representations.kappa_generator import FixStepKappaGenerator
from roadsearch.generators.exploiters.exploiters import SingleVariableExploiter
from roadsearch.generators.crossovers.crossovers import Crossover
from roadsearch.generators.mutators.frennet.model import FreNNetModel
from roadsearch.generators.mutators.mutations import FreNNetMutator

# Crossover setup
CROSS_FREQ = 30
CROSS_SIZE = 20


# Generators that are represented with single variable arrays
class FreNNet(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=40, variation=0, step=5.0)
        model = FreNNetModel(40, 40)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget_percentage=0.1,
                         strict_father=False,
                         generator=generator,
                         mutator=FreNNetMutator(model),
                         exploiter=SingleVariableExploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ),
                         model=model)


class FreNNet20(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=20, variation=0, step=10.0)
        model = FreNNetModel(20, 20)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget_percentage=0.1,
                         strict_father=False,
                         generator=generator,
                         mutator=FreNNetMutator(model),
                         exploiter=SingleVariableExploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ),
                         model=model)


class FreNNetSBST2022(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(length=20, variation=0, step=10.0)
        model = FreNNetModel(20, 20)
        super().__init__(executor=executor, map_size=map_size,
                         random_budget=3600,
                         min_oob_threshold=-0.5,
                         strict_father=False,
                         generator=generator,
                         mutator=FreNNetMutator(model),
                         exploiter=SingleVariableExploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ),
                         model=model)
