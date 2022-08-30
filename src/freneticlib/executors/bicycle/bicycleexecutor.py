import logging

import numpy as np
import pandas as pd
from shapely import geometry, ops

from freneticlib.executors.abstract_executor import AbstractExecutor, Outcome
from freneticlib.utils import geometry_utils

from . import carlapidonbicycle as cpb

logger = logging.getLogger(__name__)


class BicycleExecutor(AbstractExecutor):
    # the features that the simplified bicycle model calculates. use them directly or calculate other values.
    CALCULATED_FEATURES = [
        "pxs",
        "pys",
        "speed",
        "acceleration",
        "jerk",
        "jerk_squared",
        "cost",
        "lat_acceleration",
        "lat_jerk",
        "lat_jerk_squared",
        "lat_cost",
        "heading",
        "heading_diffs",
        "steering_control",
        "throttle_control",
        "brake_control",
    ]

    def __init__(self, road_width: float = 5, target_speed: int = 50, dt: float = 0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.road_width = road_width
        self.target_speed = target_speed  # km/h
        self.dt = dt

    def _execute(self, test: list) -> dict:
        cartesian = self.representation.to_cartesian(test)

        original_line = geometry.LineString(np.array(cartesian))
        interpolated_line = geometry_utils.cubic_spline(original_line)

        # simulate
        data = cpb.execute_carla_pid_on_bicycle(
            *interpolated_line.xy,
            desired_speed=self.target_speed,
            dt=self.dt,
        )
        pts = []
        for i in range(len(data["pxs"])):
            pts.append(geometry.Point(data["pxs"][i], data["pys"][i]))
        data["points"] = pts

        # calculate distance from center line
        records_df = pd.DataFrame.from_dict(data, orient="index").T
        records_df["distance_from_center"] = records_df.points.apply(
            lambda p: geometry.LineString(ops.nearest_points(interpolated_line, p)).length
        )
        records_df["is_oob"] = records_df.distance_from_center > (self.road_width / 2)

        # compose the return value as outcome (pass / failed), val (the objective)
        outcome = Outcome.FAIL if records_df.is_oob.any() else Outcome.PASS
        val = records_df[self.objective.feature].aggregate(self.objective.aggregator)
        return_value = {self.objective.feature: val, "outcome": outcome}

        logger.debug(f"Value obtained from simulation: {return_value}")

        # store data
        if self.results_path:
            records_df.to_csv(self.results_path / f"sim_record_{self.exec_counter}.csv")

        return return_value
