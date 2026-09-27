import json
import numpy as np
import pandas as pd
import pytest
from modeltrust.schema import ColumnSpec
from modeltrust.audit.shift import build_shift, compute_ks_statistic

def test_shift_ood_feature_range():
    # 1. shift_ood.csv temporal -> ood.feature_range.result == "fail", x_out outside_ratio == 1.0, x_in == 0.0
    df = pd.read_csv("tests/fixtures/shift_ood.csv")
    spec = ColumnSpec(target="y", time="ts")
    res = build_shift(df, spec, split_mode="temporal", test_size=0.2)

    fr = res["ood"]["feature_range"]
    assert fr["status"] == "performed"
    assert fr["result"] == "fail"
    assert fr["row_outside_ratio"] == 1.0
    assert fr["max_feature_outside_ratio"] == 1.0

    features_map = {f["column"]: f for f in fr["features"]}
    assert "x_out" in features_map
    assert "x_in" in features_map
    assert features_map["x_out"]["outside_ratio"] == 1.0
    assert features_map["x_out"]["n_outside"] == 10
    assert features_map["x_in"]["outside_ratio"] == 0.0
    assert features_map["x_in"]["n_outside"] == 0

def test_shift_ood_mahalanobis_result():
    # 2. On shift_ood.csv, prove mahalanobis result and pin actual output
    df = pd.read_csv("tests/fixtures/shift_ood.csv")
    spec = ColumnSpec(target="y", time="ts")
    res = build_shift(df, spec, split_mode="temporal", test_size=0.2)

    m = res["ood"]["mahalanobis"]
    assert m["status"] == "performed"
    assert m["result"] == "fail"
    assert m["ratio"] == 9.512194
    assert m["median_train"] == 0.855399
    assert m["median_test"] == 8.136721
    assert m["p95_train"] == 1.586765
    assert m["p95_test"] == 9.271794
    assert m["n_features"] == 2

def test_shift_clean_all_pass():
    # 3. shift_clean.csv temporal -> all pass, no ood_rows_present or drift_detected warnings
    df = pd.read_csv("tests/fixtures/shift_clean.csv")
    spec = ColumnSpec(target="y", time="ts")
    res = build_shift(df, spec, split_mode="temporal", test_size=0.2)

    assert res["ood"]["feature_range"]["result"] == "pass"
    assert res["ood"]["mahalanobis"]["result"] == "pass"
    assert res["drift"]["feature_ks"]["result"] == "pass"
    assert res["drift"]["target_ks"]["result"] == "pass"

    assert "ood_rows_present" not in res["warnings"]
    assert "drift_detected" not in res["warnings"]

def test_shift_drift_feature_ks_high():
    # 4. shift_drift.csv temporal -> drift.feature_ks.result == "fail", max_ks_stat >= 0.5
    df = pd.read_csv("tests/fixtures/shift_drift.csv")
    spec = ColumnSpec(target="y", time="ts")
    res = build_shift(df, spec, split_mode="temporal", test_size=0.2)

    fk = res["drift"]["feature_ks"]
    assert fk["status"] == "performed"
    assert fk["result"] == "fail"
    assert fk["max_ks_stat"] >= 0.5
    assert fk["max_ks_stat"] == 0.875
    assert "drift_detected" in res["warnings"]

def test_compute_ks_statistic_hand_verified():
    # 5. KS hand verification: [1,2,3,4] vs [5,6,7,8] -> 1.0; identical -> 0.0
    s1 = np.array([1.0, 2.0, 3.0, 4.0])
    s2 = np.array([5.0, 6.0, 7.0, 8.0])
    assert compute_ks_statistic(s1, s2) == 1.0
    assert compute_ks_statistic(s1, s1) == 0.0

def test_shift_constant_features_excluded():
    # 6. Constant column in train -> constant_features_excluded warning with col name, excluded from OOD/KS
    df = pd.DataFrame({
        "ts": np.arange(1, 61),
        "x_const": np.full(60, 5.0),
        "x_var": np.linspace(0.0, 10.0, 60),
        "y": np.linspace(1.0, 20.0, 60)
    })
    spec = ColumnSpec(target="y", time="ts")
    res = build_shift(df, spec, split_mode="temporal", test_size=0.2)

    assert any("constant_features_excluded" in w for w in res["warnings"])
    assert any("x_const" in w for w in res["warnings"])

    # Verify x_const is not in feature_range or feature_ks lists
    fr_cols = [f["column"] for f in res["ood"]["feature_range"]["features"]]
    ks_cols = [f["column"] for f in res["drift"]["feature_ks"]["features"]]
    assert "x_const" not in fr_cols
    assert "x_const" not in ks_cols
    assert "x_var" in fr_cols
    assert "x_var" in ks_cols

def test_shift_without_time_col():
    # 7. No --time-col -> drift controls not_assessable + not_provided; ood.* performed
    df = pd.DataFrame({
        "x": np.linspace(0.0, 10.0, 60),
        "y": np.linspace(1.0, 20.0, 60)
    })
    spec = ColumnSpec(target="y")
    res = build_shift(df, spec, split_mode="random", test_size=0.2, seed=42)

    assert res["ood"]["feature_range"]["status"] == "performed"
    assert res["ood"]["mahalanobis"]["status"] == "performed"

    assert res["drift"]["feature_ks"]["status"] == "not_assessable"
    assert res["drift"]["feature_ks"]["reason_code"] == "not_provided"
    assert res["drift"]["target_ks"]["status"] == "not_assessable"
    assert res["drift"]["target_ks"]["reason_code"] == "not_provided"
    assert "not_provided" in res["warnings"]

def test_shift_insufficient_rows():
    # 8. simple_ok.csv (2 rows) -> insufficient_rows and not_assessable
    df = pd.read_csv("tests/fixtures/simple_ok.csv")
    spec = ColumnSpec(target="y")
    res = build_shift(df, spec, split_mode="random", test_size=0.2)

    assert "insufficient_rows" in res["warnings"]
    assert res["ood"]["feature_range"]["status"] == "not_assessable"
    assert res["ood"]["feature_range"]["reason_code"] == "insufficient_rows"
    assert res["ood"]["mahalanobis"]["status"] == "not_assessable"
    assert res["ood"]["mahalanobis"]["reason_code"] == "insufficient_rows"

def test_shift_mahalanobis_degenerate_features():
    # 9. n_features >= n_train - 1 -> mahalanobis not_assessable + degenerate_covariance
    n = 25
    X = {f"f{i}": np.random.default_rng(i).normal(size=n) for i in range(25)}
    X["y"] = np.arange(n, dtype=float)
    df = pd.DataFrame(X)
    spec = ColumnSpec(target="y")
    # test_size = 0.2 -> n_test = 5, n_train = 20. n_features = 25 >= 20 - 1 = 19
    res = build_shift(df, spec, split_mode="random", test_size=0.2, seed=42)

    m = res["ood"]["mahalanobis"]
    assert m["status"] == "not_assessable"
    assert m["reason_code"] == "degenerate_covariance"

def test_shift_thresholds_warnings_order_and_determinism():
    # 10. Thresholds block, warnings order, two consecutive calls identical
    df = pd.read_csv("tests/fixtures/shift_ood.csv")
    spec = ColumnSpec(target="y", time="ts")

    res1 = build_shift(df, spec, split_mode="temporal", test_size=0.2, seed=42)
    res2 = build_shift(df, spec, split_mode="temporal", test_size=0.2, seed=42)

    # Thresholds check
    assert res1["thresholds"]["SHIFT_MIN_ROWS"] == 20
    assert res1["thresholds"]["OOD_FEATURE_OUTSIDE_RATIO_MIN"] == 0.10
    assert res1["thresholds"]["OOD_MAHALANOBIS_RATIO_MIN"] == 2.0
    assert res1["thresholds"]["DRIFT_KS_STAT_MIN"] == 0.25

    # Warnings order check
    valid_order = ["constant_features_excluded", "ood_rows_present", "drift_detected", "insufficient_rows", "not_provided"]
    warn_order_indices = []
    for w in res1["warnings"]:
        for idx, base in enumerate(valid_order):
            if w == base or w.startswith(base + ":") or w.startswith(base + " "):
                warn_order_indices.append(idx)
                break
    assert warn_order_indices == sorted(warn_order_indices)

    # Byte-identical determinism
    j1 = json.dumps(res1, sort_keys=True, indent=2)
    j2 = json.dumps(res2, sort_keys=True, indent=2)
    assert j1 == j2
