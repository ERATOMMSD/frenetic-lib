from frenetic.core.core import FreneticCore
from frenetic.core.mutation.exploiters import exploiters
from frenetic.core.objective import MaxObjective
from frenetic.executors.bicycle.bicycleexecutor import BicycleExecutor
from frenetic.representations.cartesian_generator import CatmullRomGenerator
from frenetic.representations.kappa_generator import FixStepKappaGenerator
from frenetic.frenetic import Frenetic
from frenetic.stopcriteria.counter import CountingStop
from frenetic.core.mutation.mutators.mutations import FreneticMutator
from frenetic.core.mutation.crossovers.crossovers import Crossover
from frenetic.utils.random import seeded_rng


import logging
# specify a logging format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt='%H:%M:%S'
)
def run_example():
    seeded_rng(54321)  # initialise the seed of our random number generator

    # We want a FixStep Kappa representation
    # representation = FixStepKappaGenerator(length=30, variation=5, step=10.0)
    representation = CatmullRomGenerator(control_nodes=30, variation=5)

    # Setup an objective. Here: maximize the distance_from_center (i.e. push the vehicle off the road)
    objective = MaxObjective(feature="distance_from_center",
                             # every simulation produces 10 records per second, we extract the maximum of this
                             per_simulation_aggregator="max"
                             )

    # Define the Frenetic core using representation, objective and the mutation operators
    core = FreneticCore(representation=representation,
                        objective=objective,
                        mutator = FreneticMutator(representation),
                        exploiter = exploiters.FirstVariableExploiter(),
                        crossover = Crossover(size=20, frequency=30)
                        )

    # Define the Frenetic executor and the stop-criterion.
    frenetic = Frenetic(core, BicycleExecutor(
        representation=representation,
        objective=objective,
        # results_path="./sink/detailed"
        ),
        CountingStop(n_random=1_000, n_total=10_000)
    )

    # run the search
    frenetic.start()


    # store the results for later use
    frenetic.store_results("./sink/dev.csv")

    # Display the progress
    frenetic.plot()



if __name__ == "__main__":
    run_example()