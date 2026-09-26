import json
import os
from tests.conftest import run_cli

def test_split_cli_all_modes():
    res = run_cli([
        "split",
        "--input", "tests/fixtures/split_time.csv",
        "--target-col", "y",
        "--group-col", "grp",
        "--time-col", "ts"
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert len(data["split"]["comparison"]) == 3

def test_split_cli_byte_identical():
    args = [
        "split",
        "--input", "tests/fixtures/split_time.csv",
        "--target-col", "y",
        "--group-col", "grp",
        "--time-col", "ts"
    ]
    res1 = run_cli(args)
    res2 = run_cli(args)
    assert res1.returncode == 0
    assert res1.stdout == res2.stdout

def test_split_cli_group_missing():
    res = run_cli([
        "split",
        "--input", "tests/fixtures/split_groups.csv",
        "--mode", "group"
    ])
    assert res.returncode == 4
    assert not res.stdout.strip()
    assert "requires --group-col" in res.stderr

def test_split_cli_temporal_missing():
    res = run_cli([
        "split",
        "--input", "tests/fixtures/split_time.csv",
        "--mode", "temporal"
    ])
    assert res.returncode == 4
    assert not res.stdout.strip()
    assert "requires --time-col" in res.stderr

def test_golden_split_time_all():
    res = run_cli([
        "split",
        "--input", "tests/fixtures/split_time.csv",
        "--target-col", "y",
        "--group-col", "grp",
        "--time-col", "ts"
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    if "environment" in data:
        del data["environment"]
        
    normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    golden_path = "tests/golden/split_time_all_modes.normalized.json"
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        with open(golden_path, "w", encoding="utf-8") as f:
            f.write(normalized)
            
    with open(golden_path, "r", encoding="utf-8") as f:
        golden = f.read()
        
    assert normalized == golden
