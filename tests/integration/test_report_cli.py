import json
import os
import tempfile
from tests.conftest import run_cli

def test_report_byte_identical_runs():
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        res1 = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir1])
        res2 = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir2])
        
        assert res1.returncode == 0
        assert res2.returncode == 0
        
        with open(os.path.join(tmpdir1, "report.json"), "rb") as f:
            j1 = f.read()
        with open(os.path.join(tmpdir2, "report.json"), "rb") as f:
            j2 = f.read()
            
        with open(os.path.join(tmpdir1, "report.md"), "rb") as f:
            m1 = f.read()
        with open(os.path.join(tmpdir2, "report.md"), "rb") as f:
            m2 = f.read()
            
        # JSON might have different generated_at, but we didn't use --run-timestamp so it should be null.
        # But wait, environment might differ? environment is static per machine.
        assert j1 == j2
        assert m1 == m2

def test_report_golden():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", "--out-dir", tmpdir])
        assert res.returncode == 0
        
        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            
        if "environment" in data:
            del data["environment"]
            
        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        golden_path = "tests/golden/report_simple_ok.normalized.json"
        
        if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
            with open(golden_path, "w", encoding="utf-8") as f:
                f.write(normalized)
                
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()
            
        assert normalized == golden

def test_report_input_not_found():
    res = run_cli(["report", "--input", "nonexistent.csv", "--out-dir", "out"])
    assert res.returncode == 4
    assert "file not found" in res.stderr
    assert not res.stdout.strip()

def test_report_evaluate_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", "--evaluate", "--out-dir", tmpdir])
        assert res.returncode == 0
        
        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        assert "evaluation" in data
        assert isinstance(data["evaluation"], dict)
        assert "models" in data["evaluation"]
        
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
            
        assert "## 9. Model evaluation" in md
        assert "### Models" in md
        assert "| Model | MAE | RMSE | R² | n_scored |" in md
        assert "mean_baseline" in md
        assert "ols_baseline" in md
        assert "| evaluation |" in md

def test_report_evaluate_absent_negative_control():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", "--out-dir", tmpdir])
        assert res.returncode == 0
        
        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        assert "evaluation" not in data
        
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
            
        assert "## 9. Model evaluation" not in md
        assert "| evaluation |" not in md

def test_report_eval_args_without_evaluate_fails():
    res = run_cli(["report", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--out-dir", "out"])
    assert res.returncode == 2
    assert "Error: --pred-col requires --evaluate" in res.stderr
    assert not res.stdout.strip()

    for flag in ["--model", "--cv", "--folds"]:
        val = "ols" if flag == "--model" else ("random" if "cv" in flag else "3")
        res2 = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", flag, val, "--out-dir", "out"])
        assert res2.returncode == 2
        assert f"Error: {flag} requires --evaluate" in res2.stderr
        assert not res2.stdout.strip()

    for flag in ["--split-mode", "--test-size"]:
        val = "random" if "mode" in flag else "3"
        res3 = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", flag, val, "--out-dir", "out"])
        assert res3.returncode == 2
        assert f"Error: {flag} requires --evaluate or --shift" in res3.stderr
        assert not res3.stdout.strip()

def test_report_flagged_patterns_evaluation_fail():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/eval_const_target.csv", "--target-col", "y", "--evaluate", "--out-dir", tmpdir])
        assert res.returncode == 0
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
        assert "## 5. Flagged patterns" in md
        assert "| evaluation | r2_target_variance_defined | Target variance is zero |" in md

def test_report_flagged_patterns_no_flags():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp", "--mode", "group", "--split-mode", "group", "--evaluate", "--out-dir", tmpdir])
        assert res.returncode == 0
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
        assert "## 5. Flagged patterns" in md
        assert "- No flagged patterns in the tested checks." in md

def test_report_evaluate_byte_identical_runs():
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        cmd = ["report", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp", "--evaluate", "--out-dir"]
        res1 = run_cli(cmd + [tmpdir1])
        res2 = run_cli(cmd + [tmpdir2])
        
        assert res1.returncode == 0
        assert res2.returncode == 0
        
        with open(os.path.join(tmpdir1, "report.json"), "rb") as f:
            j1 = f.read()
        with open(os.path.join(tmpdir2, "report.json"), "rb") as f:
            j2 = f.read()
            
        with open(os.path.join(tmpdir1, "report.md"), "rb") as f:
            m1 = f.read()
        with open(os.path.join(tmpdir2, "report.md"), "rb") as f:
            m2 = f.read()
            
        assert j1 == j2
        assert m1 == m2

def test_report_evaluate_golden():
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ["report", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp", "--evaluate", "--out-dir", tmpdir]
        res = run_cli(cmd)
        assert res.returncode == 0
        
        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            
        if "environment" in data:
            del data["environment"]
            
        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        golden_path = "tests/golden/report_evaluate.normalized.json"
        
        if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
            with open(golden_path, "w", encoding="utf-8") as f:
                f.write(normalized)
                
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()
            
        assert normalized == golden
        
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md_text = f.read()
        assert "| Model | MAE | RMSE | R² | n_scored |" in md_text
        assert "pipeline-code level" in md_text

def test_report_shift_present():
    """--shift flag adds shift block to JSON and distribution shift section to Markdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli([
            "report", "--input", "tests/fixtures/shift_drift.csv",
            "--target-col", "y", "--time-col", "ts",
            "--shift", "--out-dir", tmpdir
        ])
        assert res.returncode == 0

        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        assert "shift" in data
        assert isinstance(data["shift"], dict)
        assert "checks" in data["shift"]

        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
        assert "## 6. Split comparison and distribution shift" in md
        assert "### Distribution shift & OOD" in md
        assert "| Check | Result | Detail |" in md
        assert "| shift |" in md

def test_report_shift_absent_negative_control():
    """Without --shift, no shift key in JSON and §6 keeps original header."""
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli([
            "report", "--input", "tests/fixtures/shift_drift.csv",
            "--target-col", "y", "--time-col", "ts",
            "--out-dir", tmpdir
        ])
        assert res.returncode == 0

        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        assert "shift" not in data

        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
        assert "## 6. Split comparison and distribution shift" not in md
        assert "## 6. Split comparison" in md
        assert "### Distribution shift & OOD" not in md

def test_report_split_mode_without_shift_or_evaluate_fails():
    """--split-mode without --evaluate or --shift returns exit code 2."""
    res = run_cli([
        "report", "--input", "tests/fixtures/simple_ok.csv",
        "--target-col", "y", "--split-mode", "random", "--out-dir", "out"
    ])
    assert res.returncode == 2
    assert "Error: --split-mode requires --evaluate or --shift" in res.stderr
    assert not res.stdout.strip()

def test_report_shift_flagged_patterns():
    """--shift with OOD fixture shows shift fail flags in §5."""
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli([
            "report", "--input", "tests/fixtures/shift_ood.csv",
            "--target-col", "y", "--time-col", "ts",
            "--shift", "--out-dir", tmpdir
        ])
        assert res.returncode == 0
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md = f.read()
        assert "## 5. Flagged patterns" in md
        # shift module should appear in flagged patterns table (OOD fixture has out-of-range features)
        assert "| shift |" in md

def test_report_shift_byte_identical_runs():
    """Two identical --shift report runs produce byte-identical output."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        cmd = [
            "report", "--input", "tests/fixtures/shift_drift.csv",
            "--target-col", "y", "--time-col", "ts",
            "--shift", "--out-dir"
        ]
        res1 = run_cli(cmd + [tmpdir1])
        res2 = run_cli(cmd + [tmpdir2])
        assert res1.returncode == 0
        assert res2.returncode == 0

        with open(os.path.join(tmpdir1, "report.json"), "rb") as f:
            j1 = f.read()
        with open(os.path.join(tmpdir2, "report.json"), "rb") as f:
            j2 = f.read()
        with open(os.path.join(tmpdir1, "report.md"), "rb") as f:
            m1 = f.read()
        with open(os.path.join(tmpdir2, "report.md"), "rb") as f:
            m2 = f.read()
        assert j1 == j2
        assert m1 == m2

def test_report_shift_golden():
    """Golden test for report --shift using shift_drift.csv."""
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli([
            "report", "--input", "tests/fixtures/shift_drift.csv",
            "--target-col", "y", "--time-col", "ts",
            "--shift", "--out-dir", tmpdir
        ])
        assert res.returncode == 0

        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())

        if "environment" in data:
            del data["environment"]

        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        golden_path = "tests/golden/report_shift.normalized.json"

        if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
            with open(golden_path, "w", encoding="utf-8") as f:
                f.write(normalized)

        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()

        assert normalized == golden

def test_report_existing_goldens_unchanged():
    """Confirm that existing goldens (simple_ok, evaluate) are still matched — no regression."""
    # simple_ok golden
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", "--out-dir", tmpdir])
        assert res.returncode == 0
        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        if "environment" in data:
            del data["environment"]
        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        with open("tests/golden/report_simple_ok.normalized.json", "r", encoding="utf-8") as f:
            golden = f.read()
        assert normalized == golden

    # evaluate golden
    with tempfile.TemporaryDirectory() as tmpdir2:
        res2 = run_cli(["report", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp", "--evaluate", "--out-dir", tmpdir2])
        assert res2.returncode == 0
        with open(os.path.join(tmpdir2, "report.json"), "r", encoding="utf-8") as f:
            data2 = json.loads(f.read())
        if "environment" in data2:
            del data2["environment"]
        normalized2 = json.dumps(data2, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        with open("tests/golden/report_evaluate.normalized.json", "r", encoding="utf-8") as f:
            golden2 = f.read()
        assert normalized2 == golden2

def test_report_uncertainty_golden():
    """Golden test for report --evaluate --lower-col --upper-col."""
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli([
            "report", "--input", "tests/fixtures/intervals_calibrated.csv",
            "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi", "--nominal-coverage", "0.9",
            "--evaluate", "--out-dir", tmpdir
        ])
        assert res.returncode == 0

        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())

        if "environment" in data:
            del data["environment"]

        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        golden_path = "tests/golden/report_uncertainty.normalized.json"

        if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
            with open(golden_path, "w", encoding="utf-8") as f:
                f.write(normalized)

        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()

        assert normalized == golden
