from unittest.mock import MagicMock

from frenetic.core.objective import MaxObjective
import pytest

from frenetic.executors.abstract_executor import Outcome
from frenetic.executors.autonomoose.autonomoose import  AutonomooseExecutor, geometry_utils
from shapely import geometry
import numpy as np

test = [(0,0), (0,50), (50,50), (75,100), (100, 100)]

@pytest.fixture
def centerline():
    original_line = geometry.LineString(np.array(test))
    return geometry_utils.cubic_spline(original_line)


@pytest.fixture
def anm_executor():
    return AutonomooseExecutor(per_simulation_aggregator="std",
                               representation=None,
                               objective=MaxObjective("throttle_cmd"),
                               normalizer=None)


class TestAutonomooseExecutor(object):

    def test_execute_run_scenario_fails(self, anm_executor):
        anm_executor.run_scenario = MagicMock(name="mutator", return_value=None)
        result_dict = anm_executor._execute(test)
        assert result_dict["outcome"] == Outcome.ERROR

    def test_create_scenario(self, anm_executor):
        original_line = geometry.LineString(np.array(test))
        interpolated_line = geometry_utils.cubic_spline(original_line)
        anm_executor.create_scenario(interpolated_line)

    def test_extract_data(self, anm_executor, centerline):
        extracted_data = anm_executor.extract_data("./sink/frenetic.bag", centerline)
        assert extracted_data[anm_executor.objective.feature] == 0.14090911723103883


    def test_extract_data_with_oob(self, anm_executor, centerline):
        anm_executor.road_width = 3
        extracted_data = anm_executor.extract_data("./sink/frenetic.bag", centerline)
        assert extracted_data[anm_executor.objective.feature] == 0.14090911723103883
        assert extracted_data["outcome"] == Outcome.FAIL

    def test_extract_data_without_oob(self, anm_executor, centerline):
        anm_executor.road_width = 5
        extracted_data = anm_executor.extract_data("./sink/frenetic.bag", centerline)
        assert extracted_data[anm_executor.objective.feature] == 0.14090911723103883
        assert extracted_data["outcome"] == Outcome.PASS