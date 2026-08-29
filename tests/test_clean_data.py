import unittest

import pandas as pd

from src.clean_data import clean_dataframe, parse_layout


class CleanDataTests(unittest.TestCase):
    def test_parse_layout_with_and_without_living_room(self) -> None:
        self.assertEqual(parse_layout("3室2厅"), (3, 2))
        self.assertEqual(parse_layout("1室"), (1, 0))

    def test_clean_dataframe_deduplicates_and_builds_features(self) -> None:
        row = {
            "Floor": 10,
            "Garden": "示例小区",
            "Layout": "2室1厅",
            "Price": 500.0,
            "Region": "朝阳-望京-示",
            "Size": 100,
            "Year": 2008,
        }
        raw = pd.DataFrame([row, row])

        clean, summary = clean_dataframe(raw)

        self.assertEqual(len(clean), 1)
        self.assertEqual(summary["removed_exact_duplicate_rows"], 1)
        self.assertEqual(clean.iloc[0]["bedrooms"], 2)
        self.assertEqual(clean.iloc[0]["living_rooms"], 1)
        self.assertEqual(clean.iloc[0]["district"], "朝阳")
        self.assertEqual(clean.iloc[0]["building_age_2018"], 10)
        self.assertEqual(clean.iloc[0]["unit_price_yuan_sqm"], 50_000)

    def test_year_1900_is_treated_as_missing(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "Floor": 1,
                    "Garden": "示例小区",
                    "Layout": "1室",
                    "Price": 100.0,
                    "Region": "西城-天宁寺-示",
                    "Size": 20,
                    "Year": 1900,
                }
            ]
        )

        clean, summary = clean_dataframe(raw)

        self.assertTrue(pd.isna(clean.iloc[0]["construction_year"]))
        self.assertTrue(pd.isna(clean.iloc[0]["building_age_2018"]))
        self.assertEqual(summary["year_1900_treated_as_missing"], 1)

    def test_invalid_layout_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_layout("未知户型")


if __name__ == "__main__":
    unittest.main()
