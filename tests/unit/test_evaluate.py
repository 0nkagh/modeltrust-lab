import json
import os
import tempfile
import pytest
from tests.conftest import run_cli

def test_evaluate_eval_exact_linear():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_exact_linear.csv", "--target-col", "y"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    ols = next(m for m in data["evaluation"]["models"] if m["name"] == "ols_baseline")
    assert abs(ols["mae"]) < 1e-9
    assert abs(ols["rmse"]) < 1e-9
    assert abs(ols["r2"] - 1.0) < 1e-9
    
    mean_model = next(m for m in data["evaluation"]["models"] if m["name"] == "mean_baseline")
    assert mean_model["r2"] < 1.0

def test_evaluate_eval_preds():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    supp = next(m for m in data["evaluation"]["models"] if m["name"] == "supplied_predictions")
    assert abs(supp["mae"] - 1.0) < 1e-9

def test_evaluate_pred_and_model_fails():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--model", "mean"])
    assert res.returncode == 2
    assert "Error: --pred-col and --model cannot be used together" in res.stderr

def test_evaluate_eval_nan():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_nan.csv", "--target-col", "y"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    assert any(w.startswith("dropped_rows_due_to_nan") for w in data["evaluation"]["warnings"])
    
    ols = next(m for m in data["evaluation"]["models"] if m["name"] == "ols_baseline")
    # 25 total. 3 targets dropped, so 22 valid targets. 
    # x2 has 4 nans. One overlaps with target nan? 
    # y = np.arange(25); y[5,10,15] = nan
    # x2 = np.arange(25); x2[2,7,12,17] = nan
    # total valid for OLS = 25 - 3 - 4 = 18? Wait, if no overlap, 7 dropped.
    assert ols["dropped_rows"] > 0
    
def test_evaluate_const_target():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_const_target.csv", "--target-col", "y"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    assert "zero_variance_target" in data["evaluation"]["warnings"]
    
    ols = next(m for m in data["evaluation"]["models"] if m["name"] == "ols_baseline")
    assert ols["r2"] is None
    assert ols["r2_status"] == "not_assessable"

def test_evaluate_non_numeric_feature():
    # split_groups has 'grp' which is non-numeric, if we don't specify --group-col, it is treated as feature.
    res = run_cli(["evaluate", "--input", "tests/fixtures/split_groups.csv", "--target-col", "y"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    assert any(w.startswith("non_numeric_features_excluded (grp)") for w in data["evaluation"]["warnings"])

def test_evaluate_cv_group_requires_group_col():
    res = run_cli(["evaluate", "--input", "tests/fixtures/split_groups.csv", "--target-col", "y", "--cv", "group"])
    assert res.returncode == 4
    
    res2 = run_cli(["evaluate", "--input", "tests/fixtures/split_time.csv", "--target-col", "y", "--cv", "temporal"])
    assert res2.returncode == 4

def test_evaluate_cv_random():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_exact_linear.csv", "--target-col", "y", "--cv", "random", "--folds", "5"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    cv = data["evaluation"]["cv"]
    assert len(cv["folds"]) == 5
    assert cv["aggregate"]["mae_mean"] is not None
    # 40 rows / 5 folds = 8 rows per fold test
    assert all(f["n_test"] == 8 for f in cv["folds"])

def test_evaluate_group_errors():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp", "--split-mode", "random", "--test-size", "0.99"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    ge = data["evaluation"]["group_errors"]
    # 3 groups, each 10 rows. 
    # pred = y + 3 for last 10 rows, which is G3. So G3 MAE = 3.0. G1 and G2 MAE = 0.0.
    g1 = next(g for g in ge["groups"] if g["group"] == "G1")
    g3 = next(g for g in ge["groups"] if g["group"] == "G3")
    
    assert abs(g1["mae"]) < 1e-9
    assert abs(g3["mae"] - 3.0) < 1e-9

def test_evaluate_group_errors_supplied_full_coverage():
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    ge = data["evaluation"]["group_errors"]
    assert ge["coverage_ratio"] == 1.0
    assert ge["worst_by_mae"] == ["G3", "G1", "G2"]
    assert len(ge["groups"]) == 3
    g_map = {g["group"]: g for g in ge["groups"]}
    assert g_map["G1"]["n"] == 10
    assert abs(g_map["G1"]["mae"]) < 1e-9
    assert g_map["G2"]["n"] == 10
    assert abs(g_map["G2"]["mae"]) < 1e-9
    assert g_map["G3"]["n"] == 10
    assert abs(g_map["G3"]["mae"] - 3.0) < 1e-9

def test_evaluate_mae_rmse_group_invariance():
    import numpy as np
    res = run_cli(["evaluate", "--input", "tests/fixtures/eval_preds.csv", "--target-col", "y", "--pred-col", "pred", "--group-col", "grp"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    
    model = next(m for m in data["evaluation"]["models"] if m["name"] == "supplied_predictions")
    global_mae = model["mae"]
    global_rmse = model["rmse"]
    
    ge = data["evaluation"]["group_errors"]
    total_n = sum(g["n"] for g in ge["groups"])
    weighted_mae = sum(g["n"] * g["mae"] for g in ge["groups"]) / total_n
    weighted_mse = sum(g["n"] * (g["rmse"] ** 2) for g in ge["groups"]) / total_n
    weighted_rmse = np.sqrt(weighted_mse)
    
    assert abs(global_mae - weighted_mae) <= 1e-9
    assert abs(global_rmse - weighted_rmse) <= 1e-6

def test_evaluate_uncertainty_calibrated():
    res = run_cli(["evaluate", "--input", "tests/fixtures/intervals_calibrated.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi", "--nominal-coverage", "0.9"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    unc = data["evaluation"]["uncertainty"]
    assert unc["status"] == "performed"
    # Measured coverage: 0.910
    assert 0.85 <= unc["coverage"] <= 0.95
    assert unc["invalid_bounds_rows"] == 0
    assert any(c["name"] == "interval.nominal_gap" and c["result"] == "pass" for c in unc["checks"])
    assert "non_nominal_coverage" not in unc["warnings"]
    
def test_evaluate_uncertainty_overconfident():
    res = run_cli(["evaluate", "--input", "tests/fixtures/intervals_overconfident.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi", "--nominal-coverage", "0.9"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    unc = data["evaluation"]["uncertainty"]
    # Measured coverage: 0.325
    assert unc["coverage"] < 0.5
    assert any(c["name"] == "interval.nominal_gap" and c["result"] == "fail" for c in unc["checks"])
    assert "non_nominal_coverage" in unc["warnings"]
    
def test_evaluate_uncertainty_grouped():
    res = run_cli(["evaluate", "--input", "tests/fixtures/intervals_grouped.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi", "--group-col", "grp", "--nominal-coverage", "0.9"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    unc = data["evaluation"]["uncertainty"]
    assert unc["coverage_by_group"] is not None
    assert len(unc["coverage_by_group"]) == 2
    assert any(c["name"] == "interval.group_coverage_uniformity" and c["result"] == "fail" for c in unc["checks"])
    
    # Measured A: 0.925, B: 0.200
    grp_a = next(g for g in unc["coverage_by_group"] if g["group"] == "A")
    grp_b = next(g for g in unc["coverage_by_group"] if g["group"] == "B")
    assert grp_a["coverage"] >= 0.80
    assert grp_b["coverage"] <= 0.50

def test_evaluate_uncertainty_invalid():
    res = run_cli(["evaluate", "--input", "tests/fixtures/intervals_invalid.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    unc = data["evaluation"]["uncertainty"]
    assert unc["invalid_bounds_rows"] == 3
    assert any(c["name"] == "interval.bounds_valid" and c["result"] == "fail" for c in unc["checks"])
    assert "invalid_bounds" in unc["warnings"]

def test_evaluate_uncertainty_cli_args():
    res = run_cli(["evaluate", "--input", "tests/fixtures/invalid.csv", "--target-col", "y", "--lower-col", "lo"])
    assert res.returncode == 2
    assert "must be provided together" in res.stderr
    
    res2 = run_cli(["evaluate", "--input", "tests/fixtures/invalid.csv", "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi", "--nominal-coverage", "1.5"])
    assert res2.returncode == 2
    assert "must be between 0.0 and 1.0 exclusive" in res2.stderr
