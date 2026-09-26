import json
from tests.conftest import run_cli

def test_leakage_cli_base():
    res = run_cli([
        "leakage",
        "--input", "tests/fixtures/leakage_base.csv",
        "--target-col", "target",
        "--group-col", "grp",
        "--subset-col", "subset"
    ])
    
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    leak = data.get("leakage")
    assert leak is not None
    assert "target_copy" in leak["target_copy_suspicion"]
    assert "id" in leak["index_like_columns"]
    assert leak["subset_row_overlap"]["has_overlap"] is True
    assert leak["subset_group_overlap"]["overlapping_groups"] == ["G20"]
    assert leak["subset_time_overlap"]["status"] == "not_assessable"

def test_leakage_cli_time():
    res = run_cli([
        "leakage",
        "--input", "tests/fixtures/leakage_time.csv",
        "--time-col", "time",
        "--subset-col", "subset"
    ])
    
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    leak = data.get("leakage")
    assert leak is not None
    assert leak["subset_time_overlap"]["has_overlap"] is True

def test_leakage_cli_schema_fail():
    res = run_cli([
        "leakage",
        "--input", "tests/fixtures/leakage_base.csv",
        "--target-col", "nonexistent"
    ])
    
    assert res.returncode == 4
    assert not res.stdout.strip()
    assert "Missing column: nonexistent" in res.stderr
