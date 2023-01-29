import logging

from freneticlib.core.core import FreneticCore
from freneticlib.core.mutation import exploiters, crossovers
from freneticlib.core.mutation.mutators import FreneticMutator
from freneticlib.core.objective import MaxObjective
from freneticlib.executors.bicycle.bicycleexecutor import BicycleExecutor
from freneticlib.executors.road_validator import RoadValidator
from freneticlib.frenetic import Frenetic
from freneticlib.representations.kappa_representation import FixStepKappaRepresentation
from freneticlib.stopcriteria.counter import CountingStop

# specify a logging format
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%H:%M:%S")


def run_example():
    # We want a FixStep Kappa representation
    representation = FixStepKappaRepresentation(length=30, variation=5, step=10.0)
    # alternative:
    # representation = CatmullRomRepresentation(control_nodes=30, variation=5)

    # Setup an objective. Here: maximize the distance_from_center (i.e. push the vehicle off the road)
    objective = MaxObjective(
        feature="distance_from_center",
        # every simulation produces 10 records per second, we extract the maximum value of the selected feature
        per_simulation_aggregator="max",
    )

    # Define the Frenetic core using representation, objective and the mutation operators
    core = FreneticCore(
        representation=representation,
        objective=objective,
        mutator=FreneticMutator(),
        crossover=crossovers.ChooseRandomCrossoverOperator(size=20),
    )

    # Define the Frenetic executor and the stop-criterion.
    frenetic = Frenetic(
        core,
        executor=BicycleExecutor(
            representation=representation,
            objective=objective,
            # results_path="./sink/detailed"
        ),
        CountingStop(n_random=50, n_total=250),
    )

    # If we wanted to extend a previous run, we could load the history like so:
    # frenetic.load_history("./data/dev.csv")

    # run the search
    frenetic.start()

    # store the history for later use
    frenetic.store_results("./data/history.csv")

    # Display the progress
    frenetic.plot("./data/plot.png")


if __name__ == "__main__":
    run_example()
