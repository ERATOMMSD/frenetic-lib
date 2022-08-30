import numpy as np

from freneticlib.utils import random
from tests import conftest


def test_set_reset():
    """Check whether set and reset work."""
    random_ints = random.seeded_rng(conftest.TEST_SEED).integers(100, size=10)

    # reset, then set again
    random.reset_rng()
    assert random.GLOBAL_RNG is None
    np.testing.assert_array_equal(random_ints, random.seeded_rng(conftest.TEST_SEED).integers(100, size=10))

    # reset to new see ddirectly
    np.testing.assert_array_equal(random_ints, random.reset_rng(conftest.TEST_SEED).integers(100, size=10))
