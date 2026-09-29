import json
import os
import tempfile
from tests.conftest import run_cli


def test_exclude_cols_report_success():
    # 1. Base run vs exclude-cols run: drops x2, updates ncols, retains other columns
    with tempfile.TemporaryDirectory() as tmp_base, tempfile.TemporaryDirectory() as tmp_excl:
        res_base = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--out-dir", tmp_base
        ])
        assert res_base.returncode == 0
        with open(os.path.join(tmp_base, "report.json"), "r", encoding="utf-8") as f:
            base_data = json.load(f)

        res_excl = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "x2",
            "--out-dir", tmp_excl
        ])
        assert res_excl.returncode == 0
        with open(os.path.join(tmp_excl, "report.json"), "r", encoding="utf-8") as f:
            excl_data = json.load(f)

        assert excl_data["input"]["excluded_columns"] == ["x2"]
        assert excl_data["input"]["ncols"] == base_data["input"]["ncols"] - 1
        profile_cols = [c["name"] for c in excl_data["profile"]["columns"]]
        assert "x2" not in profile_cols
        assert "grp" in profile_cols
        assert "y" in profile_cols


def test_exclude_cols_omitted_when_flag_not_used():
    # 2. When flag is omitted, excluded_columns key is absent from input provenance
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--out-dir", tmp
        ])
        assert res.returncode == 0
        with open(os.path.join(tmp, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "excluded_columns" not in data["input"]


def test_exclude_cols_role_column_error():
    # 3. Excluding a role column (target/prediction/group/time/subset) exits with code 2
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "y",
            "--out-dir", tmp
        ])
        assert res.returncode == 2
        assert "Error: --exclude-cols may not contain" in res.stderr


def test_exclude_cols_unknown_column_error():
    # 4. Unknown column name in exclude-cols exits with code 2
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "nope",
            "--out-dir", tmp
        ])
        assert res.returncode == 2
        assert "unknown columns" in res.stderr


def test_exclude_cols_empty_string_error():
    # 5. Empty exclude-cols string exits with code 2
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "",
            "--out-dir", tmp
        ])
        assert res.returncode == 2
        assert "at least one column name" in res.stderr


def test_exclude_cols_deduplication():
    # 6. Duplicate column names are deduplicated in order of appearance
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "x2,x2",
            "--out-dir", tmp
        ])
        assert res.returncode == 0
        with open(os.path.join(tmp, "report.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["input"]["excluded_columns"] == ["x2"]


def test_exclude_cols_determinism():
    # 7. Two runs with the same input, config and out-dir are byte-identical
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        res1 = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "x2",
            "--out-dir", tmp1
        ])
        res2 = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--exclude-cols", "x2",
            "--out-dir", tmp2
        ])
        assert res1.returncode == 0
        assert res2.returncode == 0

        with open(os.path.join(tmp1, "report.json"), "rb") as f1, open(os.path.join(tmp2, "report.json"), "rb") as f2:
            assert f1.read() == f2.read()

        with open(os.path.join(tmp1, "report.md"), "rb") as f1, open(os.path.join(tmp2, "report.md"), "rb") as f2:
            assert f1.read() == f2.read()


def test_exclude_cols_card_integration():
    # 8. Diagnostic card records excluded columns in card.json and card.md
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cli([
            "report",
            "--input", "tests/fixtures/leak_clean.csv",
            "--target-col", "y",
            "--card",
            "--exclude-cols", "x2",
            "--out-dir", tmp
        ])
        assert res.returncode == 0
        with open(os.path.join(tmp, "card.json"), "r", encoding="utf-8") as f:
            card_json = json.load(f)
        assert card_json["input"]["excluded_columns"] == ["x2"]

        with open(os.path.join(tmp, "card.md"), "r", encoding="utf-8") as f:
            card_md = f.read()
        assert "**Excluded columns:** x2" in card_md