import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

"""
GLOBAL_RNG (np.random.Generator):
    A variable storing the globally set RNG.
    Defaults to None before first call to `seeded_rng`.
"""
GLOBAL_RNG = None


def seeded_rng(seed: int = None) -> np.random.Generator:
    """
    Once the seed is set, it is permanent, until you use `reset_rng` to reset.
    Thus, to set it, manually call it before any other function accesses.

    Args:
        seed (int): Which seed to use. If not, will use random seed.

    Returns:
        (np.random.Generator): The random number generator
    """
    global GLOBAL_RNG
    if GLOBAL_RNG is None:
        logger.info(f"Setting random seed to {seed}")
        GLOBAL_RNG = np.random.default_rng(seed)
    return GLOBAL_RNG


def reset_rng(seed: int = None) -> Optional[np.random.Generator]:
    """We might want to reset the RNG (for instance when testing)

    Args:
        seed (int, optional):
            If we want to reinitialise the RNG, then provide this value.
    Returns:
        (np.random.Generator, optional):
            The new random number generator, if seed was provided. Otherwise None.
    """
    global GLOBAL_RNG
    GLOBAL_RNG = None

    if seed is not None:  # if we provide a seed, then call seeded_rng()
        return seeded_rng(seed)
    else:
        return None
