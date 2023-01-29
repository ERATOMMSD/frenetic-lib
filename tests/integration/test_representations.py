import pytest

from freneticlib.core.core import FreneticCore
from freneticlib.core.mutation import crossovers, exploiters, mutators
from freneticlib.core.objective import MaxObjective
from freneticlib.executors.bicycle.bicycleexecutor import BicycleExecutor
from freneticlib.frenetic import Frenetic
from freneticlib.representations import (
    bezier_representation,
    cartesian_representation,
    kappa_representation,
    theta_representation,
)
from freneticlib.stopcriteria.counter import CountingStop


@pytest.fixture
def objective():
    return


def get_frenetic(representation):
    objective = MaxObjective(feature="distance_from_center", per_simulation_aggregator="max")
    core = FreneticCore(
        representation=representation,
        objective=objective,
        mutator=mutators.FreneticMutator(),
        crossover=crossovers.ChooseRandomCrossoverOperator(size=20),
    )

    frenetic = Frenetic(
        core,
        executor=BicycleExecutor(
            representation=representation,
            objective=objective,
        ),
        stop_criterion=CountingStop(n_random=50, n_total=200),
    )
    return frenetic


class Test_RepresentationIntegration(object):
    """Integration tests (i.e. run for a while)."""

    def test_FixStepKappa(self):
        representation = kappa_representation.FixStepKappaRepresentation(length=30, variation=5, step=10.0)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.history
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Kappa(self):
        representation = kappa_representation.KappaRepresentation(length=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.history
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_FixStepTheta(self):
        representation = theta_representation.FixStepThetaRepresentation(length=30, variation=5, step=10.0)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.history
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Theta(self):
        representation = theta_representation.ThetaRepresentation(length=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.history
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    def test_Bezier(self):
        representation = bezier_representation.BezierRepresentation(control_nodes=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.start()

        df = frenetic.core.history
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0

    @pytest.mark.skip(reason="For some reason, Catmull Rom causes problems. Need to fix it eventually")
    def test_CatmullRomrepresentation(self):
        representation = cartesian_representation.CatmullRomRepresentation(control_nodes=30, variation=5)

        frenetic = get_frenetic(representation)
        frenetic.core.exploiter = exploiters.Exploiter()
        frenetic.start()

        df = frenetic.core.history
        assert len(df) == 200
        assert len(df[df.outcome == "ERROR"]) == 0
