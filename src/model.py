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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
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


def fit_models(
    data: pd.DataFrame,
) -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    x = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = data[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=RANDOM_STATE
    )

    linear = Pipeline(
        [("preprocess", build_preprocessor()), ("model", LinearRegression())]
    )
    linear.fit(x_train, y_train)
    linear_predictions = linear.predict(x_test)

    lightgbm = Pipeline(
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
    )
    lightgbm.fit(x_train, y_train)
    lightgbm_predictions = lightgbm.predict(x_test)

    result = {
        "dataset_rows": int(len(data)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "random_state": RANDOM_STATE,
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
        (axes[0], "linear_prediction_wan", "线性回归", "#2864A8"),
        (axes[1], "lightgbm_prediction_wan", "LightGBM", "#D49A26"),
    ]:
        ax.scatter(predictions["actual_price_wan"], predictions[column], s=18, alpha=0.45, color=color, linewidths=0)
        ax.plot([0, upper], [0, upper], color="#333333", linestyle="--", linewidth=1)
        ax.set(title=title, xlabel="实际总价（万元）", ylabel="预测总价（万元）", xlim=(0, upper), ylim=(0, upper))
    fig.suptitle("测试集实际总价与预测总价")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


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
    (args.output_dir / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    coefficients.to_csv(args.output_dir / "linear_coefficients.csv", index=False, encoding="utf-8-sig")
    importance.to_csv(args.output_dir / "lightgbm_feature_importance.csv", index=False, encoding="utf-8-sig")
    save_prediction_chart(predictions, args.figure_dir / "model_predictions.png")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
