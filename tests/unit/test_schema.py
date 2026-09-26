import pytest
import pandas as pd
from modeltrust.schema import ColumnSpec, validate_input

def test_missing_target():
    df = pd.DataFrame({"a": [1], "b": [2]})
    meta = {}
    spec = ColumnSpec(target="y")
    res = validate_input(df, meta, spec)
    # find target_present check
    check = next(c for c in res["checks"] if c["name"] == "target_present")
    assert check["status"] == "performed"
    assert check["result"] == "fail"
    assert "y" in check["detail"]

def test_non_numeric_target():
    df = pd.DataFrame({"id": [1, 2, 3], "y": [2.5, "abc", 3.1]})
    meta = {}
    spec = ColumnSpec(target="y")
    res = validate_input(df, meta, spec)
    check = next(c for c in res["checks"] if c["name"] == "target_numeric")
    assert check["result"] == "fail"
    assert "abc" in check["detail"]

def test_validate_input_side_effect_free():
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
