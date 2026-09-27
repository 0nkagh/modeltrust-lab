import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

def compute_metrics(y_true, y_pred, warn_list: List[str]) -> Dict[str, Any]:
    mask = y_true.notna() & (y_pred.notna() if isinstance(y_pred, pd.Series) else ~np.isnan(y_pred))
    y_t = y_true[mask]
    y_p = y_pred[mask] if isinstance(y_pred, pd.Series) else y_pred[mask]
    
    n_scored = len(y_t)
    if n_scored == 0:
        return {"mae": 0.0, "rmse": 0.0, "r2": None, "r2_status": "not_assessable", "n_scored": 0}
        
    y_t_arr = np.array(y_t, dtype=float)
    y_p_arr = np.array(y_p, dtype=float)
        
    mae = np.mean(np.abs(y_t_arr - y_p_arr))
    rmse = np.sqrt(np.mean((y_t_arr - y_p_arr)**2))
    
    mean_y = np.mean(y_t_arr)
    ss_tot = np.sum((y_t_arr - mean_y)**2)
    ss_res = np.sum((y_t_arr - y_p_arr)**2)
    
    if ss_tot == 0:
        r2 = None
        r2_status = "not_assessable"
        if "zero_variance_target" not in warn_list:
            warn_list.append("zero_variance_target")
    else:
        r2 = 1.0 - (ss_res / ss_tot)
        r2_status = "performed"
        
    return {
        "mae": round(float(mae), 6),
        "rmse": round(float(rmse), 6),
        "r2": round(float(r2), 6) if r2 is not None else None,
        "r2_status": r2_status,
        "n_scored": n_scored
    }

def train_ols(X_train: pd.DataFrame, y_train: pd.Series):
    X = np.c_[np.ones(X_train.shape[0]), X_train.values]
    coeffs, _, _, _ = np.linalg.lstsq(X, y_train.values, rcond=None)
    return coeffs

def predict_ols(coeffs: np.ndarray, X_test: pd.DataFrame) -> pd.Series:
    X = np.c_[np.ones(X_test.shape[0]), X_test.values]
    preds = X @ coeffs
    return pd.Series(preds, index=X_test.index)

def split_random(n: int, seed: int, n_test: int):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n).tolist()
    return sorted(perm[n_test:]), sorted(perm[:n_test])

def split_group(df: pd.DataFrame, group_col: str, n_test: int):
    vc = df[group_col].astype(str).value_counts().reset_index()
    vc.columns = ["grp", "count"]
    vc = vc.sort_values(by=["count", "grp"], ascending=[False, True])
    test_grp = []
    test_count = 0
    for _, row in vc.iterrows():
        g = row["grp"]
        c = row["count"]
        if test_count < n_test:
            test_grp.append(g)
            test_count += c
    is_test = df[group_col].astype(str).isin(test_grp)
    return np.where(~is_test)[0].tolist(), np.where(is_test)[0].tolist()

def split_temporal(df: pd.DataFrame, time_col: str, n_test: int):
    df_time = pd.to_datetime(df[time_col], errors="coerce")
    sort_df = pd.DataFrame({"time": df_time, "orig_idx": np.arange(len(df))})
    sort_df = sort_df.sort_values(by=["time", "orig_idx"])
    n_train_actual = len(df) - n_test
    train_idx = sort_df.iloc[:n_train_actual]["orig_idx"].tolist()
    test_idx = sort_df.iloc[n_train_actual:]["orig_idx"].tolist()
    return train_idx, test_idx

def do_cv(df: pd.DataFrame, spec: Any, X_full: pd.DataFrame, y_full: pd.Series, cv_mode: str, folds: int, seed: int, model: str, warnings: List[str]):
    n = len(df)
    if cv_mode == "none":
        warnings.append("cv_not_requested")
        return {"status": "not_assessable", "reason_code": "not_provided", "scheme": "none", "folds_requested": folds, "folds": [], "aggregate": {}}
        
    if n < 10:
        warnings.append("insufficient_rows")
        return {"status": "not_assessable", "reason_code": "insufficient_rows", "scheme": cv_mode, "folds_requested": folds, "folds": [], "aggregate": {}}
        
    fold_indices = []
    
    if cv_mode == "random":
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n).tolist()
        base = n // folds
        rem = n % folds
        start = 0
        for i in range(folds):
            size = base + (1 if i < rem else 0)
            test_idx = perm[start:start+size]
            train_idx = perm[:start] + perm[start+size:]
            fold_indices.append((train_idx, test_idx))
            start += size
            
    elif cv_mode == "group":
        vc = df[spec.group].astype(str).value_counts().reset_index()
        vc.columns = ["grp", "count"]
        vc = vc.sort_values(by=["count", "grp"], ascending=[False, True])
        
        fold_sizes = [0]*folds
        fold_grps = [[] for _ in range(folds)]
        for _, row in vc.iterrows():
            g = row["grp"]
            c = row["count"]
            idx = np.argmin(fold_sizes)
            fold_sizes[idx] += c
            fold_grps[idx].append(g)
            
        group_series = df[spec.group].astype(str)
        for i in range(folds):
            test_is = group_series.isin(fold_grps[i])
            test_idx = np.where(test_is)[0].tolist()
            train_idx = np.where(~test_is)[0].tolist()
            fold_indices.append((train_idx, test_idx))
            
    elif cv_mode == "temporal":
        df_time = pd.to_datetime(df[spec.time], errors="coerce")
        sort_df = pd.DataFrame({"time": df_time, "orig_idx": np.arange(n)})
        sort_df = sort_df.sort_values(by=["time", "orig_idx"])
        
        base = n // folds
        rem = n % folds
        start = 0
        for i in range(folds):
            size = base + (1 if i < rem else 0)
            test_idx = sort_df.iloc[start:start+size]["orig_idx"].tolist()
            train_idx = sort_df.iloc[:start]["orig_idx"].tolist() + sort_df.iloc[start+size:]["orig_idx"].tolist()
            fold_indices.append((train_idx, test_idx))
            start += size
            
    out_folds = []
    maes = []
    rmses = []
    r2s = []
    
    for i, (train_idx, test_idx) in enumerate(fold_indices):
        if len(test_idx) < 3:
            if "insufficient_rows" not in warnings: warnings.append("insufficient_rows")
            return {"status": "not_assessable", "reason_code": "insufficient_rows", "scheme": cv_mode, "folds_requested": folds, "folds": [], "aggregate": {}}
            
        y_train = y_full.iloc[train_idx]
        X_train = X_full.iloc[train_idx]
        y_test = y_full.iloc[test_idx]
        X_test = X_full.iloc[test_idx]
        
        if model in ["ols", "both"]:
            train_valid = y_train.notna() & X_train.notna().all(axis=1)
            if train_valid.sum() == 0:
                if "insufficient_rows" not in warnings: warnings.append("insufficient_rows")
                return {"status": "not_assessable", "reason_code": "insufficient_rows", "scheme": cv_mode, "folds_requested": folds, "folds": [], "aggregate": {}}
            coeffs = train_ols(X_train[train_valid], y_train[train_valid])
            preds = predict_ols(coeffs, X_test)
        elif model == "mean":
            train_valid = y_train.notna()
            mean_val = y_train[train_valid].mean() if train_valid.any() else 0.0
            preds = pd.Series(mean_val, index=y_test.index)
        elif model == "supplied":
            preds = df[spec.prediction].iloc[test_idx]
            
        metrics = compute_metrics(y_test, preds, warnings)
        
        n_grps_tr = 0
        n_grps_te = 0
        if spec.group:
            g_tr = set(df.iloc[train_idx][spec.group].astype(str))
            g_te = set(df.iloc[test_idx][spec.group].astype(str))
            n_grps_tr = len(g_tr)
            n_grps_te = len(g_te)
            
        maes.append(metrics["mae"])
        rmses.append(metrics["rmse"])
        if metrics["r2"] is not None:
            r2s.append(metrics["r2"])
            
        out_folds.append({
            "fold": i + 1,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "n_groups_train": int(n_grps_tr),
            "n_groups_test": int(n_grps_te),
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"]
        })
        
    return {
        "status": "performed",
        "reason_code": None,
        "scheme": cv_mode,
        "folds_requested": folds,
        "folds": out_folds,
        "aggregate": {
            "mae_mean": round(float(np.mean(maes)), 6),
            "mae_std": round(float(np.std(maes, ddof=1) if len(maes)>1 else 0.0), 6),
            "rmse_mean": round(float(np.mean(rmses)), 6),
            "r2_mean": round(float(np.mean(r2s)), 6) if r2s else None
        }
    }

def compute_group_errors(df, spec, X_full, y_full, test_idx, train_idx, model, warnings):
    if not spec.group:
        return {"status": "not_assessable", "reason_code": "not_provided", "model": None, "groups": [], "worst_by_mae": [], "coverage_ratio": 0.0}
        
    rep_model = "ols_baseline"
    if model == "supplied":
        y_test = y_full
        preds = df[spec.prediction]
        groups = df[spec.group].astype(str)
        rep_model = "supplied_predictions"
    else:
        y_test = y_full.iloc[test_idx]
        X_test = X_full.iloc[test_idx]
        groups = df.iloc[test_idx][spec.group].astype(str)
        if model in ["ols", "both"]:
            y_train = y_full.iloc[train_idx]
            X_train = X_full.iloc[train_idx]
            train_valid = y_train.notna() & X_train.notna().all(axis=1)
            if train_valid.sum() == 0:
                rep_model = "mean_baseline" if model == "both" else "ols_baseline"
            else:
                coeffs = train_ols(X_train[train_valid], y_train[train_valid])
                preds = predict_ols(coeffs, X_test)
                
        if rep_model == "mean_baseline" or (model == "both" and "preds" not in locals()):
            y_train = y_full.iloc[train_idx]
            valid_train = y_train.notna()
            mean_val = y_train[valid_train].mean() if valid_train.any() else 0.0
            preds = pd.Series(mean_val, index=y_test.index)
            rep_model = "mean_baseline"
    
    valid_mask = y_test.notna() & (preds.notna() if isinstance(preds, pd.Series) else ~np.isnan(preds))
    valid_y = y_test[valid_mask]
    valid_p = preds[valid_mask]
    valid_g = groups[valid_mask]
    
    out_groups = []
    
    for g_name, g_idx in valid_g.groupby(valid_g).groups.items():
        sub_y = valid_y.loc[g_idx]
        sub_p = valid_p.loc[g_idx]
        n_g = len(sub_y)
        
        mae = np.mean(np.abs(sub_y - sub_p))
        rmse = np.sqrt(np.mean((sub_y - sub_p)**2))
        m_res = np.mean(sub_y - sub_p)
        
        out_groups.append({
            "group": str(g_name),
            "n": int(n_g),
            "mae": round(float(mae), 6),
            "rmse": round(float(rmse), 6),
            "mean_residual": round(float(m_res), 6)
        })
        
    out_groups.sort(key=lambda x: x["group"])
    
    valid_for_worst = [g for g in out_groups if g["n"] >= 5]
    if len(valid_for_worst) < len(out_groups) and "insufficient_group_rows" not in warnings:
        warnings.append("insufficient_group_rows")
        
    worst = sorted(valid_for_worst, key=lambda x: (-x["mae"], x["group"]))[:3]
    worst_names = [w["group"] for w in worst]
    
    total_valid = sum(g["n"] for g in out_groups)
    coverage = sum(g["n"] for g in valid_for_worst) / total_valid if total_valid > 0 else 0.0
    
    return {
        "status": "performed",
        "reason_code": None,
        "model": rep_model,
        "groups": out_groups,
        "worst_by_mae": worst_names,
        "coverage_ratio": round(float(coverage), 6)
    }

def build_evaluation(df: pd.DataFrame, spec: Any, model: str, split_mode: str, test_size: float, cv: str, folds: int, seed: int) -> Dict[str, Any]:
    warnings = []
    n = len(df)
    target_col = spec.target
    
    exclude_cols = [target_col]
    if spec.prediction: exclude_cols.append(spec.prediction)
    if spec.group: exclude_cols.append(spec.group)
    if spec.time: exclude_cols.append(spec.time)
    if spec.subset: exclude_cols.append(spec.subset)
    
    numeric_features = []
    non_numeric = []
    for c in df.columns:
        if c in exclude_cols: continue
        if pd.api.types.is_numeric_dtype(df[c]):
            numeric_features.append(c)
        else:
            non_numeric.append(c)
            
    if non_numeric:
        warnings.append(f"non_numeric_features_excluded ({', '.join(non_numeric)})")
        
    X_full = df[numeric_features]
    y_full = df[target_col]
    
    # 1. Baseline Split (Single Holdout)
    n_test = int(round(test_size * n))
    n_test = max(1, min(n - 1, n_test))
    
    if split_mode == "group":
        train_idx, test_idx = split_group(df, spec.group, n_test)
    elif split_mode == "temporal":
        train_idx, test_idx = split_temporal(df, spec.time, n_test)
    else:
        train_idx, test_idx = split_random(n, seed, n_test)
        
    models_out = []
    
    if model in ["mean", "both"]:
        y_train = y_full.iloc[train_idx]
        y_test = y_full.iloc[test_idx]
        
        valid_train = y_train.notna()
        mean_val = y_train[valid_train].mean() if valid_train.any() else 0.0
        
        preds = pd.Series(mean_val, index=y_test.index)
        metrics = compute_metrics(y_test, preds, warnings)
        
        models_out.append({
            "name": "mean_baseline",
            "status": "performed",
            "reason_code": None,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "n_scored": int(metrics["n_scored"]),
            "dropped_rows": 0,
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
            "r2_status": metrics["r2_status"]
        })
        
    if model in ["ols", "both"]:
        y_train = y_full.iloc[train_idx]
        X_train = X_full.iloc[train_idx]
        
        train_valid = y_train.notna() & X_train.notna().all(axis=1)
        dropped_train = int(len(train_idx) - train_valid.sum())
        
        if dropped_train > 0 and "dropped_rows_due_to_nan" not in warnings:
            warnings.append("dropped_rows_due_to_nan")
            
        if train_valid.sum() == 0:
            models_out.append({
                "name": "ols_baseline",
                "status": "not_assessable",
                "reason_code": "insufficient_rows",
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "n_scored": 0,
                "dropped_rows": dropped_train,
                "mae": 0.0, "rmse": 0.0, "r2": None, "r2_status": "not_assessable"
            })
        else:
            coeffs = train_ols(X_train[train_valid], y_train[train_valid])
            y_test = y_full.iloc[test_idx]
            X_test = X_full.iloc[test_idx]
            preds = predict_ols(coeffs, X_test)
            metrics = compute_metrics(y_test, preds, warnings)
            
            models_out.append({
                "name": "ols_baseline",
                "status": "performed",
                "reason_code": None,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "n_scored": int(metrics["n_scored"]),
                "dropped_rows": dropped_train,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "r2": metrics["r2"],
                "r2_status": metrics["r2_status"]
            })
            
    if model == "supplied":
        y_test = y_full
        preds = df[spec.prediction]
        metrics = compute_metrics(y_test, preds, warnings)
        
        models_out.append({
            "name": "supplied_predictions",
            "status": "performed",
            "reason_code": None,
            "n_train": 0,
            "n_test": int(n),
            "n_scored": int(metrics["n_scored"]),
            "dropped_rows": 0,
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
            "r2_status": metrics["r2_status"]
        })
        
    cv_res = do_cv(df, spec, X_full, y_full, cv, folds, seed, model, warnings)
    ge_res = compute_group_errors(df, spec, X_full, y_full, test_idx, train_idx, model, warnings)
    
    checks = []
    checks.append({
        "name": "metrics_computed",
        "status": "performed",
        "result": "pass",
        "reason_code": None,
        "detail": "",
        "evidence": {}
    })
    
    tgt_num = pd.api.types.is_numeric_dtype(y_full)
    checks.append({
        "name": "target_type_numeric",
        "status": "performed",
        "result": "pass" if tgt_num else "fail",
        "reason_code": None,
        "detail": "Target is not numeric" if not tgt_num else "",
        "evidence": {}
    })
    
    r2_def = "zero_variance_target" not in warnings
    checks.append({
        "name": "r2_target_variance_defined",
        "status": "performed",
        "result": "pass" if r2_def else "fail",
        "reason_code": None,
        "detail": "Target variance is zero" if not r2_def else "",
        "evidence": {}
    })
    
    cv_sane = cv_res["status"] == "performed"
    checks.append({
        "name": "cv_folds_size_sane",
        "status": "performed" if cv_res["scheme"] != "none" else "not_assessable",
        "result": "pass" if cv_sane else "fail",
        "reason_code": None if cv_res["scheme"] != "none" else "not_provided",
        "detail": "CV folds are not sane" if not cv_sane and cv_res["scheme"] != "none" else "",
        "evidence": {}
    })
    
    cov_ratio = ge_res["coverage_ratio"]
    checks.append({
        "name": "group_error_coverage",
        "status": "performed" if spec.group else "not_assessable",
        "result": "pass" if cov_ratio == 1.0 else "fail",
        "reason_code": None if spec.group else "not_provided",
        "detail": "Not all groups are covered" if cov_ratio < 1.0 and spec.group else "",
        "evidence": {"coverage_ratio": cov_ratio}
    })
    
    supplied = bool(spec.prediction)
    checks.append({
        "name": "supplied_predictions_present",
        "status": "performed" if supplied else "not_assessable",
        "result": "pass" if supplied else "fail",
        "reason_code": None if supplied else "not_provided",
        "detail": "",
        "evidence": {}
    })
    
    ordered_warns = ["zero_variance_target","non_numeric_features_excluded","dropped_rows_due_to_nan","insufficient_rows","insufficient_group_rows","cv_not_requested","truncated_input"]
    
    final_warns = []
    for base_w in ordered_warns:
        for actual_w in warnings:
            if actual_w == base_w or actual_w.startswith(base_w + " "):
                final_warns.append(actual_w)
    
    return {
        "evaluation_schema_version": 1,
        "target": target_col,
        "models": models_out,
        "cv": cv_res,
        "group_errors": ge_res,
        "thresholds": {"MIN_ROWS_FOR_METRICS": 10, "MIN_GROUP_ROWS_FOR_ERROR": 5, "TOP_WORST_GROUPS": 3, "CV_MIN_FOLD_SIZE": 3},
        "checks": checks,
        "warnings": final_warns,
        "interpretation": "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage."
    }
