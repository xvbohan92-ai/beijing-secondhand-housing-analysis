"""End-to-end smoke test using only the public synthetic dataset."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample" / "anjuke_synthetic.csv"


class PipelineSmokeTest(unittest.TestCase):
    def test_public_sample_runs_through_all_stages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            clean = temporary / "housing_clean.csv"
            summary = temporary / "quality.json"
            figures = temporary / "figures"
            model_results = temporary / "model_results"

            commands = [
                [sys.executable, str(ROOT / "src" / "clean_data.py"),
                 "--input", str(SAMPLE), "--output", str(clean),
                 "--summary", str(summary)],
                [sys.executable, str(ROOT / "src" / "explore.py"),
                 "--input", str(clean), "--output-dir", str(figures)],
                [sys.executable, str(ROOT / "src" / "model.py"),
                 "--input", str(clean), "--output-dir", str(model_results),
                 "--figure-dir", str(figures)],
            ]
            for command in commands:
                subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)

            self.assertTrue(summary.exists())
            self.assertTrue((model_results / "metrics.json").exists())
            self.assertTrue((model_results / "cross_validation_summary.csv").exists())
            self.assertTrue((figures / "model_predictions.png").exists())
            self.assertTrue((figures / "residuals.png").exists())


if __name__ == "__main__":
    unittest.main()
