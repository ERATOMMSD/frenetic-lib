import ast
import logging as log
from time import sleep
from roadsearch.generators.abstract_generator import AbstractGenerator


class VirtualRoadsGenerator(AbstractGenerator):
    """
        Generates virtual roads to test a lane keeping system.
    """

    def __init__(self, executor=None, map_size=None,
                 generator=None, mutator=None, exploiter=None, crossover=None,
                 strict_father=True, random_budget=3600, random_budget_percentage=None,
                 min_oob_threshold=0.0, dynamic_threshold=False,
                 store_data=True,
                 normalizer=None,
                 model=None):

        # Only considering tests with a min_oob_distance < threshold for mutation (2.0 is the max_value)
        self.dynamic_threshold = dynamic_threshold
        self.min_oobd_threshold = min_oob_threshold
        self.min_length_to_mutate = 5
        self.max_visits = 10

        # Warnings when operators are None
        self.warn_if_none(crossover, "crossover")
        self.warn_if_none(mutator, "mutator")
        self.warn_if_none(exploiter, "exploiter")
        self.warn_if_none(normalizer, "normalizer")

        self.mutator = mutator
        self.exploiter = exploiter
        self.crossover = crossover
        self.normalizer = normalizer

        # Getting the time budget from the executors
        time_budget = executor.time_budget.time_budget if executor.time_budget.time_budget is not None else executor.time_budget.generation_budget
        self.random_gen_budget = random_budget_percentage * time_budget if random_budget_percentage else random_budget

        super().__init__(time_budget=time_budget, executor=executor, map_size=map_size,
                         generator=generator, strict_father=strict_father, store_data=store_data, model=model)

    def warn_if_none(self, var, name):
        if not var:
            log.warning(f"No {name} operator was chosen.")
            sleep(1)

    def start(self):
        self.generate_initial_population()
        self.feed_model()
        self.evolve()
        self.store_dataframe()
        sleep(10)

    def execute_test(self, test, method='random', info=None):
        if self.normalizer:
            test = self.normalizer.normalize(test)
        return super().execute_test(test, method, info)

    def execute_random(self):
        test = self.generator.generate()
        self.execute_test(test, method='random')

    def recalculate_threshold(self):
        if 'min_oob_distance' in self.df.columns:
            value = self.df[(self.df.outcome == 'PASS') | (self.df.outcome == 'FAIL')].min_oob_distance.quantile(0.25)
            # For progressing the bar shall not go down...
            if value < self.min_oobd_threshold:
                log.info(f'Min oob distance was updated: {value}')
                self.min_oobd_threshold = value
                sleep(5)

    def sample_random(self, size):
        for _ in range(size):
            self.execute_random()

    def generate_initial_population(self):
        log.info("Generating initial population...")
        while self.get_elapsed_time() < self.random_gen_budget:
            self.execute_random()
        return

    def mutator_defined(self, outcome):
        return (outcome == 'FAIL' and self.executor is not None) or (outcome == 'PASS' and self.mutator is not None)

    def get_best_parent(self):
        parent = None
        if len(self.df) > 0 and 'min_oob_distance' in self.df.columns:
            selection = self.select(max_visits=1)
            if len(selection) > 0:
                parent = selection.sort_values('min_oob_distance', ascending=True).head(1)
        return parent

    def evolve(self):
        # Iterating the tests according to the value of the min_oob_distance (closer to fail).
        log.info("Starting evolution...")
        self.executed_count = 0
        while self.is_time_available():

            parent = self.get_best_parent()

            if parent is not None and self.mutator_defined(parent.outcome.item()):
                log.info(f'Modifying a test ({parent.outcome.item()} with moobd {parent.min_oob_distance.item()})')
                self.df.at[parent.index[0], 'visited'] = 1
                self.mutate_test(parent)
            else:
                if self.model and len(self.all_pos) > self.batch_size:
                    self.feed_model()

                log.info('Obtaining a random candidate.')
                test = self.generator.generate()
                self.execute_test(test, method='random')
            if self.crossover and 0 < self.crossover.frequency <= self.executed_count:
                log.info('Entering recombination phase.')
                self.parents_recombination()
                self.executed_count = 0
                if self.dynamic_threshold:
                    self.recalculate_threshold()

    def get_parent_info(self, p_index):
        parent = self.df.iloc[p_index]
        return {'parent_1_index': p_index,
                'parent_1_outcome': parent['outcome'],
                'parent_1_min_oob_distance': parent['min_oob_distance'],
                'generation': parent['generation'] + 1}

    def mutate_test(self, parent):
        # Applying different operators depending on the outcome
        if self.exploiter and parent.outcome.item() == 'FAIL':
            self.perform_modifications(self.exploiter.get_all(), parent, stop_reproduction=True)
        elif self.mutator and parent.outcome.item() == 'PASS':
            self.perform_modifications(self.mutator.get_all(), parent)
        else:
            log.warning("No modification was applied because there is no exploiter nor mutator defined.")

    def select(self, max_visits):
        return self.df[((self.df.outcome == 'PASS') | (self.df.outcome == 'FAIL')) & (self.df.visited < max_visits) & (~self.df.test.isna()) & (self.df.min_oob_distance < self.min_oobd_threshold)]

    def select_candidates(self):
        candidates = {}
        if len(self.df) > 0 and 'min_oob_distance' in self.df.columns:
            selection = self.select(self.max_visits)
            if len(selection) > self.crossover.min_size:
                for index, candidate in selection.iterrows():
                    test = candidate['test']
                    if type(test) == str:
                        log.warning('Test was stored as a string value in the data frame.')
                        test = ast.literal_eval(test)
                    candidates[index] = (test, self.get_parent_info(index))
        if not candidates:
            log.warning('No candidates were selected during recombination phase.')
        return candidates

    def parents_recombination(self):
        candidates = self.select_candidates()
        if candidates:
            children = self.crossover.generate(candidates)
            while self.is_time_available() and len(children) > 0:
                child, method, info = children.pop()
                self.df.at[info['parent_1_index'], 'visited'] = self.df.iloc[info['parent_1_index']]['visited'] + 1
                self.df.at[info['parent_2_index'], 'visited'] = self.df.iloc[info['parent_2_index']]['visited'] + 1
                self.execute_test(child, method=method, info=info)

    def perform_modifications(self, functions, parent, stop_reproduction=False):
        # Only considering paths with more than 10 values for mutations
        # test might be empty if the parent was obtained from reversing road points
        test = parent.test.item()
        if test and len(test) >= self.min_length_to_mutate:
            i = 0
            while self.is_time_available() and i < len(functions):
                name, function = functions[i]
                log.info(f'Mutation function: {name}')
                modified_versions = function(test)
                if isinstance(modified_versions, dict):
                    suggestions = modified_versions
                else:
                    suggestions = {'standard': modified_versions}

                outcome = None
                for k, modified_test in suggestions.items():
                    info = self.get_parent_info(parent.index.item())
                    info['visited'] = 1 if stop_reproduction else 0
                    info['parameter'] = k
                    outcome = self.execute_test(modified_test, method=name, info=info)

                i += 1
                if outcome == 'FAIL':
                    # Stop mutating this parent when one of the children already produced a failure
                    break
