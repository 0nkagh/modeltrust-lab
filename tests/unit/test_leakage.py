import pytest
import json
from modeltrust.dataio import read_table
from modeltrust.schema import ColumnSpec
from modeltrust.audit.leakage import build_leakage
from tests.conftest import run_cli
from modeltrust.schema import validate_input

def get_check(leak: dict, name: str) -> dict:
    return next(c for c in leak["checks"] if c["name"] == name)

def test_leakage_base():
    loaded = read_table("tests/fixtures/leakage_base.csv")
    spec = ColumnSpec(target="target", group="grp", subset="subset")
    leak = build_leakage(loaded.frame, spec)
    
    assert get_check(leak, "target_copy_exact")["result"] == "fail"
    assert get_check(leak, "index_like_feature")["result"] == "pass"
    assert get_check(leak, "subset_row_overlap")["result"] == "fail"
    assert get_check(leak, "subset_group_overlap")["result"] == "fail"

def test_leakage_time():
    loaded = read_table("tests/fixtures/leakage_time.csv")
    spec = ColumnSpec(time="time", subset="subset")
    leak = build_leakage(loaded.frame, spec)
    
    assert get_check(leak, "subset_time_ranges")["result"] == "fail"
    assert get_check(leak, "subset_time_ranges")["evidence"]["overlaps"] is True

def test_leak_copy():
    loaded = read_table("tests/fixtures/leak_copy.csv")
    spec = ColumnSpec(target="y")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "target_copy_exact")
    assert ck["result"] == "fail"
    assert ck["evidence"][0]["column"] == "x_copy"
    assert ck["evidence"][0]["equality_ratio"] == 1.0
    
    assert get_check(leak, "index_like_feature")["result"] == "pass"

def test_leak_nearcopy():
    loaded = read_table("tests/fixtures/leak_nearcopy.csv")
    spec = ColumnSpec(target="y")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "target_copy_near")
    assert ck["result"] == "fail"
    assert ck["evidence"][0]["abs_correlation"] >= 0.999
    assert ck["evidence"][0]["equality_ratio"] < 1.0

def test_leak_index():
    loaded = read_table("tests/fixtures/leak_index.csv")
    spec = ColumnSpec()
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "index_like_feature")
    assert ck["result"] == "fail"
    assert ck["evidence"][0]["column"] == "row_id"

def test_leak_overlap():
    loaded = read_table("tests/fixtures/leak_overlap.csv")
    spec = ColumnSpec(target="y", subset="subset")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "subset_row_overlap")
    assert ck["result"] == "fail"
    assert ck["evidence"]["overlap_count"] == 2
    
    ck_near = get_check(leak, "target_copy_near")
    assert ck_near["status"] == "not_assessable"
    assert ck_near["reason_code"] == "insufficient_rows"

def test_leak_group_overlap():
    loaded = read_table("tests/fixtures/leak_group_overlap.csv")
    spec = ColumnSpec(subset="subset", group="grp")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "subset_group_overlap")
    assert ck["result"] == "fail"
    assert ck["evidence"]["overlap_group_count"] == 2

def test_leak_time_overlap():
    loaded = read_table("tests/fixtures/leak_time_overlap.csv")
    spec = ColumnSpec(subset="subset", time="t")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "subset_time_ranges")
    assert ck["result"] == "fail"
    assert ck["evidence"]["overlaps"] is True

def test_leak_clean():
    loaded = read_table("tests/fixtures/leak_clean.csv")
    spec = ColumnSpec(target="y", subset="subset", group="grp")
    leak = build_leakage(loaded.frame, spec)
    
    assert leak["summary"]["suspicion_count"] == 0
    assert get_check(leak, "subset_row_overlap")["status"] == "performed"
    assert get_check(leak, "subset_row_overlap")["result"] == "pass"
    assert get_check(leak, "subset_group_overlap")["status"] == "performed"
    assert get_check(leak, "subset_group_overlap")["result"] == "pass"

def test_missing_target_cli():
    res = run_cli(["leakage", "--input", "tests/fixtures/leak_clean.csv"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    assert data["input"]["warnings"]["target_not_provided"] is True
    
    leak = data["leakage"]
    assert get_check(leak, "target_copy_exact")["status"] == "not_assessable"
    assert get_check(leak, "target_copy_exact")["reason_code"] == "not_provided"
    assert get_check(leak, "target_copy_near")["status"] == "not_assessable"
    assert get_check(leak, "target_copy_near")["reason_code"] == "not_provided"

def test_missing_subset_cli():
    res = run_cli(["leakage", "--input", "tests/fixtures/leak_clean.csv", "--target-col", "y"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    leak = data["leakage"]
    assert get_check(leak, "subset_row_overlap")["status"] == "not_assessable"
    assert get_check(leak, "subset_group_overlap")["status"] == "not_assessable"
    assert get_check(leak, "subset_time_ranges")["status"] == "not_assessable"
    assert get_check(leak, "subset_row_overlap")["reason_code"] == "not_provided"

def test_interpretation_and_thresholds():
    loaded = read_table("tests/fixtures/leak_clean.csv")
    spec = ColumnSpec()
    leak = build_leakage(loaded.frame, spec)
    
    assert leak["interpretation"] == "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage."
    assert leak["thresholds"]["EXACT_COPY_EQUALITY_RATIO"] == 1.0
    assert "suspicion_count" in leak["summary"]

def test_validate_input_side_effect():
    import pandas as pd
    df = pd.DataFrame({"id": [1, 2], "y": [2.5, 3.1], "grp": ["A", "A"]})
    meta = {}
    spec = ColumnSpec(target="y", group="grp")
    
    res1 = validate_input(df, meta, spec)
    assert meta == {}
    assert "single_group" in res1["session_warnings"]
    
    res2 = validate_input(df, meta, spec)
    assert meta == {}
    assert "single_group" in res2["session_warnings"]
    assert res1 == res2

def test_high_cardinality():
    from modeltrust.profile import build_profile
    loaded = read_table("tests/fixtures/high_card_id.csv")
    spec = ColumnSpec()
    profile = build_profile(loaded.frame, loaded.meta, spec)
    
    assert "code" in profile["high_cardinality_columns"]
