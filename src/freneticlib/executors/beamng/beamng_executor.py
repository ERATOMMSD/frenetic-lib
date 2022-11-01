# DISCLAIMER:
# Note, this code is an adaptation of the file code_pipeline/beamng_exectuor.py
# as provided by the CPS-Tool-Competition repository.
# https://github.com/sbft-cps-tool-competition/cps-tool-competition
#
# It has been licensed under the GNU General Public License.
# Thus, this file is also made available under GPL.

import logging
import subprocess

import time
import traceback
from typing import Tuple, Union, List, Dict

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from freneticlib.core.objective import AbstractObjective
from freneticlib.executors.normalizers.abstract_normalizer import AbstractNormalizer
from freneticlib.executors.outcome import Outcome
from freneticlib.representations.abstract_generator import RoadGenerator
from freneticlib.utils import geometry_utils

from shapely import geometry

import os.path

from freneticlib.executors.abstract_executor import AbstractExecutor

FloatDTuple = Tuple[float, float, float, float]

logger = logging.getLogger(__name__)

KMH_TO_MS_FACTOR = 0.277778

class BeamNGExecutor(AbstractExecutor):

    CALCULATED_FEATURES = [
        'timer',
        'pos',
        'dir',
        'vel',
        'steering',
        'steering_input',
        'brake',
        'brake_input',
        'throttle',
        'throttle_input',
        'wheelspeed',
        'vel_kmh',
        'is_oob',
        'oob_counter',
        'max_oob_percentage',
        'oob_distance',
        'oob_percentage',
    ]

    def __init__(
            self,
            representation: RoadGenerator,
            objective: AbstractObjective,
            normalizer: AbstractNormalizer = None,
            results_path: Union[str, Path] = None,
            cps_pipeline_path: Union[str, Path] = None,
            beamng_home=None, beamng_user=None,
            oob_tolerance: float = 0.95, max_speed_in_kmh: int = 70, risk_value: float = 0.7
            ):
        super().__init__(representation, objective, normalizer, results_path)

        cps_pipeline_path = Path(cps_pipeline_path).expanduser()
        print(cps_pipeline_path)
        assert cps_pipeline_path.exists(), "To use BeamNG Executor, please clone/download the CPS Tool Pipeline and pass the Path as argument."
        sys.path.append(str(cps_pipeline_path))  # add the pipeline path to sys.path so we can import/use the modules below


        # TODO This is specific to the TestSubject, we should encapsulate this better
        self.risk_value = risk_value

        self.oob_tolerance = oob_tolerance
        self.max_speed_in_kmh = max_speed_in_kmh

        self.brewer: 'BeamNGBrewer' = None
        self.pipeline_path = cps_pipeline_path
        self.beamng_home = Path(beamng_home).expanduser()
        self.beamng_user = Path(beamng_user).expanduser()
        assert self.beamng_user is not None

        # Runtime Monitor about relative movement of the car
        self.last_observation = None
        # Not sure how to set this... How far can a car move in 250 ms at 5Km/h
        self.min_delta_position = 1.0

    def _execute(self, test: List) -> Dict:
        logger.info(f"Executing test {test}")

        cartesian = self.representation.to_cartesian(test)
        original_line = geometry.LineString(np.array(cartesian))
        interpolated_points = geometry_utils.cubic_spline(original_line).xy
        beamng_format = [(x, y, -28., 8.0) for x, y in zip(*interpolated_points)]  # as shown in tests_generation.py

        # TODO Not sure why we need to repeat this 2 times...
        counter = 2

        attempt = 0
        sim = None
        condition = True
        while condition:
            attempt += 1
            if attempt == counter:
                test_outcome = "ERROR"
                description = 'Exhausted attempts'
                break
            if attempt > 1:
                self._close()
            if attempt > 2:
                time.sleep(5)

            sim = self._run_simulation(beamng_format)

            if sim.info.success:
                if sim.exception_str:
                    test_outcome = Outcome.FAIL
                    description = sim.exception_str
                else:
                    test_outcome = Outcome.PASS
                    description = 'Successful test'
                condition = False

        execution_data = sim.states
        if len(sim.states) > 0:
            features = sim.states[0]._asdict().keys()
            assert self.objective.feature in features, f"The feature ('{self.objective.feature}') is not recorded in the execution records. The records contain the following features:\n {sorted(features)}. \nBeamNG executor typically supports at least: \n {sorted(self.CALCULATED_FEATURES)}"

        val = pd.Series([rec._asdict()[self.objective.feature] for rec in sim.states], dtype=pd.Float64Dtype).aggregate(self.objective.aggregator)

        return {self.objective.feature: val, "outcome": test_outcome}

    def _is_the_car_moving(self, last_state):
        """ Check if the car moved in the past 10 seconds """

        # Has the position changed
        if self.last_observation is None:
            self.last_observation = last_state
            return True

        # If the car moved since the last observation, we store the last state and move one
        if geometry.Point(self.last_observation.pos[0], self.last_observation.pos[1]).distance(geometry.Point(last_state.pos[0], last_state.pos[1])) > self.min_delta_position:
            self.last_observation = last_state
            return True
        else:
            # How much time has passed since the last observation?
            if last_state.timer - self.last_observation.timer > 10.0:
                return False
            else:
                return True

    def _run_simulation(self, the_test) -> 'SimulationData':
        # we only use local imports, because we cannot be sure that the CPS Pipeline is actually available...
        from self_driving.beamng_brewer import BeamNGBrewer
        from self_driving.beamng_tig_maps import maps, LevelsFolder
        from self_driving.beamng_waypoint import BeamNGWaypoint
        from self_driving.simulation_data import SimulationDataRecord, SimulationData
        from self_driving.simulation_data_collector import SimulationDataCollector
        from self_driving.utils import get_node_coords, points_distance
        from self_driving.vehicle_state_reader import VehicleStateReader

        logger.debug("Running Simulation on BeamNG")
        if not self.brewer:
            logger.debug("Initialize new Brewer")
            self.brewer = BeamNGBrewer(beamng_home=self.beamng_home, beamng_user=self.beamng_user)
            self.vehicle = self.brewer.setup_vehicle()

        # For the execution we need the interpolated points
        # nodes = the_test.interpolated_points
        logger.debug("initialized")
        brewer = self.brewer
        brewer.setup_road_nodes(the_test)
        beamng = brewer.beamng
        waypoint_goal = BeamNGWaypoint('waypoint_goal', get_node_coords(the_test[-1]))

        # Note This changed since BeamNG.research
        beamng_levels = LevelsFolder(os.path.join(self.beamng_user, '0.26', 'levels'))
        maps.beamng_levels = beamng_levels
        maps.beamng_map = maps.beamng_levels.get_map('tig')
        maps.source_levels = LevelsFolder(str(self.pipeline_path / 'levels_template'))
        maps.source_map = maps.source_levels.get_map('tig')

        maps.install_map_if_needed()
        maps.beamng_map.generated().write_items(brewer.decal_road.to_json() + '\n' + waypoint_goal.to_json())

        vehicle_state_reader = VehicleStateReader(self.vehicle, beamng)
        brewer.vehicle_start_pose = brewer.road_points.vehicle_start_pose()

        steps = brewer.params.beamng_steps
        simulation_id = time.strftime('%Y-%m-%d--%H-%M-%S', time.localtime())
        simulation_name = f'beamng_executor/sim_{self.exec_counter}_{simulation_id}'
        sim_data_collector = SimulationDataCollector(self.vehicle, beamng, brewer.decal_road, brewer.params,
                                                     vehicle_state_reader=vehicle_state_reader,
                                                     simulation_name=simulation_name)
        # Patch the results path!
        if self.results_path:
            sd = sim_data_collector.simulation_data
            root = Path(self.results_path)
            sd.simulations: Path = root.joinpath('simulations')
            sd.path_root = sd.simulations.joinpath(simulation_name)
            sd.path_json = sd.path_root.joinpath('simulation.full.json')
            sd.path_partial = sd.path_root.joinpath('simulation.partial.tsv')
            sd.path_road_img = sd.path_root.joinpath('road')

        # TODO: Hacky - Not sure what's the best way to set this...
        sim_data_collector.oob_monitor.tolerance = self.oob_tolerance

        sim_data_collector.get_simulation_data().start()

        # TODO Make brewer a context manager that automatically closes everything
        logger.debug("Starting actual simulation")
        try:
            brewer.bring_up()

            brewer.vehicle.ai_set_aggression(self.risk_value)
            #  Sets the target speed for the AI in m/s, limit means this is the maximum value (not the reference one)
            brewer.vehicle.ai_set_speed(self.max_speed_in_kmh * KMH_TO_MS_FACTOR, mode='limit')
            brewer.vehicle.ai_drive_in_lane(True)
            brewer.vehicle.ai_set_waypoint(waypoint_goal.name)

            while True:
                sim_data_collector.collect_current_data(oob_bb=True)
                last_state: SimulationDataRecord = sim_data_collector.states[-1]
                # Target point reached
                if points_distance(last_state.pos, waypoint_goal.position) < 8.0:
                    break

                assert self._is_the_car_moving(last_state), "Car is not moving fast enough " + str(sim_data_collector.name)

                assert not last_state.is_oob, "Car drove out of the lane " + str(sim_data_collector.name)

                beamng.step(steps)

            sim_data_collector.get_simulation_data().end(success=True)
        except AssertionError as aex:
            # An assertion that trigger is still a successful test execution, otherwise it will count as ERROR
            sim_data_collector.get_simulation_data().end(success=True, exception=aex)
            traceback.print_exception(type(aex), aex, aex.__traceback__)
        except Exception as ex:
            sim_data_collector.get_simulation_data().end(success=False, exception=ex)
            traceback.print_exception(type(ex), ex, ex.__traceback__)
        finally:
            if self.results_path:
                sim_data_collector.save()
            try:
                sim_data_collector.take_car_picture_if_needed()
            except:
                pass

            # self.end_iteration()
            # TODO: better to close the simulator than to reuse it, as with the new version of BeamngPy the simulator
            #  gets stuck when the simulator restarts.
            self._close()

        return sim_data_collector.simulation_data

    def end_iteration(self):
        try:
            if self.brewer:
                self.brewer.beamng.stop_scenario()
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)

    def _close(self):
        if self.brewer:

            try:
                self.brewer.beamng.scenario.close()

                beamng_program_name = "BeamNG.tech.x64"
                cmd = "taskkill /IM \"{}.exe\" /F".format(beamng_program_name)
                ret = subprocess.check_output(cmd)

                output_str = ret.decode("utf-8")
            except Exception as ex:
                traceback.print_exception(type(ex), ex, ex.__traceback__)
            self.brewer = None

            logger.debug("Closing brewer, wait for 10 seconds to make sure everything is terminated.")
            # This is terrible. But I didn't find another way
            # wait for a few seconds to make sure everything is closed
            time.sleep(10)
