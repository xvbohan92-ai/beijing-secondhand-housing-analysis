"""Generate publication-ready exploratory figures from the cleaned dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BLUE = "#2864A8"
GOLD = "#D49A26"


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def save_price_distribution(data: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.histplot(data=data, x="price_wan", bins=45, color=BLUE, edgecolor="white", ax=ax)
    ax.set(
        title="北京二手房总价分布",
        xlabel="总价（万元，对数坐标）",
        ylabel="房源数量",
        xscale="log",
    )
    fig.text(0.12, 0.02, f"样本：去重后 {len(data):,} 条房源；数据采集年份：2018", fontsize=9)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(output_dir / "price_distribution.png", dpi=180)
    plt.close(fig)


def save_district_ranking(data: pd.DataFrame, output_dir: Path) -> None:
    district = (
        data.groupby("district", as_index=False)
        .agg(median_unit_price=("unit_price_yuan_sqm", "median"), listings=("district", "size"))
        .sort_values("median_unit_price")
    )
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(district["district"], district["median_unit_price"], color=BLUE)
    ax.set(
        title="各区县二手房单位面积价格中位数",
        xlabel="单位面积价格中位数（元/平方米）",
        ylabel="",
        xlim=(0, district["median_unit_price"].max() * 1.15),
    )
    for y, (_, row) in enumerate(district.iterrows()):
        ax.text(row["median_unit_price"] + 1000, y, f"{row['median_unit_price']:,.0f}  n={int(row['listings'])}", va="center", fontsize=8)
    fig.text(0.12, 0.015, "北京周边作为数据中的独立地区保留；排序依据为中位数而非均值", fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(output_dir / "district_median_unit_price.png", dpi=180)
    plt.close(fig)


def save_size_price_relationship(data: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(data["size_sqm"], data["price_wan"], s=18, alpha=0.35, color=BLUE, linewidths=0)
    ax.set(
        title="建筑面积与总价关系",
        xlabel="建筑面积（平方米，对数坐标）",
        ylabel="总价（万元，对数坐标）",
        xscale="log",
        yscale="log",
    )
    fig.text(0.12, 0.02, f"每个点代表一条去重后的房源记录，n={len(data):,}", fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(output_dir / "size_vs_price.png", dpi=180)
    plt.close(fig)


def save_correlation_heatmap(data: pd.DataFrame, output_dir: Path) -> None:
    columns = ["price_wan", "size_sqm", "floor", "building_age_2018", "bedrooms", "living_rooms"]
    corr = data[columns].corr(method="spearman")
    labels = ["总价", "面积", "楼层", "房龄", "卧室数", "客厅数"]
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, vmin=-1, vmax=1,
                xticklabels=labels, yticklabels=labels, square=True, linewidths=0.5, ax=ax)
    ax.set_title("数值变量 Spearman 相关系数")
    fig.tight_layout()
    fig.savefig(output_dir / "correlation_heatmap.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/housing_clean.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/figures"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.input)
    set_style()
    save_price_distribution(data, args.output_dir)
    save_district_ranking(data, args.output_dir)
    save_size_price_relationship(data, args.output_dir)
    save_correlation_heatmap(data, args.output_dir)
    print(f"Generated 4 figures in {args.output_dir}")


if __name__ == "__main__":
    main()
