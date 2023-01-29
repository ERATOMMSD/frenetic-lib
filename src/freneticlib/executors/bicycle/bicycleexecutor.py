import logging
from typing import Dict, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from shapely import geometry, ops

from freneticlib.executors.executor import Executor
from freneticlib.executors.outcome import Outcome
from freneticlib.utils import geometry_utils

from . import carlapidonbicycle as cpb

logger = logging.getLogger(__name__)


class BicycleExecutor(Executor):
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

    def _execute(self, test: List) -> Dict:
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
        assert self.objective.feature in records_df.columns, (
            f"The feature ('{self.objective.feature}') is not recorded in the execution records. The records contain the"
            f" following features:\n {sorted(records_df.columns.tolist())}. \nBicycle executor typically supports at least: \n"
            f" {sorted(self.CALCULATED_FEATURES)}"
        )
        val = records_df[self.objective.feature].aggregate(self.objective.aggregator)
        return_value = {self.objective.feature: val, "outcome": outcome}

        logger.debug(f"Value obtained from simulation: {return_value}")

        # store data
        if self.results_path:
            # Save the figures
            fig1, ax1 = plt.subplots()
            ax1.axis('equal')
            ax1.plot(*interpolated_line.xy, "--", "b")
            ax1.scatter(x=records_df["pxs"], y=records_df["pys"], color="red")
            fig1.tight_layout()
            fig1.savefig(self.results_path / f"road_{self.exec_counter}.png")

            fig1.clear()
            plt.close(fig1)

            # save the data records
            records_df.to_csv(self.results_path / f"sim_record_{self.exec_counter}.csv")

        return return_value
