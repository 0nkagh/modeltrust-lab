import pytest
from modeltrust.dataio import read_table
from modeltrust.schema import ColumnSpec
from modeltrust.audit.leakage import build_leakage

def test_leakage_base():
    loaded = read_table("tests/fixtures/leakage_base.csv")
    spec = ColumnSpec(target="target", group="grp", subset="subset")
    leak = build_leakage(loaded.frame, spec)
    
    assert "target_copy" in leak["target_copy_suspicion"]
    assert "id" in leak["index_like_columns"]
    
    assert leak["subset_row_overlap"]["status"] == "performed"
    assert leak["subset_row_overlap"]["has_overlap"] is True
    assert leak["subset_row_overlap"]["overlapping_row_count"] == 2
    
    assert leak["subset_group_overlap"]["status"] == "performed"
    assert "G20" in leak["subset_group_overlap"]["overlapping_groups"]
    
    assert leak["subset_time_overlap"]["status"] == "not_assessable"

def test_leakage_time():
    loaded = read_table("tests/fixtures/leakage_time.csv")
    spec = ColumnSpec(time="time", subset="subset")
    leak = build_leakage(loaded.frame, spec)
    
    assert leak["subset_time_overlap"]["status"] == "performed"
    assert leak["subset_time_overlap"]["has_overlap"] is True
