import pytest
from modeltrust.dataio import read_table
from modeltrust.schema import ColumnSpec
from modeltrust.profile import build_profile

def test_high_cardinality_positive_path():
    loaded = read_table("tests/fixtures/high_card_id.csv")
    spec = ColumnSpec()
    profile = build_profile(loaded.frame, loaded.meta, spec)
    
    assert "code" in profile["high_cardinality_columns"]
