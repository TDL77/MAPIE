from typing import Union
import numpy as np
import pandas as pd
from sklearn.calibration import _SigmoidCalibration
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.base import RegressorMixin, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

from mapie.calibration import MapieCalibrator
from mapie.metrics import top_label_ece, expected_calibration_error
from inspect import signature
import pytest

random_state = 20

CALIBRATORS = [
    "sigmoid", "isotonic", _SigmoidCalibration(), LinearRegression()
]

ESTIMATORS = [
    LogisticRegression(),
    RandomForestClassifier(random_state=random_state),
]

results = {
    "y_score": [
        [0, 0.66666667, 0],
        [0.66666667, 0, 0],
        [0, 0.66666667, 0],
        [0, 0.66666667, 0],
        [0, 0.66666667, 0],
        [0, 0, 0.8],
        [0, 0, 0.8],
    ],
    "top_label_ece": 0.2888888888888889,
    "ece": 0.16480978061996931,
}


X, y = make_classification(
    n_samples=20,
    n_classes=3,
    n_informative=4,
    random_state=random_state
)

X_, X_test, y_, y_test = train_test_split(
    X, y, test_size=0.33, random_state=random_state
)
X_train, X_calib, y_train, y_calib = train_test_split(
    X_, y_, test_size=0.33, random_state=random_state
)


def test_initialized() -> None:
    """Test that initialization does not crash."""
    MapieCalibrator()


def test_default_parameters() -> None:
    """Test default values of input parameters."""
    mapie_cal = MapieCalibrator()
    assert mapie_cal.method == "top_label"
    assert mapie_cal.calibrator is None
    assert mapie_cal.cv == "split"


def test_default_fit_params() -> None:
    """Test default sample weights."""
    mapie_cal = MapieCalibrator()
    assert (
        signature(mapie_cal.fit).parameters["sample_weight"].default
        is None
    )
    assert (
        signature(mapie_cal.fit).parameters["calib_size"].default
        == 0.3
    )
    assert (
        signature(mapie_cal.fit).parameters["random_state"].default
        is None
    )
    assert (
        signature(mapie_cal.fit).parameters["shuffle"].default
        is True
    )
    assert (
        signature(mapie_cal.fit).parameters["stratify"].default
        is None
    )


def test_false_str_estimator() -> None:
    with pytest.raises(
        ValueError,
        match=r".*Please provide a valid string*",
    ):
        mapie_cal = MapieCalibrator(
            calibrator="not_estimator"
        )
        mapie_cal.fit(X, y)


def test_estimator_none() -> None:
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(X, y)
    assert mapie_cal.calibrator == "sigmoid"


def test_other_methods() -> None:
    with pytest.raises(
        ValueError,
        match=r".*No other methods have been*",
    ):
        mapie_cal = MapieCalibrator(method="no_method")
        mapie_cal.fit(X, y)


def test_not_seen_calibrator() -> None:
    with pytest.warns(
        UserWarning,
        match=r".*WARNING: This calibration was not previously seen*"
    ):
        mapie_cal = MapieCalibrator()
        mapie_cal.fit(X, y)
        mapie_cal.calibrators.clear()
        mapie_cal.predict_proba(X)


@pytest.mark.parametrize("calibrator", CALIBRATORS)
@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_shape_of_output(
    calibrator: Union[str, RegressorMixin],
    estimator: ClassifierMixin
) -> None:
    mapie_cal = MapieCalibrator(
        estimator=estimator,
        calibrator=calibrator,
    )
    mapie_cal.fit(X, y)
    calib_ = mapie_cal.predict_proba(X)
    assert calib_.shape == (len(y), mapie_cal.n_classes_)


def test_number_of_classes_equal_calibrators() -> None:
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(
        X=X_train,
        y=y_train,
        X_calib=X_calib,
        y_calib=y_calib
    )
    y_pred_calib_set = mapie_cal.estimator.predict(X=X_calib)
    assert len(mapie_cal.calibrators) == len(np.unique(y_pred_calib_set))


def test_same_predict() -> None:
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(
        X=X_train,
        y=y_train,
        X_calib=X_calib,
        y_calib=y_calib
    )
    y_pred_calib_set = mapie_cal.estimator.predict(X=X_test)
    y_pred_calibrated_test_set = mapie_cal.predict(X=X_test)
    np.testing.assert_allclose(y_pred_calib_set, y_pred_calibrated_test_set)


def test_correct_binary_ece_results() -> None:
    X_bin, y_comb = make_classification(
        n_samples=200000,
        n_classes=2,
        n_informative=4,
        random_state=random_state
    )
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(X_bin, y_comb)
    pred_ = mapie_cal.predict_proba(X_bin)
    ece_ = expected_calibration_error(pred_, y_comb)
    np.testing.assert_almost_equal(results["ece"], ece_, decimal=2)


def test_correct_results() -> None:
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(
        X=X_train,
        y=y_train,
        X_calib=X_calib,
        y_calib=y_calib
    )
    pred_ = mapie_cal.predict_proba(X_test)
    top_label_ece_ = top_label_ece(pred_, y_test)
    np.testing.assert_allclose(results["y_score"], pred_)
    np.testing.assert_allclose(results["top_label_ece"], top_label_ece_)


def test_correct_results_binary() -> None:
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(
        X=X_train,
        y=y_train,
        X_calib=X_calib,
        y_calib=y_calib
    )
    pred_ = mapie_cal.predict_proba(X_test)
    top_label_ece_ = top_label_ece(pred_, y_test)
    np.testing.assert_allclose(results["y_score"], pred_)
    np.testing.assert_allclose(results["top_label_ece"], top_label_ece_)


def test_different_binary_y_combinations() -> None:
    X_comb, y_comb = make_classification(
        n_samples=20,
        n_classes=3,
        n_informative=4,
        random_state=random_state
    )
    mapie_cal = MapieCalibrator()
    mapie_cal.fit(X_comb, y_comb)
    y_score = mapie_cal.predict_proba(X_comb)

    y_comb += 1
    mapie_cal1 = MapieCalibrator()
    mapie_cal1.fit(X_comb, y_comb)
    y_score1 = mapie_cal.predict_proba(X_comb)

    y_comb[np.where(y_comb == 2)[0]] = 3
    mapie_cal2 = MapieCalibrator()
    mapie_cal2.fit(X_comb, y_comb)
    y_score2 = mapie_cal.predict_proba(X_comb)
    np.testing.assert_array_almost_equal(y_score, y_score1)
    np.testing.assert_array_almost_equal(y_score, y_score2)


@pytest.mark.parametrize("calibrator", CALIBRATORS)
@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_results_with_constant_sample_weights(
    calibrator: Union[str, RegressorMixin],
    estimator: ClassifierMixin
) -> None:
    """
    Test predictions when sample weights are None
    or constant with different values.
    """
    n_samples = len(X)
    mapie_clf0 = MapieCalibrator(estimator=estimator, calibrator=calibrator)
    mapie_clf1 = MapieCalibrator(estimator=estimator, calibrator=calibrator)
    mapie_clf2 = MapieCalibrator(estimator=estimator, calibrator=calibrator)
    mapie_clf0.fit(X, y, sample_weight=None)
    mapie_clf1.fit(X, y, sample_weight=np.ones(shape=n_samples))
    mapie_clf2.fit(X, y, sample_weight=np.ones(shape=n_samples) * 5)
    y_pred0 = mapie_clf0.predict_proba(X)
    y_pred1 = mapie_clf1.predict_proba(X)
    y_pred2 = mapie_clf2.predict_proba(X)
    np.testing.assert_allclose(y_pred0, y_pred1)
    np.testing.assert_allclose(y_pred0, y_pred2)


def test_pipeline_compatibility() -> None:
    """Check that MAPIE works on pipeline based on pandas dataframes"""
    X = pd.DataFrame(
        {
            "x_cat": ["A", "A", "B", "A", "A", "B"],
            "x_num": [0, 1, 1, 4, np.nan, 5],
        }
    )
    y = pd.Series([0, 1, 2, 0, 1, 0])
    numeric_preprocessor = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="mean")),
        ]
    )
    categorical_preprocessor = Pipeline(
        steps=[
            ("encoding", OneHotEncoder(handle_unknown="ignore"))
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("cat", categorical_preprocessor, ["x_cat"]),
            ("num", numeric_preprocessor, ["x_num"])
        ]
    )
    pipe = make_pipeline(preprocessor, LogisticRegression())
    pipe.fit(X, y)
    mapie = MapieCalibrator(estimator=pipe)
    mapie.fit(X, y)
    mapie.predict(X)
