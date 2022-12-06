import logging
from pathlib import Path

from freneticlib.core.core import FreneticCore
from freneticlib.core.mutation import exploiters, crossovers
from freneticlib.core.mutation.mutators import FreneticMutator
from freneticlib.core.objective import MaxObjective
from freneticlib.executors.beamng.beamng_executor import BeamNGExecutor
from freneticlib.executors.bicycle.bicycleexecutor import BicycleExecutor
from freneticlib.frenetic import Frenetic
from freneticlib.representations.kappa_representation import FixStepKappaRepresentation
from freneticlib.stopcriteria.counter import CountingStop

# specify a logging format
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%H:%M:%S")


def run_example():
    # We want a FixStep Kappa representation
    representation = FixStepKappaRepresentation(length=30, variation=5, step=10.0)
    # representation = CatmullRomRepresentation(control_nodes=30, variation=5)

    # Setup an objective. Here: maximize the distance_from_center (i.e. push the vehicle off the road)
    objective = MaxObjective(
        feature="oob_percentage",  # BeamNG Executor
        # every simulation produces many records per second, we extract the maximum of this
        per_simulation_aggregator="max",
    )

    # Define the Frenetic core using representation, objective and the mutation operators
    core = FreneticCore(
        representation=representation,
        objective=objective,
        mutator=FreneticMutator(),
        exploiter=exploiters.Exploiter([
            exploiters.ReverseTest(),
            exploiters.SplitAndSwap(),
            exploiters.FlipSign()
        ]),
        crossover=crossovers.ChooseRandomCrossoverOperator(size=20),
    )

    # Define the Frenetic executor and the stop-criterion.
    frenetic = Frenetic(
        core,
        BeamNGExecutor(
            representation=representation,
            objective=objective,
            cps_pipeline_path=Path("~/cps-tool-competition"),
            results_path="./sink/detailed",
            beamng_home=str(Path("~/Downloads/BeamNG.tech.v0.26.1.0")),
            beamng_user=str(Path("~/BeamNG.tech").expanduser()),
        ),
        CountingStop(n_random=5, n_total=15),  # just a few, since simulation takes long
    )

    # run the search
    frenetic.start()

    # store the results for later use
    frenetic.store_results("./sink/dev.csv")

    # Display the progress
    frenetic.plot()


if __name__ == "__main__":
    run_example()
