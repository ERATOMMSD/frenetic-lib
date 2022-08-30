import logging

import numpy as np

logger = logging.getLogger(__name__)

GLOBAL_RNG = None


def seeded_rng(seed=12345) -> np.random.Generator:
    """
    Note, once the seed is set, there is no reset.
    Thus, to set it, manually call it before any other function accesses.
    """
    global GLOBAL_RNG
    if GLOBAL_RNG is None:
        logger.info(f"Setting random seed to {seed}")
        GLOBAL_RNG = np.random.default_rng(seed)
    return GLOBAL_RNG


def reset_rng(seed=None) -> np.random.Generator:
    """
    We might want to reset the RNG (for instance when testing)
    :param seed: if we want to reinitialise it, then it should work here.
    :return:
    """
    global GLOBAL_RNG
    GLOBAL_RNG = None

    if seed is not None:  # if we provide a seed, then call seeded_rng()
        return seeded_rng(seed)
