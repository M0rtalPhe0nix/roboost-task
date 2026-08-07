from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from analysis.feasibility_analysis import reviewer_overlap, select_trends, theme_trends
from analysis.reconstruct_database import build_database


ROOT = Path(__file__).resolve().parents[1]


class DatabaseReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.database_path = Path(cls.temporary_directory.name) / "benchmark.sqlite"
        cls.result = build_database(ROOT / "Files", ROOT / "DATA_DICTIONARY.xlsx", cls.database_path)
        cls.connection = sqlite3.connect(cls.database_path)
        cls.connection.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()
        cls.temporary_directory.cleanup()

    def test_source_and_canonical_counts_are_reconciled(self) -> None:
        self.assertEqual(
            self.result["counts"],
            {
                "brands": 3,
                "branches": 157,
                "source_reviews": 15150,
                "unique_reviews": 15149,
                "exact_duplicate_reviews": 1,
                "menu_items": 180,
            },
        )

    def test_database_integrity_and_foreign_keys_pass(self) -> None:
        self.assertEqual(self.connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(self.connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        orphan_count = self.connection.execute(
            "SELECT COUNT(*) FROM reviews r LEFT JOIN branches b USING(branch_id) WHERE b.branch_id IS NULL"
        ).fetchone()[0]
        self.assertEqual(orphan_count, 0)

    def test_manifest_hashes_match_source_files(self) -> None:
        rows = self.connection.execute("SELECT file_name, sha256 FROM ingestion_manifest").fetchall()
        for row in rows:
            path = ROOT / "DATA_DICTIONARY.xlsx" if row["file_name"] == "DATA_DICTIONARY.xlsx" else ROOT / "Files" / row["file_name"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(row["sha256"], actual, row["file_name"])

    def test_data_dictionary_was_imported(self) -> None:
        counts = dict(self.connection.execute(
            "SELECT entity, COUNT(*) FROM data_dictionary_fields GROUP BY entity"
        ).fetchall())
        self.assertEqual(counts, {"branch": 22, "review": 29})
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM data_dictionary_files").fetchone()[0], 8)

    def test_reviewer_overlap_uses_inclusive_set_semantics(self) -> None:
        rows = reviewer_overlap(self.connection)
        pairs = {(row["brand_a"], row["brand_b"]): row for row in rows}
        self.assertEqual(pairs[("Lumen Coffee", "Solara Coffee")]["shared_reviewers"], 63)
        self.assertEqual(pairs[("Lumen Coffee", "Solara Coffee")]["pair_exclusive_reviewers"], 61)
        self.assertEqual(pairs[("Lumen Coffee", "Vera Coffee")]["shared_reviewers"], 30)
        self.assertEqual(pairs[("Solara Coffee", "Vera Coffee")]["shared_reviewers"], 65)

    def test_wait_proxy_reproduces_frozen_feasibility_result(self) -> None:
        wait = select_trends(theme_trends(self.connection), ["wait_time_complaint"])
        lumen = next(row for row in wait if row["brand"] == "Lumen Coffee")
        self.assertEqual((lumen["early_matches"], lumen["recent_matches"]), (23, 51))
        self.assertAlmostEqual(lumen["relative_change_percent"], 93.46, places=1)


class NotebookArtifactTests(unittest.TestCase):
    def test_notebook_is_executed_and_has_no_error_outputs(self) -> None:
        path = ROOT / "analysis/part2_pm_claim_feasibility.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(notebook["nbformat"], 4)
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertTrue(code_cells)
        self.assertTrue(all(cell["execution_count"] is not None for cell in code_cells))
        errors = [
            output for cell in code_cells for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        ]
        self.assertEqual(errors, [])

    def test_notebook_contains_all_six_claim_verdicts(self) -> None:
        notebook = json.loads((ROOT / "analysis/part2_pm_claim_feasibility.ipynb").read_text(encoding="utf-8"))
        content = "\n".join(cell["source"] for cell in notebook["cells"])
        for label in ("Claim (a)", "Claim (b)", "Claim (c)", "Claim (d)", "Claim (e)", "Claim (f)"):
            self.assertIn(label, content)


if __name__ == "__main__":
    unittest.main()
