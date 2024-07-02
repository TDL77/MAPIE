from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Tuple, Union

from mapie._typing import ArrayLike, NDArray


class EnsembleEstimator(metaclass=ABCMeta):
    """
    This class implements methods to handle the training and usage of the
    estimator. This estimator can be unique or composed by cross validated
    estimators.
    """

    @abstractmethod
    def fit(
        self,
        X: ArrayLike,
        y: ArrayLike,
        **kwargs
    ) -> EnsembleEstimator:
        """
        Fit the base estimator under the ``single_estimator_`` attribute.
        Fit all cross-validated estimator clones
        and rearrange them into a list, the ``estimators_`` attribute.
        Out-of-fold conformity scores are stored under
        the ``conformity_scores_`` attribute.
        """

    @abstractmethod
    def predict(
        self,
        X: ArrayLike,
        **kwargs,
    ) -> Union[NDArray, Tuple[NDArray, NDArray, NDArray]]:
        """
        Predict target from X. It also computes the prediction per train sample
        for each test sample according to ``self.method``.

        Parameters
        ----------
        X: ArrayLike of shape (n_samples, n_features)
            Test data.

        ensemble: bool
            Boolean determining whether the predictions are ensembled or not.
            If ``False``, predictions are those of the model trained on the
            whole training set.
            If ``True``, predictions from perturbed models are aggregated by
            the aggregation function specified in the ``agg_function``
            attribute.

            If ``cv`` is ``"prefit"`` or ``"split"``, ``ensemble`` is ignored.

            By default ``False``.

        return_multi_pred: bool
            If ``True`` the method returns the predictions and the multiple
            predictions (3 arrays). If ``False`` the method return the
            simple predictions only.

        **kwargs : dict
            Additional parameters.

        Returns
        -------
        Tuple[NDArray, NDArray, NDArray]
            - Predictions
            - The multiple predictions for the lower bound of the intervals.
            - The multiple predictions for the upper bound of the intervals.
        """
