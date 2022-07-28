from roadsearch.generators.crossovers.crossovers import Crossover
from roadsearch.generators.exploiters.exploiters import Exploiter
from roadsearch.generators.mutators.mutations import ValueAlterationMutatorKappaStep, ValueAlterationMutator
from roadsearch.generators.representations.kappa_generator import FixStepKappaGenerator, KappaGenerator
from roadsearch.generators.representations.theta_generator import FixStepThetaGenerator, ThetaGenerator
from roadsearch.generators.representations.cartesian_generator import CatmullRomGenerator
from roadsearch.generators.representations.bezier_generator import BezierGenerator
from roadsearch.generators.virtual_road_generator import VirtualRoadsGenerator
import numpy as np

# Crossover setup
CROSS_FREQ = 30
CROSS_SIZE = 20


class TupleRoadGenerator(VirtualRoadsGenerator):
    def __init__(self, executor=None, map_size=None, generator=None, name=None, store_data=True):
        self.name = name

        if isinstance(generator, KappaGenerator):
            # Using special mutator for kappa+step generator because the last step is not used
            mutator = ValueAlterationMutatorKappaStep()
        else:
            mutator = ValueAlterationMutator()

        super().__init__(executor=executor, map_size=map_size,
                         random_budget_percentage=0.1,
                         strict_father=False,
                         generator=generator,
                         mutator=mutator,
                         exploiter=Exploiter(),
                         crossover=Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ),
                         store_data=store_data)

    # Quick hack to rename the generator when creating custom configurations
    def get_name(self):
        if self.name:
            return self.name
        else:
            return super().get_name()


# Generators that are represented with single variable arrays
class Frenetic(TupleRoadGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepKappaGenerator(
            length=25,
            variation=0,
            step=7.5,
            global_bound=0.07,
            local_bound=0.05
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class FreneticStep(TupleRoadGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = KappaGenerator(
            length=28,
            variation=0,
            low_step=0.5,
            high_step=16.16,
            global_bound=0.08,
            local_bound=0.05
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class TheTicStep(TupleRoadGenerator):
    def __init__(self, executor=None, map_size=None):
        step_mean = 9.47
        step_variance = 3.5
        generator = ThetaGenerator(
            length=19,
            variation=0,
            low_step=step_mean - step_variance,
            high_step=step_mean + step_variance,
            bound=np.pi/5,
            delta=np.pi/23
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class TheTic(TupleRoadGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = FixStepThetaGenerator(
            length=36,
            variation=0,
            step=5,
            bound=np.pi/8,
            delta=np.pi/44
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class DJGenerative(TupleRoadGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = CatmullRomGenerator(
            control_nodes=10,
            max_angle=50,
            seg_length=22.5,
            num_spline_nodes=10
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)


class Bezier(TupleRoadGenerator):
    def __init__(self, executor=None, map_size=None):
        generator = BezierGenerator(
            control_nodes=28,
            max_angle=40,
            seg_length=6.92,
            interpolation_nodes=9
        )
        super().__init__(executor=executor, map_size=map_size, generator=generator)
