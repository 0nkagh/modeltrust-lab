import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from modeltrust.schema import ColumnSpec
from modeltrust.audit.split import compute_split_indices

SHIFT_MIN_ROWS = 20
CV_MIN_FOLD_SIZE = 3
OOD_FEATURE_OUTSIDE_RATIO_MIN = 0.10
OOD_MAHALANOBIS_RATIO_MIN = 2.0
DRIFT_KS_STAT_MIN = 0.25

def compute_ks_statistic(sample1: np.ndarray, sample2: np.ndarray) -> float:
    """Compute two-sample Kolmogorov-Smirnov statistic D = max|ECDF1 - ECDF2|."""
    s1 = sample1[~np.isnan(sample1)]
    s2 = sample2[~np.isnan(sample2)]
    n1 = len(s1)
    n2 = len(s2)
    if n1 == 0 or n2 == 0:
        return 0.0
    s1 = np.sort(s1)
    s2 = np.sort(s2)
    all_vals = np.concatenate([s1, s2])
    all_vals.sort()
    cdf1 = np.searchsorted(s1, all_vals, side="right") / n1
    cdf2 = np.searchsorted(s2, all_vals, side="right") / n2
    d = np.max(np.abs(cdf1 - cdf2))
    return round(float(d), 6)

def build_shift(
    df: pd.DataFrame,
    spec: ColumnSpec,
    split_mode: str = "random",
    test_size: float = 0.2,
    seed: int = 42
) -> Dict[str, Any]:
    n = len(df)
    warnings: List[str] = []
    checks: List[Dict[str, Any]] = []

    # 1. Compute split indices
    split_status = "performed"
    split_reason = None
    train_idx: List[int] = []
    test_idx: List[int] = []

    try:
        train_idx, test_idx = compute_split_indices(
            df, spec, mode=split_mode, test_size=test_size, seed=seed
        )
    except Exception as e:
        split_status = "not_assessable"
        split_reason = "not_provided" if ("required" in str(e) or "missing" in str(e).lower()) else "insufficient_groups"
        warnings.append(split_reason)

    n_train = len(train_idx)
    n_test = len(test_idx)

    # Check shift.split_available
    if split_status == "performed":
        checks.append({
            "name": "shift.split_available",
            "status": "performed",
            "reason_code": None,
            "result": "pass",
            "detail": f"Split generated using {split_mode} mode"
        })
    else:
        checks.append({
            "name": "shift.split_available",
            "status": "not_assessable",
            "reason_code": split_reason,
            "result": "fail",
            "detail": f"Split not available: {split_reason}"
        })

    # Check shift.row_count
    has_sufficient_rows = (n_train >= SHIFT_MIN_ROWS) and (n_test >= CV_MIN_FOLD_SIZE)
    if has_sufficient_rows:
        checks.append({
            "name": "shift.row_count",
            "status": "performed",
            "reason_code": None,
            "result": "pass",
            "detail": f"Sufficient rows for shift analysis (train={n_train}, test={n_test})"
        })
    else:
        warnings.append("insufficient_rows")
        checks.append({
            "name": "shift.row_count",
            "status": "not_assessable",
            "reason_code": "insufficient_rows",
            "result": "fail",
            "detail": f"Insufficient rows for shift analysis (train={n_train}, test={n_test}, min_train={SHIFT_MIN_ROWS}, min_test={CV_MIN_FOLD_SIZE})"
        })

    # Determine candidate numeric features
    exclude_cols = {spec.target, spec.time, spec.group, spec.subset}
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude_cols]
    numeric_cols = sorted(numeric_cols)

    constant_cols = []
    active_features = []

    if has_sufficient_rows:
        for col in numeric_cols:
            tr_s = df.iloc[train_idx][col].dropna()
            if len(tr_s) <= 1 or tr_s.min() == tr_s.max() or (float(tr_s.std(ddof=1)) == 0.0):
                constant_cols.append(col)
            else:
                active_features.append(col)

    if constant_cols:
        warnings.append(f"constant_features_excluded: {', '.join(sorted(constant_cols))}")

    active_features = sorted(active_features)

    # 2. OOD: feature_range
    if not has_sufficient_rows or split_status != "performed":
        range_reason = "insufficient_rows" if not has_sufficient_rows else split_reason
        ood_feature_range = {
            "status": "not_assessable",
            "reason_code": range_reason,
            "result": "pass",
            "features": [],
            "row_outside_ratio": 0.0,
            "max_feature_outside_ratio": 0.0
        }
        checks.append({
            "name": "ood.feature_range",
            "status": "not_assessable",
            "reason_code": range_reason,
            "result": "pass",
            "detail": f"Diagnostic indicator: feature range not assessable ({range_reason})"
        })
    else:
        range_features = []
        outside_rows_mask = np.zeros(n_test, dtype=bool)

        for col in active_features:
            tr_col = df.iloc[train_idx][col].dropna()
            te_col = df.iloc[test_idx][col]

            tr_min = round(float(tr_col.min()), 6) if len(tr_col) > 0 else 0.0
            tr_max = round(float(tr_col.max()), 6) if len(tr_col) > 0 else 0.0

            valid_te = te_col.dropna()
            is_outside = (valid_te < tr_min) | (valid_te > tr_max)
            n_out = int(is_outside.sum())
            n_te_col = len(valid_te)
            out_ratio = round(float(n_out / n_te_col), 6) if n_te_col > 0 else 0.0

            row_is_out = (te_col < tr_min) | (te_col > tr_max)
            outside_rows_mask |= row_is_out.fillna(False).values

            range_features.append({
                "column": col,
                "train_min": tr_min,
                "train_max": tr_max,
                "outside_ratio": out_ratio,
                "n_outside": n_out
            })

        range_features = sorted(range_features, key=lambda x: x["column"])
        max_feat_out_ratio = round(float(max([f["outside_ratio"] for f in range_features], default=0.0)), 6)
        n_out_rows = int(outside_rows_mask.sum())
        row_out_ratio = round(float(n_out_rows / n_test), 6) if n_test > 0 else 0.0

        if n_out_rows > 0:
            warnings.append("ood_rows_present")

        range_result = "fail" if max_feat_out_ratio >= OOD_FEATURE_OUTSIDE_RATIO_MIN else "pass"
        ood_feature_range = {
            "status": "performed",
            "reason_code": None,
            "result": range_result,
            "features": range_features,
            "row_outside_ratio": row_out_ratio,
            "max_feature_outside_ratio": max_feat_out_ratio
        }
        checks.append({
            "name": "ood.feature_range",
            "status": "performed",
            "reason_code": None,
            "result": range_result,
            "detail": f"Diagnostic indicator: {max_feat_out_ratio:.6f} max outside ratio (heuristic threshold {OOD_FEATURE_OUTSIDE_RATIO_MIN:.2f})"
        })

    # 3. OOD: mahalanobis
    if not has_sufficient_rows or split_status != "performed":
        m_reason = "insufficient_rows" if not has_sufficient_rows else split_reason
        ood_mahalanobis = {
            "status": "not_assessable",
            "reason_code": m_reason,
            "result": "pass",
            "n_features": len(active_features),
            "median_train": None,
            "median_test": None,
            "ratio": None,
            "p95_train": None,
            "p95_test": None
        }
        checks.append({
            "name": "ood.mahalanobis",
            "status": "not_assessable",
            "reason_code": m_reason,
            "result": "pass",
            "detail": f"Diagnostic indicator: Mahalanobis distance not assessable ({m_reason})"
        })
    elif len(active_features) == 0:
        ood_mahalanobis = {
            "status": "not_assessable",
            "reason_code": "degenerate_covariance",
            "result": "pass",
            "n_features": 0,
            "median_train": None,
            "median_test": None,
            "ratio": None,
            "p95_train": None,
            "p95_test": None
        }
        checks.append({
            "name": "ood.mahalanobis",
            "status": "not_assessable",
            "reason_code": "degenerate_covariance",
            "result": "pass",
            "detail": "Diagnostic indicator: Mahalanobis distance not assessable (no active features)"
        })
    else:
        # Full rows across active features
        X_tr_df = df.iloc[train_idx][active_features].dropna()
        X_te_df = df.iloc[test_idx][active_features].dropna()

        n_tr_complete = len(X_tr_df)
        n_te_complete = len(X_te_df)
        n_feat = len(active_features)

        if n_tr_complete < SHIFT_MIN_ROWS or n_feat >= n_tr_complete - 1 or n_te_complete == 0:
            deg_reason = "degenerate_covariance" if n_feat >= n_tr_complete - 1 else "insufficient_rows"
            ood_mahalanobis = {
                "status": "not_assessable",
                "reason_code": deg_reason,
                "result": "pass",
                "n_features": n_feat,
                "median_train": None,
                "median_test": None,
                "ratio": None,
                "p95_train": None,
                "p95_test": None
            }
            checks.append({
                "name": "ood.mahalanobis",
                "status": "not_assessable",
                "reason_code": deg_reason,
                "result": "pass",
                "detail": f"Diagnostic indicator: Mahalanobis distance not assessable ({deg_reason})"
            })
        else:
            X_tr = X_tr_df.values.astype(float)
            X_te = X_te_df.values.astype(float)

            mu = np.mean(X_tr, axis=0)
            cov = np.cov(X_tr, rowvar=False, ddof=1)
            if n_feat == 1:
                cov = np.array([[float(cov)]])
            cov_pinv = np.linalg.pinv(cov)

            diff_tr = X_tr - mu
            d_tr_sq = np.sum((diff_tr @ cov_pinv) * diff_tr, axis=1)
            d_tr = np.sqrt(np.maximum(0.0, d_tr_sq))

            diff_te = X_te - mu
            d_te_sq = np.sum((diff_te @ cov_pinv) * diff_te, axis=1)
            d_te = np.sqrt(np.maximum(0.0, d_te_sq))

            med_tr = round(float(np.median(d_tr)), 6)
            med_te = round(float(np.median(d_te)), 6)
            p95_tr = round(float(np.percentile(d_tr, 95)), 6)
            p95_te = round(float(np.percentile(d_te, 95)), 6)

            if med_tr <= 1e-12:
                ood_mahalanobis = {
                    "status": "not_assessable",
                    "reason_code": "degenerate_covariance",
                    "result": "pass",
                    "n_features": n_feat,
                    "median_train": med_tr,
                    "median_test": med_te,
                    "ratio": None,
                    "p95_train": p95_tr,
                    "p95_test": p95_te
                }
                checks.append({
                    "name": "ood.mahalanobis",
                    "status": "not_assessable",
                    "reason_code": "degenerate_covariance",
                    "result": "pass",
                    "detail": "Diagnostic indicator: Mahalanobis distance not assessable (degenerate_covariance)"
                })
            else:
                m_ratio = round(float(med_te / med_tr), 6)
                m_result = "fail" if m_ratio >= OOD_MAHALANOBIS_RATIO_MIN else "pass"
                ood_mahalanobis = {
                    "status": "performed",
                    "reason_code": None,
                    "result": m_result,
                    "n_features": n_feat,
                    "median_train": med_tr,
                    "median_test": med_te,
                    "ratio": m_ratio,
                    "p95_train": p95_tr,
                    "p95_test": p95_te
                }
                checks.append({
                    "name": "ood.mahalanobis",
                    "status": "performed",
                    "reason_code": None,
                    "result": m_result,
                    "detail": f"Diagnostic indicator: Mahalanobis distance ratio={m_ratio:.6f} (heuristic threshold {OOD_MAHALANOBIS_RATIO_MIN:.2f})"
                })

    # 4. DRIFT: feature_ks & target_ks
    has_time_col = (spec.time is not None) and (spec.time in df.columns)

    if not has_time_col:
        warnings.append("not_provided")
        drift_feature_ks = {
            "status": "not_assessable",
            "reason_code": "not_provided",
            "result": "pass",
            "features": [],
            "max_ks_stat": 0.0
        }
        checks.append({
            "name": "drift.feature_ks",
            "status": "not_assessable",
            "reason_code": "not_provided",
            "result": "pass",
            "detail": "Diagnostic indicator: Feature KS drift not assessable (not_provided)"
        })

        drift_target_ks = {
            "status": "not_assessable",
            "reason_code": "not_provided",
            "result": "pass",
            "ks_stat": 0.0,
            "n_train": 0,
            "n_test": 0
        }
        checks.append({
            "name": "drift.target_ks",
            "status": "not_assessable",
            "reason_code": "not_provided",
            "result": "pass",
            "detail": "Diagnostic indicator: Target KS drift not assessable (not_provided)"
        })
    elif not has_sufficient_rows or split_status != "performed":
        d_reason = "insufficient_rows" if not has_sufficient_rows else split_reason
        drift_feature_ks = {
            "status": "not_assessable",
            "reason_code": d_reason,
            "result": "pass",
            "features": [],
            "max_ks_stat": 0.0
        }
        checks.append({
            "name": "drift.feature_ks",
            "status": "not_assessable",
            "reason_code": d_reason,
            "result": "pass",
            "detail": f"Diagnostic indicator: Feature KS drift not assessable ({d_reason})"
        })

        drift_target_ks = {
            "status": "not_assessable",
            "reason_code": d_reason,
            "result": "pass",
            "ks_stat": 0.0,
            "n_train": 0,
            "n_test": 0
        }
        checks.append({
            "name": "drift.target_ks",
            "status": "not_assessable",
            "reason_code": d_reason,
            "result": "pass",
            "detail": f"Diagnostic indicator: Target KS drift not assessable ({d_reason})"
        })
    else:
        # feature_ks
        feat_ks_list = []
        for col in active_features:
            tr_vals = df.iloc[train_idx][col].dropna().values
            te_vals = df.iloc[test_idx][col].dropna().values
            stat = compute_ks_statistic(tr_vals, te_vals)
            feat_ks_list.append({
                "column": col,
                "ks_stat": stat,
                "n_train": len(tr_vals),
                "n_test": len(te_vals)
            })

        feat_ks_list = sorted(feat_ks_list, key=lambda x: x["column"])
        max_ks = round(float(max([f["ks_stat"] for f in feat_ks_list], default=0.0)), 6)
        ks_res = "fail" if max_ks >= DRIFT_KS_STAT_MIN else "pass"

        drift_feature_ks = {
            "status": "performed",
            "reason_code": None,
            "result": ks_res,
            "features": feat_ks_list,
            "max_ks_stat": max_ks
        }
        checks.append({
            "name": "drift.feature_ks",
            "status": "performed",
            "reason_code": None,
            "result": ks_res,
            "detail": f"Diagnostic indicator: max KS stat={max_ks:.6f} across features (heuristic threshold {DRIFT_KS_STAT_MIN:.2f})"
        })

        # target_ks
        if spec.target is None or spec.target not in df.columns:
            drift_target_ks = {
                "status": "not_assessable",
                "reason_code": "not_provided",
                "result": "pass",
                "ks_stat": 0.0,
                "n_train": 0,
                "n_test": 0
            }
            checks.append({
                "name": "drift.target_ks",
                "status": "not_assessable",
                "reason_code": "not_provided",
                "result": "pass",
                "detail": "Diagnostic indicator: Target KS drift not assessable (not_provided)"
            })
        else:
            tr_y = df.iloc[train_idx][spec.target].dropna().values
            te_y = df.iloc[test_idx][spec.target].dropna().values
            tgt_ks_stat = compute_ks_statistic(tr_y, te_y)
            tgt_res = "fail" if tgt_ks_stat >= DRIFT_KS_STAT_MIN else "pass"

            drift_target_ks = {
                "status": "performed",
                "reason_code": None,
                "result": tgt_res,
                "ks_stat": tgt_ks_stat,
                "n_train": len(tr_y),
                "n_test": len(te_y)
            }
            checks.append({
                "name": "drift.target_ks",
                "status": "performed",
                "reason_code": None,
                "result": tgt_res,
                "detail": f"Diagnostic indicator: target KS stat={tgt_ks_stat:.6f} (heuristic threshold {DRIFT_KS_STAT_MIN:.2f})"
            })

            if ks_res == "fail" or tgt_res == "fail":
                warnings.append("drift_detected")

    # Order warnings strictly:
    # constant_features_excluded, ood_rows_present, drift_detected, insufficient_rows, not_provided
    ordered_prefixes = [
        "constant_features_excluded",
        "ood_rows_present",
        "drift_detected",
        "insufficient_rows",
        "not_provided"
    ]
    final_warnings = []
    for prefix in ordered_prefixes:
        for w in warnings:
            if (w == prefix or w.startswith(prefix + ":") or w.startswith(prefix + " ")) and w not in final_warnings:
                final_warnings.append(w)

    return {
        "shift_schema_version": 1,
        "split": {
            "mode": split_mode,
            "n_train": n_train,
            "n_test": n_test
        },
        "ood": {
            "feature_range": ood_feature_range,
            "mahalanobis": ood_mahalanobis
        },
        "drift": {
            "feature_ks": drift_feature_ks,
            "target_ks": drift_target_ks
        },
        "thresholds": {
            "SHIFT_MIN_ROWS": SHIFT_MIN_ROWS,
            "OOD_FEATURE_OUTSIDE_RATIO_MIN": OOD_FEATURE_OUTSIDE_RATIO_MIN,
            "OOD_MAHALANOBIS_RATIO_MIN": OOD_MAHALANOBIS_RATIO_MIN,
            "DRIFT_KS_STAT_MIN": DRIFT_KS_STAT_MIN
        },
        "checks": checks,
        "warnings": final_warnings,
        "interpretation": "Diagnostic indicators only. Heuristic thresholds; no significance testing is performed. A flagged pattern may be legitimate."
    }
