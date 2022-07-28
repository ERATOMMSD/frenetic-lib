from frenetic.core.core import FreneticCore
from frenetic.core.mutation.exploiters.exploiters import SingleVariableExploiter
from frenetic.core.objective import MaxObjective
from frenetic.executors.mock import MockExecutor
from frenetic.representations.kappa_generator import FixStepKappaGenerator
from frenetic.executors.autonomoose.autonomoose import AutonomooseExecutor
from frenetic.frenetic import Frenetic
from frenetic.stopcriteria.counter import CountingStop
from frenetic.core.mutation.mutators.mutations import FreneticMutator
from frenetic.core.mutation.crossovers.crossovers import Crossover

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt='%H:%M:%S'
)


def run_example():
    representation = FixStepKappaGenerator(length=30, variation=5, step=10.0)

    # Crossover setup
    CROSS_FREQ = 30
    CROSS_SIZE = 20

    objective = MaxObjective(feature="acceleration", threshold=0.0)

    core = FreneticCore(representation=representation,
                        objective=objective,
                        mutator = FreneticMutator(representation),
                        exploiter = SingleVariableExploiter(),
                        crossover = Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ),
                        # min_oob_threshold = 1.0
                        )

    # normalizer = KappaNormalizer(global_bound=generator.global_bound,
    #                              local_bound=generator.local_bound),

    frenetic = Frenetic(core, MockExecutor(
        representation=representation,
        objective=objective,
        normalizer=None
    ), CountingStop(n_random=5, n_total=15))
    frenetic.start()
    frenetic.store_results("./sink/dev.json")

if __name__ == "__main__":
    run_example()