"""Train comparable linear-regression and LightGBM price models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_FEATURES = [
    "size_sqm",
    "floor",
    "building_age_2018",
    "bedrooms",
    "living_rooms",
]
CATEGORICAL_FEATURES = ["district"]
TARGET = "price_wan"
RANDOM_STATE = 42
CV_FOLDS = 5


def set_plot_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    return {
        "mae_wan": float(mean_absolute_error(y_true, predictions)),
        "rmse_wan": float(mean_squared_error(y_true, predictions) ** 0.5),
        "r2": float(r2_score(y_true, predictions)),
    }


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical = Pipeline(
        [("impute", SimpleImputer(strategy="most_frequent")),
         ("onehot", OneHotEncoder(handle_unknown="ignore", drop="first"))]
    )
    return ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES),
         ("categorical", categorical, CATEGORICAL_FEATURES)]
    )


def build_models() -> dict[str, Pipeline]:
    """Return comparable pipelines with preprocessing contained in each fold."""
    return {
        "dummy_mean": Pipeline(
            [("preprocess", build_preprocessor()),
             ("model", DummyRegressor(strategy="mean"))]
        ),
        "linear_regression": Pipeline(
            [("preprocess", build_preprocessor()), ("model", LinearRegression())]
        ),
        "lightgbm": Pipeline(
            [
                ("preprocess", build_preprocessor()),
                ("model", lgb.LGBMRegressor(
                    n_estimators=400,
                    learning_rate=0.03,
                    num_leaves=31,
                    random_state=RANDOM_STATE,
                    verbosity=-1,
                )),
            ]
        ),
    }


def cross_validation_results(data: pd.DataFrame) -> pd.DataFrame:
    """Evaluate all models on the same deterministic five folds."""
    x = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = data[TARGET]
    folds = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scoring = {
        "mae_wan": "neg_mean_absolute_error",
        "rmse_wan": "neg_root_mean_squared_error",
        "r2": "r2",
    }
    rows = []
    for model_name, model in build_models().items():
        scores = cross_validate(model, x, y, cv=folds, scoring=scoring)
        for fold in range(CV_FOLDS):
            rows.append(
                {
                    "model": model_name,
                    "fold": fold + 1,
                    "mae_wan": -float(scores["test_mae_wan"][fold]),
                    "rmse_wan": -float(scores["test_rmse_wan"][fold]),
                    "r2": float(scores["test_r2"][fold]),
                }
            )
    return pd.DataFrame(rows)


def fit_models(
    data: pd.DataFrame,
) -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    x = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = data[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=RANDOM_STATE
    )

    models = build_models()
    dummy = models["dummy_mean"]
    linear = models["linear_regression"]
    lightgbm = models["lightgbm"]
    dummy.fit(x_train, y_train)
    dummy_predictions = dummy.predict(x_test)
    linear.fit(x_train, y_train)
    linear_predictions = linear.predict(x_test)

    lightgbm.fit(x_train, y_train)
    lightgbm_predictions = lightgbm.predict(x_test)

    result = {
        "dataset_rows": int(len(data)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "random_state": RANDOM_STATE,
        "dummy_mean": metrics(y_test, dummy_predictions),
        "linear_regression": metrics(y_test, linear_predictions),
        "lightgbm": metrics(y_test, lightgbm_predictions),
    }

    feature_names = linear.named_steps["preprocess"].get_feature_names_out()
    coefficients = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient_wan": linear.named_steps["model"].coef_,
        }
    ).sort_values("coefficient_wan", key=abs, ascending=False)
    importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": lightgbm.named_steps["model"].feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    predictions = pd.DataFrame(
        {
            "actual_price_wan": y_test.to_numpy(),
            "linear_prediction_wan": linear_predictions,
            "lightgbm_prediction_wan": lightgbm_predictions,
        }
    )
    return result, coefficients, importance, predictions


def save_prediction_chart(predictions: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True, sharey=True)
    upper = float(max(predictions.max()))
    for ax, column, title, color in [
        (axes[0], "linear_prediction_wan", "Linear regression", "#2864A8"),
        (axes[1], "lightgbm_prediction_wan", "LightGBM", "#D49A26"),
    ]:
        ax.scatter(predictions["actual_price_wan"], predictions[column], s=18, alpha=0.45, color=color, linewidths=0)
        positive = (predictions["actual_price_wan"] > 0) & (predictions[column] > 0)
        ax.clear()
        ax.scatter(predictions.loc[positive, "actual_price_wan"], predictions.loc[positive, column],
                   s=18, alpha=0.45, color=color, linewidths=0)
        lower = float(min(predictions.loc[positive, "actual_price_wan"].min(), predictions.loc[positive, column].min()))
        ax.plot([lower, upper], [lower, upper], color="#333333", linestyle="--", linewidth=1)
        ax.set(title=title, xlabel="Actual price (RMB 10,000; log scale)",
               ylabel="Predicted price (RMB 10,000; log scale)", xscale="log", yscale="log")
    fig.suptitle("Actual vs. predicted price on the fixed test set")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_residual_chart(predictions: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, column, title, color in [
        (axes[0], "linear_prediction_wan", "Linear regression", "#2864A8"),
        (axes[1], "lightgbm_prediction_wan", "LightGBM", "#D49A26"),
    ]:
        residuals = predictions["actual_price_wan"] - predictions[column]
        ax.scatter(predictions[column], residuals, s=18, alpha=0.4, color=color, linewidths=0)
        ax.axhline(0, color="#333333", linestyle="--", linewidth=1)
        ax.set(title=title, xlabel="Predicted price (RMB 10,000)",
               ylabel="Residual: actual - predicted (RMB 10,000)")
    fig.suptitle("Residuals on the fixed test set")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def price_band_errors(predictions: pd.DataFrame) -> pd.DataFrame:
    bands = pd.cut(predictions["actual_price_wan"], bins=[0, 300, 600, 1000, np.inf],
                   labels=["0-300", "300-600", "600-1000", "1000+"])
    rows = []
    for band in bands.cat.categories:
        mask = bands.eq(band)
        if not mask.any():
            continue
        for model, column in [("linear_regression", "linear_prediction_wan"),
                              ("lightgbm", "lightgbm_prediction_wan")]:
            rows.append({"price_band_wan": str(band), "model": model,
                         "n": int(mask.sum()),
                         "mae_wan": float(mean_absolute_error(
                             predictions.loc[mask, "actual_price_wan"], predictions.loc[mask, column]))})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/housing_clean.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/model_results"))
    parser.add_argument("--figure-dir", type=Path, default=Path("reports/figures"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.figure_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(args.input)
    set_plot_style()
    result, coefficients, importance, predictions = fit_models(data)
    cv = cross_validation_results(data)
    (args.output_dir / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    coefficients.to_csv(args.output_dir / "linear_coefficients.csv", index=False, encoding="utf-8-sig")
    importance.to_csv(args.output_dir / "lightgbm_feature_importance.csv", index=False, encoding="utf-8-sig")
    cv.to_csv(args.output_dir / "cross_validation_folds.csv", index=False, encoding="utf-8-sig")
    cv_summary = cv.groupby("model")[["mae_wan", "rmse_wan", "r2"]].agg(["mean", "std"])
    cv_summary.columns = [f"{metric}_{stat}" for metric, stat in cv_summary.columns]
    cv_summary.reset_index().to_csv(args.output_dir / "cross_validation_summary.csv", index=False, encoding="utf-8-sig")
    price_band_errors(predictions).to_csv(args.output_dir / "price_band_errors.csv", index=False, encoding="utf-8-sig")
    save_prediction_chart(predictions, args.figure_dir / "model_predictions.png")
    save_residual_chart(predictions, args.figure_dir / "residuals.png")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
