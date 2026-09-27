import os
import json
from pathlib import Path
from tests.conftest import run_cli

def test_evaluate_cli_byte_identical():
    res1 = run_cli(["evaluate", "--input", "tests/fixtures/eval_exact_linear.csv", "--target-col", "y"])
    res2 = run_cli(["evaluate", "--input", "tests/fixtures/eval_exact_linear.csv", "--target-col", "y"])
    
    assert res1.returncode == 0
    assert res2.returncode == 0
    assert res1.stdout == res2.stdout

def test_evaluate_cli_split_mode_group_missing_col():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_exact_linear.csv", "--target-col", "y", "--split-mode", "group"])
    assert res.returncode == 4
    assert res.stdout.strip() == ""
    assert "Error: --split-mode group requires --group-col" in res.stderr

def test_evaluate_cli_golden():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_exact_linear.csv", "--target-col", "y"])
    assert res.returncode == 0
    
    actual_data = json.loads(res.stdout)
    actual_data.pop("environment", None)
    
    golden_path = Path("tests/golden/evaluate_exact_linear.normalized.json")
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        golden_path.parent.mkdir(exist_ok=True, parents=True)
        golden_path.write_text(json.dumps(actual_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_norm = json.load(f)
        
    assert actual_data == golden_norm

def test_evaluate_cli_golden_intervals():
    res = run_cli(["evaluate", "--input", "tests/fixtures/intervals_calibrated.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi", "--nominal-coverage", "0.9"])
    assert res.returncode == 0
    
    actual_data = json.loads(res.stdout)
    actual_data.pop("environment", None)
    
    golden_path = Path("tests/golden/evaluate_intervals.normalized.json")
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        golden_path.parent.mkdir(exist_ok=True, parents=True)
        golden_path.write_text(json.dumps(actual_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_norm = json.load(f)
        
    assert actual_data == golden_norm

def test_evaluate_cli_uncertainty_byte_identical():
    res1 = run_cli(["evaluate", "--input", "tests/fixtures/intervals_calibrated.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi"])
    res2 = run_cli(["evaluate", "--input", "tests/fixtures/intervals_calibrated.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi"])
    
    assert res1.returncode == 0
    assert res2.returncode == 0
    assert res1.stdout == res2.stdout
