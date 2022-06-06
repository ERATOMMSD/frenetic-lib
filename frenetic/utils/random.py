import numpy as np

GLOBAL_RNG = None


def seeded_rng(seed=12345) -> np.random.Generator:
    """
    Note, once the seed is set, there is no reset.
    Thus, to set it, manually call it before any other function accesses.
    """
    global GLOBAL_RNG
    if GLOBAL_RNG is None:
        GLOBAL_RNG = np.random.default_rng(seed)
    return GLOBAL_RNG

