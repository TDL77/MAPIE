from typing import Optional
import warnings

from sklearn.utils.multiclass import (check_classification_targets,
                                      type_of_target)

from .regression import BaseRegressionScore
from .classification import BaseClassificationScore
from .bounds import AbsoluteConformityScore
from .sets import APS, LAC, Naive, RAPS, TopK

from mapie._typing import ArrayLike


def check_regression_conformity_score(
    conformity_score: Optional[BaseRegressionScore],
    sym: bool = True,
) -> BaseRegressionScore:
    """
    Check parameter ``conformity_score`` for regression task.

    Raises
    ------
    ValueError
        If parameters are not valid.

    Examples
    --------
    >>> from mapie.conformity_scores.utils import (
    ...     check_regression_conformity_score
    ... )
    >>> try:
    ...     check_regression_conformity_score(1)
    ... except Exception as exception:
    ...     print(exception)
    ...
    Invalid conformity_score argument.
    Must be None or a ConformityScore instance.
    """
    if conformity_score is None:
        return AbsoluteConformityScore(sym=sym)
    elif isinstance(conformity_score, BaseRegressionScore):
        return conformity_score
    else:
        raise ValueError(
            "Invalid conformity_score argument.\n"
            "Must be None or a ConformityScore instance."
        )


def _check_depreciated(
    method: str
) -> None:
    """
    Check if the chosen method is outdated.

    Raises
    ------
    Warning
        If method is ``"score"`` (not ``"lac"``) or
        if method is ``"cumulated_score"`` (not ``"aps"``).
    """
    if method == "score":
        warnings.warn(
            "WARNING: Deprecated method. "
            + "The method \"score\" is outdated. "
            + "Prefer to use \"lac\" instead to keep "
            + "the same behavior in the next release.",
            DeprecationWarning
        )
    if method == "cumulated_score":
        warnings.warn(
            "WARNING: Deprecated method. "
            + "The method \"cumulated_score\" is outdated. "
            + "Prefer to use \"aps\" instead to keep "
            + "the same behavior in the next release.",
            DeprecationWarning
        )


def check_target(
    conformity_score: BaseClassificationScore,
    y: ArrayLike
) -> None:
    """
    Check that if the type of target is binary,
    (then the method have to be ``"lac"``), or multi-class.

    Parameters
    ----------
    conformity_score: BaseClassificationScore
        Conformity score function.

    y: NDArray of shape (n_samples,)
        Training labels.

    Raises
    ------
    ValueError
        If type of target is binary and method is not ``"lac"``
        or ``"score"`` or if type of target is not multi-class.
    """
    check_classification_targets(y)
    if type_of_target(y) == "binary" and not isinstance(conformity_score, LAC):
        raise ValueError(
            "Invalid method for binary target. "
            "Your target is not of type multiclass and "
            "allowed values for binary type are "
            f"{['score', 'lac']}."
        )


def check_classification_conformity_score(
    conformity_score: Optional[BaseClassificationScore] = None,
    method: Optional[str] = None,
) -> BaseClassificationScore:
    """
    Check parameter ``conformity_score`` for classification task.

    Raises
    ------
    ValueError
        If parameters are not valid.

    Examples
    --------
    >>> from mapie.conformity_scores.utils import (
    ...     check_classification_conformity_score
    ... )
    >>> try:
    ...     check_classification_conformity_score(1)
    ... except Exception as exception:
    ...     print(exception)
    ...
    Invalid conformity_score argument.
    Must be None or a ConformityScore instance.
    """
    allowed_methods = ['lac', 'naive', 'aps', 'raps', 'top_k']
    if method is not None:
        _check_depreciated(method)
        if method in ['score', 'lac']:
            return LAC()
        if method in ['cumulated_score', 'aps']:
            return APS()
        if method in ['naive']:
            return Naive()
        if method in ['raps']:
            return RAPS()
        if method in ['top_k']:
            return TopK()
        else:
            raise ValueError(
                f"Invalid method. Allowed values are {allowed_methods}."
            )
    elif isinstance(conformity_score, BaseClassificationScore):
        return conformity_score
    elif conformity_score is None:
        return LAC()
    else:
        raise ValueError(
            "Invalid conformity_score argument.\n"
            "Must be None or a ConformityScore instance."
        )
