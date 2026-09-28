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
            with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
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
        assert "| Model | MAE | RMSE | R² | n_scored (split) |" in md
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
            with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(normalized)
                
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()
            
        assert normalized == golden
        
        with open(os.path.join(tmpdir, "report.md"), "r", encoding="utf-8") as f:
            md_text = f.read()
        assert "| Model | MAE | RMSE | R² | n_scored (all rows provided) |" in md_text
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
            with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
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
            with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(normalized)

        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()

        assert normalized == golden


import json
import os
import tempfile
import hashlib
from tests.conftest import run_cli

def test_report_card_writes_four_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(['report', '--input', 'tests/fixtures/intervals_calibrated.csv', '--target-col', 'y', '--evaluate', '--shift', '--card', '--out-dir', tmpdir])
        assert res.returncode == 0
        assert os.path.exists(os.path.join(tmpdir, 'report.json'))
        assert os.path.exists(os.path.join(tmpdir, 'report.md'))
        assert os.path.exists(os.path.join(tmpdir, 'card.json'))
        assert os.path.exists(os.path.join(tmpdir, 'card.md'))
        expected_msg = f'wrote {os.path.join(tmpdir, "report.json")}, {os.path.join(tmpdir, "report.md")}, {os.path.join(tmpdir, "card.json")} and {os.path.join(tmpdir, "card.md")}'
        assert expected_msg in res.stderr

def test_report_card_determinism():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = os.path.join(tmpdir, 'out')
        args = ['report', '--input', 'tests/fixtures/intervals_calibrated.csv', '--target-col', 'y', '--lower-col', 'lo', '--upper-col', 'hi', '--nominal-coverage', '0.9', '--evaluate', '--shift', '--card', '--out-dir', out_dir]
        
        res1 = run_cli(args)
        assert res1.returncode == 0
        hashes1 = {}
        for fname in ['report.json', 'report.md', 'card.json', 'card.md']:
            with open(os.path.join(out_dir, fname), 'rb') as f:
                hashes1[fname] = hashlib.sha256(f.read()).hexdigest()
                
        res2 = run_cli(args)
        assert res2.returncode == 0
        for fname in ['report.json', 'report.md', 'card.json', 'card.md']:
            with open(os.path.join(out_dir, fname), 'rb') as f:
                assert hashes1[fname] == hashlib.sha256(f.read()).hexdigest()


def test_report_card_consistency_with_card_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Senaryo 1: eval_preds.csv
        rep_dir1 = os.path.join(tmpdir, 'rep1')
        card_dir1 = os.path.join(tmpdir, 'card1')
        res_rep1 = run_cli(['report', '--input', 'tests/fixtures/eval_preds.csv', '--target-col', 'y', '--pred-col', 'pred', '--group-col', 'grp', '--evaluate', '--shift', '--card', '--out-dir', rep_dir1])
        res_card1 = run_cli(['card', '--input', 'tests/fixtures/eval_preds.csv', '--target-col', 'y', '--pred-col', 'pred', '--group-col', 'grp', '--out-dir', card_dir1])
        assert res_rep1.returncode == 0
        assert res_card1.returncode == 0
        
        with open(os.path.join(rep_dir1, 'card.json'), 'r', encoding='utf-8') as f:
            c1_s1 = json.load(f)
        with open(os.path.join(card_dir1, 'card.json'), 'r', encoding='utf-8') as f:
            c2_s1 = json.load(f)
            
        blocks = ['questions', 'checks_summary', 'not_assessable', 'metrics', 'thresholds', 'scope']
        for b in blocks:
            assert c1_s1.get(b) == c2_s1.get(b)

        # Senaryo 2: intervals_calibrated.csv
        rep_dir2 = os.path.join(tmpdir, 'rep2')
        card_dir2 = os.path.join(tmpdir, 'card2')
        res_rep2 = run_cli(['report', '--input', 'tests/fixtures/intervals_calibrated.csv', '--target-col', 'y', '--lower-col', 'lo', '--upper-col', 'hi', '--nominal-coverage', '0.9', '--evaluate', '--shift', '--card', '--out-dir', rep_dir2])
        res_card2 = run_cli(['card', '--input', 'tests/fixtures/intervals_calibrated.csv', '--target-col', 'y', '--lower-col', 'lo', '--upper-col', 'hi', '--nominal-coverage', '0.9', '--out-dir', card_dir2])
        assert res_rep2.returncode == 0
        assert res_card2.returncode == 0
        
        with open(os.path.join(rep_dir2, 'card.json'), 'r', encoding='utf-8') as f:
            c1_s2 = json.load(f)
        with open(os.path.join(card_dir2, 'card.json'), 'r', encoding='utf-8') as f:
            c2_s2 = json.load(f)
            
        for b in blocks:
            assert c1_s2.get(b) == c2_s2.get(b)

def test_report_card_golden():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(['report', '--input', 'tests/fixtures/intervals_calibrated.csv', '--target-col', 'y', '--evaluate', '--shift', '--card', '--out-dir', tmpdir])
        assert res.returncode == 0
        
        with open(os.path.join(tmpdir, 'card.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for k in ['run', 'environment', 'reproduce_command']:
            if k in data:
                del data[k]
        if 'input' in data and 'path' in data['input']:
            data['input']['path'] = 'normalized'
            
        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        golden_path = 'tests/golden/report_card.normalized.json'
        
        if os.environ.get('MODELTRUST_REGEN_GOLDEN') == '1':
            with open(golden_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(normalized)
                
        with open(golden_path, 'r', encoding='utf-8') as f:
            golden = f.read()
            
        assert normalized == golden

def test_report_without_card_unchanged():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(['report', '--input', 'tests/fixtures/simple_ok.csv', '--out-dir', tmpdir])
        assert res.returncode == 0
        
        files = os.listdir(tmpdir)
        assert sorted(files) == ['report.json', 'report.md']
        
        expected_msg = f'wrote {os.path.join(tmpdir, "report.json")} and {os.path.join(tmpdir, "report.md")}'
        assert expected_msg in res.stderr
