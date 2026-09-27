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
    
    assert get_check(leak, "index_like_feature")["status"] == "not_assessable"

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

def test_leak_index_insufficient_rows():
    loaded = read_table("tests/fixtures/simple_ok.csv")
    spec = ColumnSpec()
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "index_like_feature")
    assert ck["status"] == "not_assessable"
    assert ck["result"] is None
    assert ck["reason_code"] == "insufficient_rows"
    assert ck["evidence"] is None

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
    
    assert "target_not_provided" in data["input"]["warnings"]
    
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
    assert leak["thresholds"]["MIN_ROWS_FOR_INDEX_CHECK"] == 10
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

def test_preprocess_global_standardization_signature():
    loaded = read_table("tests/fixtures/leak_std_full.csv")
    spec = ColumnSpec(target="y")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "preprocess.global_standardization_signature")
    assert ck["status"] == "performed"
    assert ck["result"] == "fail"
    assert ck["evidence"] is not None
    cols = [e["column"] for e in ck["evidence"]]
    assert "x_z" in cols
    assert "x_raw" not in cols

def test_preprocess_global_minmax_signature():
    loaded = read_table("tests/fixtures/leak_minmax_full.csv")
    spec = ColumnSpec(target="y")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "preprocess.global_minmax_signature")
    assert ck["status"] == "performed"
    assert ck["result"] == "fail"
    assert ck["evidence"] is not None
    cols = [e["column"] for e in ck["evidence"]]
    assert "x_norm" in cols

def test_preprocess_feature_target_near_deterministic():
    loaded = read_table("tests/fixtures/leak_det_feature.csv")
    spec = ColumnSpec(target="y")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "preprocess.feature_target_near_deterministic")
    assert ck["status"] == "performed"
    assert ck["result"] == "fail"
    assert ck["evidence"] is not None
    cols = [e["column"] for e in ck["evidence"]]
    assert "x_det" in cols

def test_preprocess_suspicious_feature_name():
    loaded = read_table("tests/fixtures/leak_name_hints.csv")
    spec = ColumnSpec(target="y")
    leak = build_leakage(loaded.frame, spec)
    
    ck = get_check(leak, "preprocess.suspicious_feature_name")
    assert ck["status"] == "performed"
    assert ck["result"] == "pass"
    assert "suspicious_feature_names" in leak["warnings"]
    assert ck["evidence"] is not None
    cols = [e["column"] for e in ck["evidence"]]
    assert len(cols) == 3
    assert "y_mean_3" in cols
    assert "x_ratio" in cols
    assert "z_score_x" in cols

def test_preprocess_signatures_clean_negative():
    loaded = read_table("tests/fixtures/leak_clean.csv")
    spec = ColumnSpec(target="y", subset="subset", group="grp")
    leak = build_leakage(loaded.frame, spec)
    
    ck_std = get_check(leak, "preprocess.global_standardization_signature")
    assert ck_std["status"] == "performed"
    assert ck_std["result"] == "pass"
    
    ck_minmax = get_check(leak, "preprocess.global_minmax_signature")
    assert ck_minmax["status"] == "performed"
    assert ck_minmax["result"] == "pass"
    
    ck_det = get_check(leak, "preprocess.feature_target_near_deterministic")
    assert ck_det["status"] == "performed"
    assert ck_det["result"] == "pass"

def test_preprocess_redundant_feature_pair():
    import pandas as pd
    import numpy as np
    rng = np.random.default_rng(42)
    f1 = rng.normal(0, 1, 25)
    f2 = f1 + rng.normal(0, 1e-6, 25)
    f3 = rng.normal(10, 2, 25)
    df_redundant = pd.DataFrame({"f1": f1, "f2": f2, "f3": f3, "y": f1 * 2})
    spec = ColumnSpec(target="y")
    
    leak = build_leakage(df_redundant, spec)
    ck = get_check(leak, "preprocess.redundant_feature_pair")
    assert ck["status"] == "performed"
    assert ck["result"] == "pass"
    assert "redundant_features" in leak["warnings"]
    assert ck["evidence"] is not None
    assert any((e["feature_a"] == "f1" and e["feature_b"] == "f2") or (e["feature_a"] == "f2" and e["feature_b"] == "f1") for e in ck["evidence"])
    
    loaded_clean = read_table("tests/fixtures/leak_clean.csv")
    leak_clean = build_leakage(loaded_clean.frame, ColumnSpec(target="y"))
    ck_clean = get_check(leak_clean, "preprocess.redundant_feature_pair")
    assert ck_clean["status"] == "performed"
    assert ck_clean["result"] == "pass"
    assert "redundant_features" not in leak_clean["warnings"]

def test_preprocess_fit_scope_always_not_assessable():
    for fixture in ["tests/fixtures/leak_clean.csv", "tests/fixtures/leak_std_full.csv", "tests/fixtures/leak_det_feature.csv"]:
        loaded = read_table(fixture)
        leak = build_leakage(loaded.frame, ColumnSpec(target="y"))
        ck = get_check(leak, "preprocess.fit_scope")
        assert ck["status"] == "not_assessable"
        assert ck["result"] is None
        assert ck["reason_code"] == "requires_pipeline_code"
        assert ck["detail"] == "Whether transformers, imputers or encoders were fit on training data only cannot be determined from a CSV. Pipeline code is out of scope for v1."

def test_preprocess_thresholds_and_warning_order():
    loaded = read_table("tests/fixtures/leak_name_hints.csv")
    spec = ColumnSpec()
    leak = build_leakage(loaded.frame, spec)
    
    th = leak["thresholds"]
    assert th["PREPROCESS_MIN_ROWS"] == 10
    assert th["PREPROCESS_NUMERIC_TOL"] == 1e-9
    assert th["FEATURE_TARGET_DET_MIN"] == 0.999
    assert th["REDUNDANT_PAIR_MIN"] == 0.999
    
    expected_order = [
        "target_not_provided",
        "subset_not_provided",
        "group_not_provided",
        "time_not_provided",
        "suspicious_feature_names"
    ]
    assert leak["warnings"] == expected_order
