import json
import os
import subprocess
from tests.conftest import run_cli

def test_leakage_exit_0_and_split_3():
    res_leak = run_cli([
        "leakage",
        "--input", "tests/fixtures/leak_clean.csv",
        "--target-col", "y",
        "--subset-col", "subset",
        "--group-col", "grp"
    ])
    assert res_leak.returncode == 0
    data = json.loads(res_leak.stdout)
    assert "leakage" in data
    
    res_split = run_cli([
        "report",
        "--input", "tests/fixtures/leak_clean.csv"
    ])
    assert res_split.returncode == 2

def test_leakage_byte_identical():
    args = [
        "leakage",
        "--input", "tests/fixtures/leak_clean.csv",
        "--target-col", "y",
        "--subset-col", "subset",
        "--group-col", "grp"
    ]
    res1 = run_cli(args)
    res2 = run_cli(args)
    
    assert res1.returncode == 0
    assert res1.stdout == res2.stdout

def test_leakage_file_not_found():
    res = run_cli([
        "leakage",
        "--input", "nonexistent.csv"
    ])
    assert res.returncode == 4
    assert not res.stdout.strip()
    assert "file not found" in res.stderr

def test_golden_leakage_clean():
    res = run_cli([
        "leakage",
        "--input", "tests/fixtures/leak_clean.csv",
        "--target-col", "y",
        "--subset-col", "subset",
        "--group-col", "grp"
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    if "environment" in data:
        del data["environment"]
        
    normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    golden_path = "tests/golden/leakage_clean.normalized.json"
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(normalized)
            
    with open(golden_path, "r", encoding="utf-8") as f:
        golden = f.read()
        
    assert normalized == golden

def test_leakage_cli_preprocess_std_exit_code():
    res = run_cli([
        "leakage",
        "--input", "tests/fixtures/leak_std_full.csv",
        "--target-col", "y"
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "leakage" in data
    check_names = [c["name"] for c in data["leakage"]["checks"]]
    assert "preprocess.fit_scope" in check_names
    assert "preprocess.global_standardization_signature" in check_names
    assert "preprocess.global_minmax_signature" in check_names
    assert "preprocess.feature_target_near_deterministic" in check_names
    assert "preprocess.redundant_feature_pair" in check_names
    assert "preprocess.suspicious_feature_name" in check_names

def test_golden_leakage_preprocess():
    res = run_cli([
        "leakage",
        "--input", "tests/fixtures/leak_std_full.csv",
        "--target-col", "y"
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    if "environment" in data:
        del data["environment"]
        
    normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    golden_path = "tests/golden/leakage_preprocess.normalized.json"
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(normalized)
            
    with open(golden_path, "r", encoding="utf-8") as f:
        golden = f.read()
        
    assert normalized == golden
