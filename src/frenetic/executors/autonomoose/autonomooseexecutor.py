import os
import subprocess
from pathlib import Path
from typing import Union, Optional

import numpy as np

from frenetic.executors.abstract_executor import AbstractExecutor, Outcome

from pyproj import CRS, Transformer
from shapely import geometry, affinity, ops
import matplotlib.pyplot as plt

from . import geometry_utils, osm_utils, anm_rosbag
# from . import benchmark_wrapper

from .scenario_scaffolder import CopyScenarioScaffolder

import logging
logger = logging.getLogger(__name__)

class AutonomooseExecutor(AbstractExecutor):

    def __init__(self, per_simulation_aggregator: Union[callable, str, list, dict], *args, **kwargs):
        """
        :param aggregator: function, str, list, dict. Per-simulation aggregation of values.
            See https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.aggregate.html
        :param args: passed on to Executor.__init__(...)
        :param kwargs: passed on to Executor.__init__(...)
        """
        super().__init__(*args, **kwargs)
        self.road_width = 5
        self.store_result = True
        self.aggregator = per_simulation_aggregator.strip()

    def _execute(self, cartesian: list) -> dict:
        original_line = geometry.LineString(np.array(cartesian))
        interpolated_line = geometry_utils.cubic_spline(original_line)

        scen = self.create_scenario(centerline=interpolated_line)
        if (bagfile := self.run_scenario(scen)) is not None:
            return self.extract_data(bagfile=bagfile, centerline=interpolated_line)
        else:
            return dict(outcome=Outcome.ERROR)

    def create_scenario(self, centerline: geometry.LineString, scenario_name: str = "frenetic"):
        logger.debug(f"Creating scenario {scenario_name}")

        scaffolder = CopyScenarioScaffolder(new_scenario_name=scenario_name, new_map_name=f"{scenario_name}_lanelet2_map", SPEED_OVERRIDE=100)

        # calculate lanelet bounds and transform to GPS
        left_1st, left_2nd, right_1st, right_2nd, start, end, orientation = lane_to_lanelet_bounds(centerline, road_width=5)

        transformer = Transformer.from_crs(geometry_utils.WATERLOO_CRS, geometry_utils.GPS_CRS, always_xy=True)
        gps_left_1st = ops.transform(transformer.transform, left_1st)
        gps_left_2nd = ops.transform(transformer.transform, left_2nd)
        gps_right_1st = ops.transform(transformer.transform, right_1st)
        gps_right_2nd = ops.transform(transformer.transform, right_2nd)
        gps_start = ops.transform(transformer.transform, start)
        gps_end = ops.transform(transformer.transform, end)

        osmgen = osm_utils.Lanelet2_OSMGenerator()
        osmgen.create_lanelets(gps_left_1st, gps_left_2nd, gps_right_1st, gps_right_2nd)
        osmgen.write_to_file(scaffolder.new_map_osm_file)

        # use the scaffolder to create the scenario structure
        scaffolder.origin = (gps_start.x, gps_start.y)
        scaffolder.do_it()

        # create scenario files
        osm_utils.create_gpx(scaffolder.new_scenario_gpx_file,
                             (gps_start.x, gps_start.y),
                             (gps_end.x, gps_end.y))

        config_node = osm_utils.create_config_node(scaffolder.origin,  # config node position is Ego start!
                                              node_id=osmgen.newid,
                                              lanelet_map=scaffolder.new_map_name,
                                              scenario_name=scaffolder.new_scenario_name,
                                              id_generator=osmgen.newid,
                                              timeout=120)

        start_node = osm_utils.create_ego_start(scaffolder.origin, orientation=int(orientation), node_id=osmgen.newid)

        # abuse CR state_list for ANM trajectory !
        end_node = osm_utils.create_ego_goal((gps_end.x, gps_end.y), node_id=osmgen.newid)
        osm_utils.osm_write_to_file(scaffolder.new_scenario_osm_file, nodes=[config_node, start_node, end_node])

        return scenario_name

    def run_scenario(self, scenario_name, rosbag_path: str="~/rosbags") -> Optional[Union[Path,str]]:
        """
        :param scenario:
        :return: Optional[str] path to the rosbag file or None
        """
        logger.debug(f"Executing scenario {scenario_name}")
        bag_dir = Path(rosbag_path)
        bag_dir.expanduser().mkdir(exist_ok=True)
        bagfile = f"{scenario_name}_{self.exec_counter}.bag"

        call = f"""python3 {Path(__file__).parent}/ANMbenchmarks/bench.py scenario -b {(bag_dir / bagfile).expanduser()} "{scenario_name} -el" """

        (bag_dir / bagfile).expanduser().unlink(missing_ok=True)  # remove before execution

        p = subprocess.Popen([call], stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()

        if (bag_dir/bagfile).expanduser().exists():
            return bag_dir / bagfile
        else:
            import pdb; pdb.set_trace()
            logger.warning("The scenario didn't produce a bagfile.")
            return None


    def extract_data(self, bagfile: Union[Path,str], centerline: geometry.LineString):
        logger.debug(f"Extracting data from rosbag file {bagfile}")
        bagpath = Path(bagfile).expanduser()  # make sure it's a Path
        try:
            records_df = anm_rosbag.rosbag_to_sim_data(bagpath, centerline, road_width=self.road_width, store_result=True)
            records_df["is_oob"] = records_df.distance_from_center > (self.road_width/2)
            val = records_df[self.objective.feature].aggregate(self.aggregator)
            outcome = Outcome.FAIL if records_df.is_oob.any() else Outcome.PASS
        except:
            logger.error("Error during data extract.", exc_info=True)
            return {self.objective.feature: None, "outcome": Outcome.ERROR}

        return_value = {self.objective.feature: val, "outcome": outcome}
        logger.debug(f"Data extracted from rosbag: {return_value}")
        return return_value


def lane_to_lanelet_bounds(centerline: geometry.LineString, road_width: float):
    START_END_POINT_DISTANCE = 2

    first = ops.substring(centerline, start_dist=0, end_dist=0.5, normalized=True)
    second = ops.substring(centerline, start_dist=0.5, end_dist=1, normalized=True)

    # create two lanelets
    left_1st = geometry_utils.offset_left(first, road_width / 2)
    right_1st = geometry_utils.offset_right(first, road_width / 2)
    left_2nd = geometry_utils.offset_left(second, road_width / 2)
    right_2nd = geometry_utils.offset_right(second, road_width / 2)

    road_start = geometry.Point(centerline.interpolate(START_END_POINT_DISTANCE))  # start is
    road_end = geometry.Point(centerline.interpolate(-1 * START_END_POINT_DISTANCE))

    # if True:
    #     fig, ax = plt.subplots()
    #     ax.set_aspect('equal')
    #
    #     ax.plot(coordinates[:,0], coordinates[:,1], "--", c="k")
    #     ax.plot(*interpolated.xy, c="b")
    #
    #     # the first four are lines
    #     ax.plot(*left_1st.xy, c='g')
    #     ax.plot(*left_2nd.xy, c='r')
    #     ax.plot(*right_1st.xy, c='g')
    #     ax.plot(*right_2nd.xy, c='r')
    #
    #     ax.scatter(*road_start.xy, c='g')
    #     ax.scatter(*road_end.xy, c='r')
    #     plt.show()

    dx, dy = np.array([road_start.x, road_start.y]) - centerline.coords[0]
    orientation = 360 - np.degrees(np.arctan2(dy, dx))

    return left_1st, left_2nd, right_1st, right_2nd, road_start, road_end, orientation

