import pytest
from pathlib import Path
from modeltrust.dataio import read_table
from modeltrust.schema import ColumnSpec
from modeltrust.profile import build_profile
from tests.conftest import run_cli
import json

def test_profile_dirty():
    loaded = read_table("tests/fixtures/profile_dirty.csv")
    spec = ColumnSpec(target="y", group="grp")
    profile = build_profile(loaded.frame, loaded.meta, spec)
    
    assert profile["row_count"] == 8
    assert profile["column_count"] == 7
    assert profile["duplicate_rows"]["exact_duplicate_count"] == 1
    assert profile["duplicate_rows"]["example_row_indices"] == [3]
    
    assert "const" in profile["constant_columns"]
    assert "empty" in profile["all_missing_columns"]
    
    # empty column is_constant should be None
    empty_col = next(c for c in profile["columns"] if c["name"] == "empty")
    assert empty_col["is_constant"] is None
    
    score_col = next(c for c in profile["columns"] if c["name"] == "score")
    assert score_col["non_finite_count"] == 1
    assert score_col["stats"] is not None
    assert score_col["stats"]["max"] == 5.5 # inf is excluded
    
    y_col = next(c for c in profile["columns"] if c["name"] == "y")
    assert y_col["missing_count"] == 2
    
    # target_numeric pass despite missing cells
    schema_res = __import__("modeltrust.schema", fromlist=["validate_input"]).validate_input(loaded.frame, loaded.meta, spec)
    tn_check = next(c for c in schema_res["checks"] if c["name"] == "target_numeric")
    assert tn_check["result"] == "pass"
    
    # txt unique ratio is 7/8 = 0.875, which is < 0.95, so it shouldn't be high cardinality
    assert "txt" not in profile["high_cardinality_columns"]
    
    # Check roles
    assert y_col["role"] == "target"
    grp_col = next(c for c in profile["columns"] if c["name"] == "grp")
    assert grp_col["role"] == "group"
    txt_col = next(c for c in profile["columns"] if c["name"] == "txt")
    assert txt_col["role"] == "feature"

def test_top_values_order():
    loaded = read_table("tests/fixtures/profile_dirty.csv")
    spec = ColumnSpec()
    profile = build_profile(loaded.frame, loaded.meta, spec)
    
    grp_col = next(c for c in profile["columns"] if c["name"] == "grp")
    # grp has C:3, B:3, A:2. C and B should be ordered by B, then C because of alphabetical order?
    # counts: A:2, B:3, C:3 (Wait, A has 2, B has 3, C has 3)
    # top_values sort key is (-count, value)
    # so count 3: B, C. count 2: A.
    # order should be B, C, A.
    tv = grp_col["top_values"]
    assert tv[0]["value"] == "B"
    assert tv[1]["value"] == "C"
    assert tv[2]["value"] == "A"

def test_missing_and_unique_ratio():
    loaded = read_table("tests/fixtures/empty_rows.csv")
    spec = ColumnSpec()
    profile = build_profile(loaded.frame, loaded.meta, spec)
    
    assert profile["row_count"] == 0
    a_col = next(c for c in profile["columns"] if c["name"] == "a")
    assert a_col["missing_ratio"] == 0.0
    assert a_col["unique_ratio"] == 0.0
    assert a_col["is_all_missing"] is True
    assert a_col["is_constant"] is None
    
    # Check rows_present
    rp_check = next(c for c in profile["checks"] if c["name"] == "rows_present")
    assert rp_check["result"] == "fail"

def test_byte_identical_cli():
    res1 = run_cli(["profile", "--input", "tests/fixtures/profile_dirty.csv"])
    res2 = run_cli(["profile", "--input", "tests/fixtures/profile_dirty.csv"])
    
    assert res1.returncode == 0
    assert res1.stdout == res2.stdout

def test_cli_routing():
    # profile without file -> exit 4
    res = run_cli(["profile", "--input", "nonexistent.csv"])
    assert res.returncode == 4
    
    # leakage -> exit 3
    res2 = run_cli(["leakage", "--input", "tests/fixtures/profile_dirty.csv"])
    assert res2.returncode == 3

def test_target_available_for_summary():
    loaded = read_table("tests/fixtures/profile_dirty.csv")
    spec = ColumnSpec() # no target
    profile = build_profile(loaded.frame, loaded.meta, spec)
    
    ck = next(c for c in profile["checks"] if c["name"] == "target_available_for_summary")
    assert ck["status"] == "not_assessable"
    assert ck["reason_code"] == "not_provided"
