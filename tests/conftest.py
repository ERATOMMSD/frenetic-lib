import pytest

from freneticlib.utils import random

TEST_SEED = 54321


@pytest.fixture(autouse=True)
def reset_random():
    random.reset_rng(TEST_SEED)
    yield
    random.reset_rng()
