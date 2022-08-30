import pytest

from frenetic.core.core import FreneticCore
from frenetic.core.mutation.crossovers.crossovers import Crossover
from frenetic.core.mutation.exploiters.exploiters import SingleVariableExploiter, FirstVariableExploiter
from frenetic.core.mutation.mutators.mutations import FreneticMutator
from frenetic.core.objective import MaxObjective
from frenetic.executors.bicycle.bicycleexecutor import BicycleExecutor
from frenetic.frenetic import Frenetic
from frenetic.representations import kappa_generator, bezier_generator, cartesian_generator, theta_generator
from frenetic.stopcriteria.counter import CountingStop


@pytest.fixture
def objective():
    return


def get_frenetic(representation):
    objective = MaxObjective(feature="distance_from_center", per_simulation_aggregator="max")
    core = FreneticCore(representation=representation,
                        objective=objective,
                        mutator = FreneticMutator(representation),
                        exploiter = SingleVariableExploiter(),
                        crossover = Crossover(size=20, frequency=30)
                        )

    frenetic = Frenetic(core,
                        executor=BicycleExecutor(
                            representation=representation,
                            objective=objective,
                        ),
                        stop_criterion=CountingStop(n_random=50, n_total=200)
                        )
    return frenetic


class Test_RepresentationIntegration(object):
    """Integration tests (i.e. run for a while)."""

    def test_FixStepKappa(self):
        representation = kappa_generator.FixStepKappaGenerator(length=30, variation=5, step=10.0)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.df
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Kappa(self):
        representation = kappa_generator.KappaGenerator(length=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.df
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_FixStepTheta(self):
        representation = theta_generator.FixStepThetaGenerator(length=30, variation=5, step=10.0)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.df
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Theta(self):
        representation = theta_generator.ThetaGenerator(length=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.df
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Bezier(self):
        representation = bezier_generator.BezierGenerator(control_nodes=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.df
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Cartesian(self):
        representation = cartesian_generator.CatmullRomGenerator(control_nodes=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.core.exploiter = FirstVariableExploiter()
        frenetic.start()

        df = frenetic.core.df
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0