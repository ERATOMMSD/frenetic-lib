"""
The FreNNet model
"""
__author__ = "Cédric Ho Thanh"

from pathlib import Path
from typing import List, Union, Dict
from roadsearch.utils.gaussian import gaussian_alteration

import keras
import numpy as np


class FreNNetModel:
    """
    The FreNNet model
    """

    EARLY_STOPPING_PATIENCE: int = 10
    """Patience for the early stopping callback."""

    MAX_EPOCHS: int = 800
    """Maximum number of epochs to train the model for on a single batch."""

    _all_kappas: np.array
    """All `kappas` ever fed to the model"""

    _all_oob_distances: np.array
    """All `oob_distances` (resampled) ever fed to the model."""

    _model: keras.Model
    """
    Standard model. Given a list of `oob_distance` values (i.e. essentially the
    behavior of the car), it predicts the `kappa` values that made the road.
    """

    _n_kappa_points: int
    """Number output `kappa` points the model outputs."""

    _n_road_points: int
    """Number of `oob_distance` points the model takes as input."""

    def __init__(self, n_road_points: int, n_kappa_values: int):
        """
        Args:
            n_road_points (int): Number of points in a road, which internally
                will be the expected number of input `oob_distance` points for
                the model.
            n_kappa_values (int): Expected number of output `kappa` points.
        """
        self._all_kappas = np.array(None)
        self._all_oob_distances = np.array(None)
        self._n_road_points = n_road_points
        self._n_kappa_points = n_kappa_values
        self._model = keras.Sequential(
            [
                keras.layers.Input(
                    name="input",
                    shape=(n_road_points),
                ),
                keras.layers.Dense(200, activation="relu", name="dense_1"),
                keras.layers.Dense(130, activation="relu", name="dense_2"),
                keras.layers.Dense(120, activation="relu", name="dense_3"),
                keras.layers.Dense(230, activation="relu", name="dense_4"),
                keras.layers.Dense(
                    n_kappa_values,
                    name="output",
                ),
            ],
        )
        self._model.compile(
            optimizer="nadam",
            loss="mean_absolute_error",
            # metrics=["accuracy"],
        )

    def _append_to_dataset(
            self,
            oob_distances: np.ndarray,
            kappas: np.ndarray,
    ):
        """
        Adds new entries to the dataset that the model has been fed so far.

        Args:
            oob_distances (np.ndarray): An (batch_size, n_road_points) array.
            kappas (np.ndarray): An (batch_size, n_kappa_values) array.
        """
        if not self._all_kappas.shape:
            self._all_kappas = kappas
        else:
            self._all_kappas = np.concatenate([self._all_kappas, kappas])
        if not self._all_oob_distances.shape:
            self._all_oob_distances = oob_distances
        else:
            self._all_oob_distances = np.concatenate(
                [self._all_oob_distances, oob_distances]
            )

    def _resample_oob_distances(
            self,
            oob_distances: np.array,
            road_points: np.array,
            car_positions: np.array,
    ) -> np.array:
        """
        In the output of a simulation, the length of the of `oob_distance` list
        is variable and not correlated to the length of the `kappa` list. This
        function resamples the former into a list of the same length as that of
        the road points.

        Warning:
            This function operates on a single simulation result at a time (it
            is NOT batched).

        Args:
            oob_distances (np.ndarray): The `oob_distance` sequence.
            road_points (np.ndarray): An (n_road_points, 2) array describing
                the roads points (in cartesial coordinates).
            car_positions (np.ndarray): An (?, 2) array describing the roads
                points (in cartesial coordinates).

        Returns:
            A new np.ndarray of `oob_distance` of shape (n_road_points, ).
        """
        if road_points.shape != (self._n_road_points, 2):
            raise ValueError(
                "Argument road_points should have shape "
                f"{(self._n_kappa_points, 2)}. Found {road_points.shape} "
                "instead."
            )
        # if oob_distances.shape[0] < self._n_road_points:
        #     raise ValueError(
        #         "Cannot upsample the oob_distance sequence: the oob_distances "
        #         f"argument has length {oob_distances.shape[0]}, should be at "
        #         f"least {self._n_road_points}."
        #     )
        indexes = [
            np.linalg.norm(car_positions - p, axis=-1).argmin()
            for p in road_points
        ]
        return oob_distances[indexes]

    def feed(
            self,
            oob_distances: List[np.ndarray],
            road_points: np.ndarray,
            car_positions: List[np.ndarray],
            kappas: np.ndarray,
    ) -> None:
        """
        Trains the model on a new set of simulation results. Automatically
        resamples the `oob_distance` sequences.

        In the even of a failed scenario (i.e. the car got off the lane), the
        simulation is terminated. This makes the resulting data unusable since
        it's basically truncated up to the point of failure. Therefore, only
        passing scenario results (i.e. where the car didn't crash) should be
        fed to the model.

        Args:
            oob_distances (List[np.ndarray]): A ragged tensor of `oob_distance`
                sequences (in List[np.ndarray] for ease of use). The
                length of the list (i.e. `len(oob_distances)`) should
                correspond to the `batch_size` of the other arguments.
            road_points (np.ndarray): A `(batch_size, n_road_points, 2)`
                array describing the roads points (in cartesial coordinates).
            car_positions (List[np.ndarray]): A list of length `batch_size`
                containing numpy arrays of shape `(?, 2)` array describing
                the car positions (in cartesial coordinates) in each scenario.
            kappas (np.ndarray): A `(batch_size, n_kappa_values)` array
                describing the roads of this batch.
        """
        zipped_results = zip(oob_distances, road_points, car_positions)
        resampled_oob_distances = []
        for oobd, rp, cp in zipped_results:
            resampled_oob_distances.append(
                self._resample_oob_distances(oobd, rp, cp),
            )
        resampled_oob_distances = np.array(resampled_oob_distances)
        self._append_to_dataset(resampled_oob_distances, kappas)
        self._model.fit(
            resampled_oob_distances,
            kappas,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor="loss",
                    patience=FreNNetModel.EARLY_STOPPING_PATIENCE,
                    restore_best_weights=True,
                ),
            ],
            epochs=FreNNetModel.MAX_EPOCHS,
        )

    def global_loss(self) -> float:
        """
        Returns the loss (MAE) of the model on its training dataset.
        """
        return self._model.evaluate(
            self._all_oob_distances,
            self._all_kappas,
        )

    @staticmethod
    def load(path: Union[str, Path]) -> "FreNNetModel":
        """
        Loads a FreNNetModel from a directory.
        """
        all_kappas = np.load(Path(path) / "kappas.npz")["arr_0"]
        all_oob_distances = np.load(Path(path) / "oob_distances.npz")["arr_0"]
        model = FreNNetModel(all_oob_distances.shape[1], all_kappas.shape[1])
        model._all_kappas = all_kappas
        model._all_oob_distances = all_oob_distances
        model._model = keras.models.load_model(Path(path) / "model.h5")
        return model

    def predict(self, oob_distances: np.ndarray) -> np.ndarray:
        """
        From a batch of `oob_distance` sequences, predicts the corresponding
        `kappa` value sequences.
        """
        return self._model(oob_distances)

    @staticmethod
    def _alter_oob_distances(arr, std_dev=1.0, size=20, bound=2.0):
        center = np.where(arr == np.amin(arr))[0][0]
        modified = gaussian_alteration(arr, center, std_dev=std_dev, size=size, bound=bound)
        return modified

    def suggest(self,
                oob_distances: np.array,
                road_points: np.array,
                car_positions: np.array,
                ) -> np.array:
        # TODO: Validate the shape
        resampled = self._resample_oob_distances(oob_distances=oob_distances,
                                                 road_points=road_points,
                                                 car_positions=car_positions)

        alt_oob_dist = self._alter_oob_distances(resampled)

        return self.predict(np.array([alt_oob_dist])).numpy()

    def suggestions(self,
                    oob_distances: np.array,
                    road_points: np.array,
                    car_positions: np.array,
                    ) -> Dict[str, List]:

        result = {}
        resampled = self._resample_oob_distances(oob_distances=oob_distances,
                                                 road_points=road_points,
                                                 car_positions=car_positions)

        for p in range(1, 6):
            alt_oob_dist = self._alter_oob_distances(resampled, std_dev=float(p), size=20, bound=2.0)
            result[f'std-{p}-pos-0'] = self.predict(np.array([alt_oob_dist])).numpy()[0].tolist()

        for p in range(1, 10):
            center = np.where(resampled == np.amin(resampled))[0][0] - p
            if center < 0:
                break
            alt_oob_dist = gaussian_alteration(resampled, center, std_dev=1.0, size=20, bound=2.0)
            result[f'std-1-pos-{p}'] = self.predict(np.array([alt_oob_dist])).numpy()[0].tolist()

        return result

    def save(self, output_directory: Union[str, Path]):
        """
        Saves the model and its training dataset to disk.
        """
        self._model.save(
            Path(output_directory) / "model.h5",
            save_format="h5",
        )
        np.savez_compressed(
            Path(output_directory) / "oob_distances.npz",
            self._all_oob_distances,
        )
        np.savez_compressed(
            Path(output_directory) / "kappas.npz",
            self._all_kappas,
        )
