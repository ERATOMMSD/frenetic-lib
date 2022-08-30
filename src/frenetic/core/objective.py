import abc
from typing import Union

import pandas as pd


class AbstractObjective(abc.ABC):

    def __init__(self, feature, per_simulation_aggregator: Union[callable, str, list, dict], threshold=None):
        self.feature = feature
        self.threshold = threshold
        self.aggregator = per_simulation_aggregator.strip()

        self.minimize = True

    def get_best(self, selection: pd.DataFrame) -> pd.Series:
        if len(selection) == 0:
            return None

        best = selection.sort_values(self.feature, ascending=self.minimize).iloc[0]
        return best

    @abc.abstractmethod
    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


class MaxObjective(AbstractObjective):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimize = False

    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.threshold:  # no threshold defined, return full df
            return df
        return df[df[self.feature] >= self.threshold]


class MinObjective(AbstractObjective):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimize = True

    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.threshold:  # no threshold defined, return full df
            return df
        return df[df[self.feature] <= self.threshold]
