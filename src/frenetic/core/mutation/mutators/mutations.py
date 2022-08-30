from abc import ABC, abstractmethod
from typing import Union

import numpy as np

from frenetic.utils.gaussian import gaussian_alteration
from frenetic.utils.random import seeded_rng


class AbstractMutator(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @staticmethod
    def get_test(parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        if isinstance(parent_info, dict):
            test = parent_info["test"]
        else:
            test = parent_info
        return test


class ListMutator(AbstractMutator):
    def __init__(self, generator):
        self.generator = generator
        self.min_length = 10

    def get_all(self):
        return [
            ("extend test with 1 to 5 new values", self.extend),
            ("randomly remove 1 to 5 values", self.randomly_remove_kappas),
            ("remove 1 to 5 values from front", self.remove_from_front),
            ("remove 1 to 5 values from tail", self.remove_from_tail),
            ("randomly replace 1 to 5 values", self.random_replacement),
        ]

    def remove_from_front(self, parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = self.get_test(parent_info)
        assert len(test) >= self.min_length
        return test[seeded_rng().integers(1, 5) :]

    def remove_from_tail(self, parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = self.get_test(parent_info)
        assert len(test) >= self.min_length
        return test[: -seeded_rng().integers(1, 5)]

    def randomly_remove_kappas(self, parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = self.get_test(parent_info)
        assert len(test) >= self.min_length
        # number of test to be removed
        k = seeded_rng().integers(1, 5)
        modified_test = test[:]
        while k > 0 and len(modified_test) > 5:
            # Randomly remove a kappa
            i = seeded_rng().integers(len(modified_test))
            del modified_test[i]
            k -= 1
        return modified_test

    def extend(self, parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = self.get_test(parent_info)
        modified_test = test[:]
        for i in range(seeded_rng().integers(1, 5)):
            # Randomly add a value
            modified_test.append(self.generator.get_value(modified_test))
        return modified_test

    def random_replacement(self, parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = self.get_test(parent_info)
        # Randomly replace values
        indices = seeded_rng().choice(len(test), seeded_rng().integers(1, 5), replace=False)
        modified_test = test[:]

        for i in indices:
            modified_test[i] = self.generator.get_value(modified_test[:i])
        return modified_test


class ValueAlterationMutator(AbstractMutator):
    def get_all(self):
        return [("alter the values by 0.9 ~ 1.1", self.random_alteration)]

    @staticmethod
    def random_alteration(parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = ValueAlterationMutator.get_test(parent_info)

        modified = False

        while not modified:
            modified_test = []

            for k in test:
                if type(k) == float:
                    if seeded_rng().random() < 0.1:
                        modified_test.append(k * seeded_rng().uniform(0.90, 1.1))
                        modified = True
                    else:
                        modified_test.append(k)
                elif type(k) == tuple:
                    mk = []
                    for v in k:
                        if seeded_rng().random() < 0.1:
                            mk.append(v * seeded_rng().uniform(0.90, 1.1))
                            modified = True
                        else:
                            mk.append(v)
                    modified_test.append(tuple(mk))
                else:
                    raise NotImplementedError("Method alteration is only implemented for floats or tuples of floats")

        return modified_test


class ValueAlterationMutatorKappaStep(AbstractMutator):
    def get_all(self):
        return [("alter the values by 0.9 ~ 1.1", self.random_alteration)]

    @staticmethod
    def random_alteration(parent_info: Union[dict, list[float]]) -> list[Union[float, tuple[float, float]]]:
        test = ValueAlterationMutator.get_test(parent_info)
        modified = False

        while not modified:
            modified_test = []
            for k in test[:-1]:
                mk = []
                for v in k:
                    if seeded_rng().random() < 0.1:
                        mk.append(v * seeded_rng().uniform(0.9, 1.1))
                        modified = True
                    else:
                        mk.append(v)
                modified_test.append(tuple(mk))

            kappa, step = test[-1]
            if seeded_rng().random() < 0.1:
                modified_kappa = kappa * seeded_rng().uniform(0.9, 1.1)
                modified_test.append((modified_kappa, step))
                modified = True
            else:
                modified_test.append((kappa, step))

        return modified_test


class FreNNetMutator(AbstractMutator):
    def __init__(self, model):
        self.model = model

    def get_all(self):
        return [("freNNetic alteration", self.frennetic_alteration)]

    def frennetic_alteration(self, parent_info: dict) -> dict[str, list[float]]:
        oob_distances = np.array(parent_info["oob_distances"])
        road = np.array(parent_info["road"])
        car_positions = parent_info["car_positions"]
        return self.model.suggestions(oob_distances, road, car_positions)


class GaussianPushMutator(ListMutator):
    def __init__(self, generator):
        super().__init__(generator)
        self.bound = generator.global_bound

    def get_all(self):
        return [("gaussian push", self.gaussian_push)]

    def gaussian_push(self, parent_info: dict) -> dict[str, list[float]]:
        test = parent_info["test"]

        result: dict[str, list[float]] = {}
        oob_distances = np.array(parent_info["oob_distances"])
        road = np.array(parent_info["road"])
        car_positions = parent_info["car_positions"]

        resampled_oobd = GaussianPushMutator._resample_oob_distances(
            oob_distances=oob_distances, road_points=road, car_positions=car_positions
        )

        center = np.where(resampled_oobd == np.amin(resampled_oobd))[0][0]

        min_std = 1
        max_std = 6

        for std in range(min_std, max_std):
            result[f"std-{std}-pos-0"] = gaussian_alteration(test, center, std_dev=float(std), bound=self.bound)

        for pos in range(1, 10):
            shifted_center = center - pos
            if shifted_center < 0:
                break
            result[f"std-1-pos-{pos}"] = gaussian_alteration(test, shifted_center, bound=self.bound)

        return result

    @staticmethod
    def _resample_oob_distances(
        oob_distances: np.array,
        road_points: np.array,
        car_positions: np.array,
    ) -> np.array:
        # TODO: Refactor (this method is also defied in freNNet model).
        indexes = [np.linalg.norm(car_positions - p, axis=-1).argmin() for p in road_points]
        return oob_distances[indexes]


class FreneticMutator(ListMutator):
    def get_all(self):
        return super().get_all() + [("alter the values by 0.9 ~ 1.1", ValueAlterationMutator.random_alteration)]
