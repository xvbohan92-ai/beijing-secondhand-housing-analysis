"""Create a reproducible cleaned dataset from the raw Anjuke CSV."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


COL_RENAME = {
    "Floor": "floor",
    "Garden": "garden",
    "Layout": "layout",
    "Price": "price_wan",
    "Region": "region",
    "Size": "size_sqm",
    "Year": "construction_year",
}

EXPECTED_COLUMNS = list(COL_RENAME)
COLLECTION_YEAR = 2018


def parse_layout(value: str) -> tuple[int, int]:
    """Return bedroom and living-room counts from strings such as '3室2厅'."""
    match = re.fullmatch(r"(\d+)室(?:(\d+)厅)?", str(value).strip())
    if match is None:
        raise ValueError(f"Unsupported layout value: {value!r}")
    return int(match.group(1)), int(match.group(2) or 0)


def clean_dataframe(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Validate, deduplicate, and enrich the raw dataframe."""
    if raw.columns.tolist() != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected columns: {raw.columns.tolist()}; expected {EXPECTED_COLUMNS}"
        )

    summary = {
        "raw_rows": int(len(raw)),
        "raw_columns": int(raw.shape[1]),
        "missing_values": {key: int(value) for key, value in raw.isna().sum().items()},
        "extra_exact_duplicate_rows": int(raw.duplicated().sum()),
    }

    clean = raw.drop_duplicates().copy().rename(columns=COL_RENAME)

    layout_parts = clean["layout"].map(parse_layout)
    clean["bedrooms"] = layout_parts.str[0]
    clean["living_rooms"] = layout_parts.str[1]

    region_parts = clean["region"].str.split("-")
    clean["district"] = region_parts.str[0]
    clean["subdistrict"] = region_parts.str[1]

    clean["construction_year"] = clean["construction_year"].mask(
        clean["construction_year"].eq(1900)
    ).astype("Int64")
    clean["building_age_2018"] = (
        COLLECTION_YEAR - clean["construction_year"]
    ).astype("Int64")
    clean["unit_price_yuan_sqm"] = (
        clean["price_wan"] * 10_000 / clean["size_sqm"]
    ).round(2)

    summary.update(
        {
            "clean_rows": int(len(clean)),
            "removed_exact_duplicate_rows": int(len(raw) - len(clean)),
            "year_1900_treated_as_missing": int(raw["Year"].eq(1900).sum()),
            "district_count": int(clean["district"].nunique()),
        }
    )
    return clean, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("data/raw/anjuke.csv")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/housing_clean.csv")
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("data/processed/data_quality_summary.json"),
    )
    args = parser.parse_args()

    raw = pd.read_csv(args.input, encoding="utf-8")
    clean, summary = clean_dataframe(raw)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output, index=False, encoding="utf-8-sig")
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

