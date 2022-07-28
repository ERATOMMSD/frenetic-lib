from unittest.mock import MagicMock
import pytest
import numpy as np

from frenetic.core.objective import MaxObjective
from frenetic.executors.abstract_executor import Outcome
from frenetic.executors.bicycleexecutor.bicycleexecutor import BicycleExecutor

test = [(0,0), (0,50), (50,50), (75,100), (100, 100)]

@pytest.fixture
def centerline():
    original_line = geometry.LineString(np.array(test))
    return geometry_utils.cubic_spline(original_line)


@pytest.fixture
def bic_executor():
    return BicycleExecutor(per_simulation_aggregator="std",
                               representation=None,
                               objective=MaxObjective("throttle_cmd"),
                               normalizer=None)

class TestAutonomooseExecutor(object):

    def test_execute(self, anm_executor):
        anm_executor.run_scenario = MagicMock(name="mutator", return_value=None)
        result_dict = anm_executor._execute(test)
        assert result_dict["outcome"] == Outcome.ERROR