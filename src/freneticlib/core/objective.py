import abc
import logging
from typing import Callable, Dict, List, Union

import pandas as pd

from freneticlib.executors.outcome import Outcome

logger = logging.getLogger(__name__)


class AbstractObjective(abc.ABC):
    """Objective base class. Don't use."""

    def __init__(
        self,
        feature,
        per_simulation_aggregator: Union[Callable, str, List, Dict],
        threshold: float = None,
        dynamic_threshold_quantile: float = None,
    ):
        """
        Args:
            feature (str):
                The feature that should be optimised.
            per_simulation_aggregator (Union[Callable, str, List, Dict]): How to aggregate over a simulation's records.
                (see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.aggregate.html)
            threshold (float, optional):
                Only consider elements "better" than this. Defaults to None
            dynamic_threshold_quantile (float, optional):
                If set, specifies which quantile of values should be used for re-calculation of threshold.
        """
        self.feature = feature
        self.threshold = threshold
        self.aggregator = per_simulation_aggregator.strip()
        self.dynamic_threshold_quantile = dynamic_threshold_quantile

        self.minimize = True

    def get_best(self, df: pd.DataFrame) -> pd.Series:
        """Returns the row whose <feature> value is best (i.e. maximal or minimal).
        Args:
            df (pd.DataFrame): The execution history.

        Returns:
            (pd.Series): The best row.
        """
        if len(df) == 0:
            return None

        best = df.sort_values(self.feature, ascending=self.minimize).iloc[0]
        return best

    @abc.abstractmethod
    def recalculate_dynamic_threshold(self, df: pd.DataFrame):
        """Recalculates the dynamic threshold, if it is provided.

        Args:
            df (pd.DataFrame): The execution history.
        """
        pass

    @abc.abstractmethod
    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        """If threshold is specified, filters the dataframe to only contain rows where the feature value exceeds the threshold.

        Args:
            df (pd.DataFrame): The execution history.
        """
        pass


class MaxObjective(AbstractObjective):
    """For the specification to maximize a given feature."""

    def __init__(self, *args, **kwargs):
        """See `AbstractObject.__init__` for parameters."""
        super().__init__(*args, **kwargs)
        self.minimize = False

    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        """If threshold is specified, filters the dataframe to only contain rows where `self.feature` >= self.threshold.

        Args:
            df (pd.DataFrame): The execution history.
        """
        if not self.threshold:  # no threshold defined, return full df
            return df
        return df[df[self.feature] >= self.threshold]

    def recalculate_dynamic_threshold(self, df: pd.DataFrame):
        """Recalculates the dynamic threshold according to `self.dynamic_threshold_quantile` and updates it if the new value is higher than the previous threshold.

        Args:
            df (pd.DataFrame): The execution history.
        """
        if self.dynamic_threshold_quantile is not None:
            new_value = df[(df.outcome == Outcome.PASS) | (df.outcome == Outcome.FAIL)][self.feature].quantile(
                self.dynamic_threshold_quantile
            )
            # For progressing the bar shall not go down...
            if new_value > self.threshold:
                logger.info(f"Objective threshold was updated from {self.threshold} to {new_value}")
                self.threshold = new_value


class MinObjective(AbstractObjective):
    """For the specification to minimize a given feature."""

    def __init__(self, *args, **kwargs):
        """Constructor for MinObjective. Forwards arguments to `AbstractObjective`.

        Args:
            *args: Arguments that are forwarded to super constructor.
            **kwargs: KW-arguments that are forwarded to super constructor.
        """
        super().__init__(*args, **kwargs)
        self.minimize = True

    def filter_by_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        """If threshold is specified, filters the dataframe to only contain rows where `self.feature` <= self.threshold.

        Args:
            df (pd.DataFrame): The execution history.
        """
        if not self.threshold:  # no threshold defined, return full df
            return df
        return df[df[self.feature] <= self.threshold]

    def recalculate_dynamic_threshold(self, df: pd.DataFrame):
        """Recalculates the dynamic threshold according to `self.dynamic_threshold_quantile` and updates it if the new value is lower than the previous threshold.

        Args:
            df (pd.DataFrame): The execution history.
        """
        if self.dynamic_threshold_quantile is not None:
            new_value = df[(df.outcome == Outcome.PASS) | (df.outcome == Outcome.FAIL)][self.feature].quantile(
                self.dynamic_threshold_quantile
            )
            # For progressing the bar shall not go down...
            if new_value < self.threshold:
                logger.info(f"Objective threshold was updated from {self.threshold} to {new_value}")
                self.threshold = new_value
