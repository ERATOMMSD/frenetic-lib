import click
from frenetic import frenetic

import logging

from frenetic.core.core import FreneticCore
from frenetic.core.mutation.exploiters.exploiters import SingleVariableExploiter
from frenetic.core.representations.kappa_generator import FixStepKappaGenerator
from frenetic.executors.mock import MockExecutor
from frenetic.frenetic import Frenetic
from frenetic.stopcriteria.counter import CountingStop

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt='%H:%M:%S'
)

cli = click.Group()

@cli.command("test")
def test():
    representation = FixStepKappaGenerator(length=30, variation=5, step=10.0)

    # Crossover setup
    CROSS_FREQ = 30
    CROSS_SIZE = 20

    from frenetic.core.mutation.mutators.mutations import FreneticMutator
    from frenetic.core.mutation.crossovers.crossovers import Crossover
    core = FreneticCore(representation=representation,
                        mutator = FreneticMutator(representation),
                        exploiter = SingleVariableExploiter(),
                        crossover = Crossover(size=CROSS_SIZE, frequency=CROSS_FREQ),
                        # min_oob_threshold = 1.0
                        )

    # normalizer = KappaNormalizer(global_bound=generator.global_bound,
    #                              local_bound=generator.local_bound),

    frenetic = Frenetic(core, MockExecutor(), CountingStop(n_random=25, n_total=75))
    frenetic.start()
    frenetic.store_results("./sink/dev.json")


if __name__ == "__main__":
    cli()