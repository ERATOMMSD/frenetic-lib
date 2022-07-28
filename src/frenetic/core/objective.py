import abc
import pandas as pd


class AbstractObjective(abc.ABC):

    def __init__(self, feature, threshold=None):
        self.feature = feature
        self.threshold = threshold

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

    def __init__(self, feature, threshold=None):
        super().__init__(feature, threshold)
        self.minimize = False

    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.threshold:  # no threshold defined, return full df
            return df
        return df[df[self.feature] >= self.threshold]


class MinObjective(AbstractObjective):

    def __init__(self, feature, threshold=None):
        super().__init__(feature, threshold)
        self.minimize = True

    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.threshold:  # no threshold defined, return full df
            return df
        return df[df[self.feature] <= self.threshold]
