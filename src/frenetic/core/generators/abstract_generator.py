from abc import ABC, abstractmethod
import logging as log
import numpy as np
import pandas as pd
import itertools as it
import os
import ast
from pathlib import Path

from time import sleep, time
from datetime import datetime

import sys

from roadsearch.anm.executors import AutonomooseExecutor

sys.path.append('../../sbst_beamng')

from code_pipeline.tests_generation import RoadTestFactory
from code_pipeline.executors import MockExecutor


class AbstractGenerator(ABC):

    def __init__(self, time_budget=None, executor=None, map_size=None, generator=None, strict_father=False, store_data=True, model=None):
        self.time_budget = time_budget
        self.executor = executor
        self.map_size = map_size
        self.generator = generator

        # Dataframe to store the results
        self.df = pd.DataFrame()
        if store_data:
            results_dir = '../sink/'
            if not os.path.exists(results_dir):
                os.mkdir(results_dir)
            creation_date = datetime.now().strftime('%Y%m%d-%H%M%S')
            self.file_name = f'{results_dir}{creation_date}-{self.get_name()}-results.csv'
            log.info(f'ERATO experiment output will be stored in {self.file_name}')
        else:
            self.file_name = None

        # update the results folder
        self.executor.result_folder = os.path.dirname((self.file_name))

        # Adding mutants for future mutation only if its min_oob_distance is better than its parent's min_oob_distance
        # min_oob_distance < parent_min_oob_distance
        self.strict_father = strict_father
        self.road_width = 10

        # Quick access stats
        self.stats = {'CANNOT_REFRAME': 0, 'PASS': 0, 'FAIL': 0, 'ERROR': 0, 'INVALID': 0}
        self.min_oob_distances = []
        self.executed_count = 0

        # Data structures for learning
        self.model = model
        self.all_kappas = []
        self.all_oob_distances = []
        self.all_pos = []
        self.all_roads = []
        self.batch_size = 30
        self.start_time = time()

    def load_data(self, filename):
        self.df = pd.read_csv(filename)
        self.df['oob_distances'] = self.df['oob_distances'].apply(lambda x: ast.literal_eval(x) if x is not np.nan else [])
        self.df['road'] = self.df['road'].apply(lambda x: ast.literal_eval(x) if x is not np.nan else [])
        self.df['test'] = self.df['test'].apply(lambda x: ast.literal_eval(x) if x is not np.nan else [])
        self.df['car_positions'] = self.df['car_positions'].apply(lambda x: ast.literal_eval(x) if x is not np.nan else [])

        if 'elapsed_time' in self.df.columns:
            self.start_time = self.start_time - self.df.iloc[-1]['elapsed_time']

        if self.model:
            self.all_kappas = list(self.df[self.df.outcome == 'PASS']['test'].apply(np.array))
            self.all_oob_distances = list(self.df[self.df.outcome == 'PASS']['oob_distances'].apply(np.array))
            self.all_pos = list(self.df[self.df.outcome == 'PASS']['car_positions'].apply(np.array))
            self.all_roads = list(self.df[self.df.outcome == 'PASS']['road'].apply(np.array))

    def clear_batch_feed(self):
        self.all_pos.clear()
        self.all_roads.clear()
        self.all_kappas.clear()
        self.all_oob_distances.clear()

    def feed_model(self):
        if len(self.all_oob_distances) > 0:
            log.info(f'Updating the model ({self.remaining_time()})')
            self.model.feed(oob_distances=self.all_oob_distances,
                            road_points=np.array(self.all_roads),
                            car_positions=self.all_pos,
                            kappas=np.array(self.all_kappas))
            self.clear_batch_feed()
            log.info(f'Finished updating the model ({self.remaining_time()})')
        else:
            log.info("No data to feed the model")

    @abstractmethod
    def start(self):
        pass

    def get_name(self):
        return self.__class__.__name__

    def reset(self):
        self.start_time = time()

    def get_elapsed_time(self):
        return time() - self.start_time

    def is_time_available(self):
        return not self.executor.is_over()

    def remaining_time(self):
        return self.executor.time_budget.get_remaining_real_time()

    def store_dataframe(self):
        if self.file_name:
            log.info("Storing the all the experiment results in a csv.")
            # Storing the results as csv in sink folders
            with open(self.file_name, 'w') as outfile:
                self.df.to_csv(outfile)
        else:
            log.info("Data is not being a stored in a file.")

    def execute_test(self, test, method='random', info=None):
        log.info(f"Remaining time: {self.remaining_time()}")
        log.info('Transforming the test into road points')
        road_points = self.generator.to_cartesian(test)

        log.info("Re-framing the road")
        road_points = self.reframe_road(road_points)
        if not road_points:
            self.stats['CANNOT_REFRAME'] += 1
            return 'CANNOT_REFRAME'

        log.info("Generated test using: %s", road_points)
        the_test = RoadTestFactory.create_road_test(road_points)

        # Try to execute the test (removed: , additional_info={'test': test, 'method': method})
        test_outcome, description, execution_data = self.executor.execute_test(the_test)

        # Print the result from the test and continue
        log.info("test_outcome %s", test_outcome)
        log.info("description %s", description)
        # Adding the info of the results to the summary
        self.stats[test_outcome] += 1

        test_info = {'test': test,
                     'outcome': test_outcome,
                     'description': description,
                     'road': road_points,
                     'method': method,
                     'visited': 0,
                     'generation': 0,
                     'elapsed_time': self.get_elapsed_time()}

        if info:
            test_info.update(info)

        if test_outcome == 'ERROR':
            log.info("There as an ERROR in the simulator. Current test was not properly executed.")
            # restarting the simulator (assuming BeamNG simulator)
            self.restart_simulator()
            # adding data to the dataframe when there was a simulator error
            self.df = self.df.append(test_info, ignore_index=True)
            return test_outcome

        # Storing the data in a dataframe for next phase
        if execution_data:
            # base metrics
            #self.add_all_metrics(execution_data, test_info)
            self.add_metric_info(execution_data, min, 'oob_distance', test_info)
            test_info['max_oob_percentage'] = execution_data[-1].max_oob_percentage
            test_info['last_pos'] = execution_data[-1].pos
            oob_distances = self.get_metric_data(execution_data, 'oob_distance')
            test_info['oob_distances'] = oob_distances
            car_positions = [(x, y) for (x, y, z) in self.get_metric_data(execution_data, 'pos')]
            test_info['car_positions'] = car_positions

            # updating the recent count of executed tests
            self.executed_count += 1
            self.min_oob_distances.append(test_info['min_oob_distance'])

            # adding data to feed the model
            if test_outcome == 'PASS' and self.model:
                self.all_oob_distances.append(np.array(oob_distances))
                self.all_roads.append(np.array(road_points))
                self.all_kappas.append(np.array(test))
                self.all_pos.append(np.array(car_positions))

            # complex metrics
            accum_neg_oob = self.accumulated_negative_oob(execution_data)
            test_info['accum_neg_oob'] = accum_neg_oob

            # avoid visiting mutants that perform worst than its parents
            if self.strict_father and (('parent_1_min_oob_distance' in test_info and
                                        test_info['min_oob_distance'] > test_info['parent_1_min_oob_distance']) or
                                       ('parent_2_min_oob_distance' in test_info and
                                        test_info['min_oob_distance'] > test_info['parent_2_min_oob_distance'])):
                test_info['visited'] = 1
                log.info('Weaker mutant: Disabling current test for future mutations.')

            # Retrieving file name
            # if not isinstance(self.executors, (MockExecutor, AutonomooseExecutor)):
            #     last_file = sorted(Path('simulations/beamng_executor').iterdir(), key=os.path.getmtime)[-1]
            #     test_info['simulation_file'] = last_file.name

            # Logging some test_info for debugging
            log.info('Min oob_distance: {:0.3f}'.format(test_info['min_oob_distance']))
            log.info('Accumulated negative oob_distance: {:0.3f}'.format(accum_neg_oob))

        self.df = self.df.append(test_info, ignore_index=True)

        # Updating dataframe when having new valid tests.
        if test_info['outcome'] == 'PASS' or test_info['outcome'] == 'FAIL':
            self.store_dataframe()

        if self.executor.road_visualizer:
            sleep(5)
        return test_outcome

    def add_all_metrics(self, execution_data, test_info):
        metrics = ['steering', 'steering_input', 'brake', 'brake_input', 'throttle', 'throttle_input',
                   'wheelspeed', 'vel_kmh', 'oob_counter', 'oob_distance']
        functions = [np.max, np.min, np.mean, np.average]
        for metric,  func in it.product(metrics, functions):
            self.add_metric_info(execution_data, func, metric, test_info)

    @staticmethod
    def add_metric_info(execution_data, func, metric, test_info):
        metric_data = AbstractGenerator.get_metric_data(execution_data, metric)
        if metric_data:
            test_info['{:s}_{:s}'.format(func.__name__, metric)] = func(metric_data)

    @staticmethod
    def get_metric_data(execution_data, metric):
        metric_data = [y for y in map(lambda x: getattr(x, metric), execution_data) if y is not None]
        return metric_data

    def restart_simulator(self):
        if isinstance(self.executor, MockExecutor):
            log.info("Mock Executor does not need to be restarted.")
        else:
            pass
            # from code_pipeline.beamng_executor import BeamngExecutor
            # log.info("Restarting the simulator.")
            # beamng_home = self.executors.beamng_home
            # beamng_user = self.executors.beamng_user
            # time_budget = self.executors.time_budget
            # map_size = self.map_size
            # road_visualizer = self.executors.road_visualizer
            # start_time = self.executors.start_time
            # stats = self.executors.stats
            # result_folder = self.executors.result_folder
            # try:
            #     self.executors.close()
            # except Exception:
            #     log.info("There was en exception while restarting the simulator.")
            #     pass
            # self.executors = BeamngExecutor(beamng_home=beamng_home, beamng_user=beamng_user, time_budget=time_budget,
            #                                map_size=map_size, road_visualizer=road_visualizer,
            #                                result_folder=result_folder)
            # # setting the start time to the original time
            # self.executors.start_time = start_time
            # self.executors.stats = stats

    @staticmethod
    def accumulated_negative_oob(execution_data):
        """
        Note: Normalizing oob_distance to be negative.
        Default interval: [-2, 2] --> Normalized interval: [-4, 0]
        Args:
            execution_data: execution data from the simulator
        Returns:
            Accumulated oob_distance when the center the mass already crossed one of the lanes (oob_distance < 0).
        """
        return (sum(
            map(lambda k: (execution_data[k].oob_distance - 2) * (execution_data[k].timer - execution_data[k - 1].timer)
            if execution_data[k].oob_distance < 0 else 0, range(1, len(execution_data)))))

    def reframe_road(self, road_points):
        """
        Args:
            road_points = [(x, y)...]: list of cartesian coordinates
        Returns:
            A representation of the road that fits the map size (when possible).
        """

        xs, ys = zip(*road_points)

        min_xs = min(xs)
        min_ys = min(ys)
        road_width = self.road_width  # TODO: How to get the exact road width?
        if (max(xs) - min_xs + road_width > self.map_size - self.road_width) \
                or (max(ys) - min_ys + road_width > self.map_size - self.road_width):
            log.info("Cannot re-frame the road. Skipping this test.")
            return None
            # TODO: Fail the entire test and start over
        xs = list(map(lambda x: x - min_xs + road_width, xs))
        ys = list(map(lambda y: y - min_ys + road_width, ys))
        return list(zip(xs, ys))
