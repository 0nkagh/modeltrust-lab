import json
import os
import tempfile
from tests.conftest import run_cli
import pandas as pd
from modeltrust.report import build_report_md

def test_report_files_created_and_canonical():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        assert res.returncode == 0
        
        json_path = os.path.join(tmpdir, "report.json")
        md_path = os.path.join(tmpdir, "report.md")
        
        assert os.path.exists(json_path)
        assert os.path.exists(md_path)
        
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            
        assert "schema" in data
        assert "profile" in data
        assert "leakage" in data
        
        # Test canonical format string matches
        canonical = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        assert content == canonical
        
def test_report_section_3_not_assessable():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        md_path = os.path.join(tmpdir, "report.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
            
        # target_available_for_summary should be listed because --target-col is not provided
        assert "target_available_for_summary" in md
        assert "not_provided" in md
        assert "What could NOT be assessed" in md

def test_report_no_forbidden_language():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        md_path = os.path.join(tmpdir, "report.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
            
        forbidden_words = ["production-ready", "leakage-proof", "fully reliable", "guaranteed", "regulatory compliant", "all failure modes detected", "model is safe", "low risk"]
        md_lower = md.lower()
        for w in forbidden_words:
            assert w not in md_lower, f"Forbidden word '{w}' found in report"
            
        assert "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage." in md
        
        assert "## 5. Flagged patterns" in md
        assert "No flagged patterns in the tested checks." in md

def test_report_out_dir_required():
    res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv"])
    assert res.returncode == 2
    assert "Error: --out-dir is required" in res.stderr

def test_report_split_null_if_not_requested():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        assert res.returncode == 0
        json_path = os.path.join(tmpdir, "report.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            
        assert data.get("split") is None
        assert "split_not_requested" in data["input"]["warnings"]

def test_report_section_2_summary_table_includes_profile():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        assert res.returncode == 0
        md_path = os.path.join(tmpdir, "report.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
            
        assert "| Module | Performed | Not Assessable | Skipped | Fail |" in md
        assert "| profile |" in md
        assert "* Checks marked as `not_assessable` are skipped when prerequisite conditions" in md
        assert "* Profile fail findings indicate data quality issues, not model leakage or split errors." in md

def test_report_evaluate_markdown_structure():
    fake_prov = {
        "input": {"path": "test.csv", "sha256": "abc", "nrows_total": 10, "ncols": 2, "columns_sha256": "def"},
        "run_metadata": {"seed": 42},
        "environment": {"python": "3.11", "pandas": "2.0"},
        "column_spec": {"target": "y", "prediction": "pred", "group": "grp", "time": None, "subset": None},
        "evaluation": {
            "models": [
                {"name": "supplied_predictions", "status": "performed", "mae": 1.0, "rmse": 1.732051, "r2": 0.5, "n_scored": 10}
            ],
            "cv": {
                "status": "not_assessable",
                "reason_code": "not_provided",
                "folds": [],
                "aggregate": {}
            },
            "group_errors": {
                "status": "performed",
                "worst_by_mae": ["G1"],
                "groups": [{"group": "G1", "n": 10, "mae": 1.0, "rmse": 1.0, "mean_residual": 0.0}],
                "coverage_ratio": 1.0
            },
            "thresholds": {"MIN_ROWS_FOR_METRICS": 10, "TOP_WORST_GROUPS": 3},
            "checks": [
                {"name": "cv_folds_size_sane", "status": "not_assessable", "reason_code": "not_provided", "result": "fail"}
            ]
        }
    }
    md = build_report_md(fake_prov)
    assert "## 9. Model evaluation" in md
    assert "| Model | MAE | RMSE | R² | n_scored (split) |" in md
    assert "| Fold | MAE | RMSE | R² |" in md
    assert "| supplied_predictions | 1.000000 | 1.732051 | 0.500000 | 10 |" in md
    assert "Cross-validation not assessable: N/A (not_provided)" in md
    assert "| G1 | 10 | 1.000000 | 1.000000 |" in md
    assert "- Coverage ratio: 1.000000" in md
    assert "- Thresholds: MIN_ROWS_FOR_METRICS=10, TOP_WORST_GROUPS=3" in md
    assert "- Not assessable: cv_folds_size_sane (not_provided)" in md

def test_report_scope_wording_and_metric_headers():
    fake_prov = {
        "input": {"path": "test.csv", "sha256": "abc", "nrows_total": 10, "ncols": 2, "columns_sha256": "def"},
        "run_metadata": {"seed": 42},
        "environment": {"python": "3.11", "pandas": "2.0"},
        "column_spec": {"target": "y", "prediction": None, "group": None, "time": None, "subset": None},
    }
    md = build_report_md(fake_prov)
    assert "pipeline-code level" in md
    assert "- Out of scope: pipeline-code level preprocessing leakage (fit scope cannot be inspected from a file), feature engineering transformations, sampling bias, label noise, database join leakage, temporal causality violations." in md



def test_report_shift_markdown_structure():
    """build_report_md with shift data renders section 6 with distribution shift and OOD table."""
    fake_prov = {
        "input": {"path": "test.csv", "sha256": "abc", "nrows_total": 50, "ncols": 3, "columns_sha256": "def"},
        "run_metadata": {"seed": 42},
        "environment": {"python": "3.12", "pandas": "3.0"},
        "column_spec": {"target": "y", "prediction": None, "group": None, "time": "ts", "subset": None},
        "shift": {
            "warnings": [],
            "interpretation": "Diagnostic indicator: review flagged checks manually.",
            "checks": [
                {
                    "name": "shift.split_available",
                    "status": "performed",
                    "reason_code": None,
                    "result": "pass",
                    "detail": "Split generated using temporal mode"
                },
                {
                    "name": "ood.feature_range",
                    "status": "performed",
                    "reason_code": None,
                    "result": "fail",
                    "detail": "Diagnostic indicator: 3 test rows outside training range in x"
                },
                {
                    "name": "drift.feature_ks",
                    "status": "not_assessable",
                    "reason_code": "not_provided",
                    "result": "pass",
                    "detail": "Diagnostic indicator: Feature KS drift not assessable (not_provided)"
                },
            ]
        }
    }
    md = build_report_md(fake_prov)
    assert "## 6. Split comparison and distribution shift" in md
    assert "### Distribution shift & OOD" in md
    assert "| Check | Result | Detail |" in md
    assert "| ood.feature_range | fail | Diagnostic indicator: 3 test rows outside training range in x |" in md
    assert "not_assessable (not_provided)" in md
    assert "| shift | ood.feature_range |" in md
    assert "| shift |" in md
    assert "--shift" in md
