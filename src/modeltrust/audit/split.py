import hashlib
import numpy as np
import pandas as pd
from typing import Any, Dict, List
from modeltrust.schema import ColumnSpec

def build_split(df: pd.DataFrame, spec: ColumnSpec, mode: str = "all", test_size: float = 0.2, seed: int = 42) -> Dict[str, Any]:
    n = len(df)
    n_test = int(round(test_size * n))
    n_test = max(1, min(n - 1, n_test))
    
    modes_out = {}
    
    # helper for target summary
    def _target_summary(train_idx: List[int], test_idx: List[int]) -> Any:
        if spec.target is None or spec.target not in df.columns:
            return None
        
        y_train = df.iloc[train_idx][spec.target]
        y_test = df.iloc[test_idx][spec.target]
        
        def _stats(s):
            return {
                "mean": round(float(s.mean()), 6),
                "std": round(float(s.std(ddof=1) if len(s)>1 else 0.0), 6),
                "q25": round(float(s.quantile(0.25)), 6),
                "q50": round(float(s.quantile(0.50)), 6),
                "q75": round(float(s.quantile(0.75)), 6),
            }
        
        # Standardized absolute mean difference (Cohen's d with unweighted average sample variance, ddof=1)
        var_train = float(y_train.var(ddof=1) if len(y_train)>1 else 0.0)
        var_test = float(y_test.var(ddof=1) if len(y_test)>1 else 0.0)
        
        abs_std_mean_diff = None
        denom = np.sqrt((var_train + var_test) / 2.0)
        if denom > 0:
            abs_std_mean_diff = round(abs(y_train.mean() - y_test.mean()) / denom, 6)
            
        return {
            "train": _stats(y_train),
            "test": _stats(y_test),
            "abs_std_mean_diff": abs_std_mean_diff
        }
    
    def _row_hash(idx: List[int]) -> str:
        s = ",".join(str(i) for i in sorted(idx))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
        
    def _eval_group_overlap(train_idx: List[int], test_idx: List[int]) -> Dict[str, Any]:
        if spec.group is None or spec.group not in df.columns:
            return {"status": "not_assessable", "reason_code": "not_provided", "count": 0, "ratio_of_smaller": 0.0, "groups": []}
            
        train_grp = set(df.iloc[train_idx][spec.group].astype(str))
        test_grp = set(df.iloc[test_idx][spec.group].astype(str))
        overlap = sorted(list(train_grp.intersection(test_grp)))
        
        ratio = 0.0
        min_sz = min(len(train_grp), len(test_grp))
        if min_sz > 0:
            ratio = round(len(overlap) / min_sz, 6)
            
        return {
            "status": "performed",
            "reason_code": None,
            "count": len(overlap),
            "ratio_of_smaller": ratio,
            "groups": overlap[:5]
        }
        
    def _eval_row_overlap(train_idx: List[int], test_idx: List[int]) -> int:
        exclude = [spec.subset] if spec.subset else []
        cols = [c for c in df.columns if c not in exclude]
        
        df_str = df[cols].astype(str)
        
        row_hashes = df_str.apply(lambda row: hashlib.sha256("".join(str(v) for v in row).encode('utf-8')).hexdigest(), axis=1)
        
        train_h = set(row_hashes.iloc[train_idx])
        test_h = set(row_hashes.iloc[test_idx])
        
        return len(train_h.intersection(test_h))

    # RANDOM
    if mode in ["all", "random"]:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n).tolist()
        test_idx = sorted(perm[:n_test])
        train_idx = sorted(perm[n_test:])
        
        g_ov = _eval_group_overlap(train_idx, test_idx)
        r_ov = _eval_row_overlap(train_idx, test_idx)
        
        target_summ = _target_summary(train_idx, test_idx)
        
        modes_out["random"] = {
            "status": "performed",
            "reason_code": None,
            "n_train": len(train_idx),
            "n_test": len(test_idx),
            "test_fraction": round(len(test_idx) / n, 6),
            "train_row_indices_sha256": _row_hash(train_idx),
            "test_row_indices_sha256": _row_hash(test_idx),
            "row_overlap_count": r_ov,
            "group_overlap": g_ov,
            "time_ranges": {"status": "not_assessable", "reason_code": "not_provided", "train_min": None, "train_max": None, "test_min": None, "test_max": None, "overlaps": None, "boundary_ties": 0},
            "group_assignments": [],
            "target_summary": target_summ
        }
        
    # GROUP
    if mode in ["all", "group"]:
        if spec.group is None or spec.group not in df.columns:
            modes_out["group"] = {
                "status": "not_assessable",
                "reason_code": "not_provided",
                "n_train": 0, "n_test": 0, "test_fraction": 0.0,
                "train_row_indices_sha256": "", "test_row_indices_sha256": "",
                "row_overlap_count": 0,
                "group_overlap": {"status": "not_assessable", "reason_code": "not_provided", "count": 0, "ratio_of_smaller": 0.0, "groups": []},
                "time_ranges": {"status": "not_assessable", "reason_code": "not_provided", "train_min": None, "train_max": None, "test_min": None, "test_max": None, "overlaps": None, "boundary_ties": 0},
                "group_assignments": [],
                "target_summary": None
            }
        else:
            vc = df[spec.group].astype(str).value_counts().reset_index()
            vc.columns = ["grp", "count"]
            vc = vc.sort_values(by=["count", "grp"], ascending=[False, True])
            
            if len(vc) < 2:
                modes_out["group"] = {
                    "status": "not_assessable",
                    "reason_code": "insufficient_groups",
                    "n_train": 0, "n_test": 0, "test_fraction": 0.0,
                    "train_row_indices_sha256": "", "test_row_indices_sha256": "",
                    "row_overlap_count": 0,
                    "group_overlap": {"status": "not_assessable", "reason_code": "insufficient_groups", "count": 0, "ratio_of_smaller": 0.0, "groups": []},
                    "time_ranges": {"status": "not_assessable", "reason_code": "not_provided", "train_min": None, "train_max": None, "test_min": None, "test_max": None, "overlaps": None, "boundary_ties": 0},
                    "group_assignments": [],
                    "target_summary": None
                }
            else:
                test_grp = []
                test_count = 0
                for _, row in vc.iterrows():
                    g = row["grp"]
                    c = row["count"]
                    if test_count < n_test:
                        test_grp.append(g)
                        test_count += c
                        
                # Use absolute integer indices to match perm indexing style
                # Avoid dataframe indices
                group_series = df[spec.group].astype(str)
                is_test = group_series.isin(test_grp)
                train_idx = np.where(~is_test)[0].tolist()
                test_idx = np.where(is_test)[0].tolist()
                
                g_ov = _eval_group_overlap(train_idx, test_idx)
                r_ov = _eval_row_overlap(train_idx, test_idx)
                target_summ = _target_summary(train_idx, test_idx)
                
                assignments = []
                for g in test_grp:
                    assignments.append({"group": g, "rows": int(group_series.eq(g).sum()), "side": "test"})
                train_g = set(group_series) - set(test_grp)
                for g in sorted(list(train_g)):
                    assignments.append({"group": g, "rows": int(group_series.eq(g).sum()), "side": "train"})
                    
                assignments = sorted(assignments, key=lambda x: x["group"])
                
                modes_out["group"] = {
                    "status": "performed",
                    "reason_code": None,
                    "n_train": len(train_idx),
                    "n_test": len(test_idx),
                    "test_fraction": round(len(test_idx) / n, 6) if n > 0 else 0.0,
                    "train_row_indices_sha256": _row_hash(train_idx),
                    "test_row_indices_sha256": _row_hash(test_idx),
                    "row_overlap_count": r_ov,
                    "group_overlap": g_ov,
                    "time_ranges": {"status": "not_assessable", "reason_code": "not_provided", "train_min": None, "train_max": None, "test_min": None, "test_max": None, "overlaps": None, "boundary_ties": 0},
                    "group_assignments": assignments,
                    "target_summary": target_summ
                }
                
    # TEMPORAL
    if mode in ["all", "temporal"]:
        if spec.time is None or spec.time not in df.columns:
            modes_out["temporal"] = {
                "status": "not_assessable",
                "reason_code": "not_provided",
                "n_train": 0, "n_test": 0, "test_fraction": 0.0,
                "train_row_indices_sha256": "", "test_row_indices_sha256": "",
                "row_overlap_count": 0,
                "group_overlap": {"status": "not_assessable", "reason_code": "not_provided", "count": 0, "ratio_of_smaller": 0.0, "groups": []},
                "time_ranges": {"status": "not_assessable", "reason_code": "not_provided", "train_min": None, "train_max": None, "test_min": None, "test_max": None, "overlaps": None, "boundary_ties": 0},
                "group_assignments": [],
                "target_summary": None
            }
        else:
            df_time = pd.to_datetime(df[spec.time], errors="coerce")
            
            # create sort keys, sort by time and original index
            sort_df = pd.DataFrame({"time": df_time, "orig_idx": np.arange(n)})
            sort_df = sort_df.sort_values(by=["time", "orig_idx"])
            
            n_train_actual = n - n_test
            train_idx = sort_df.iloc[:n_train_actual]["orig_idx"].tolist()
            test_idx = sort_df.iloc[n_train_actual:]["orig_idx"].tolist()
            
            # evaluate boundary ties
            boundary_ties = 0
            if n_train_actual > 0 and n_train_actual < n:
                train_max_val = df_time.iloc[train_idx[-1]]
                test_min_val = df_time.iloc[test_idx[0]]
                if not pd.isna(train_max_val) and not pd.isna(test_min_val) and train_max_val == test_min_val:
                    boundary_ties = int(df_time.eq(train_max_val).sum())
                    
            train_min = str(df_time.iloc[train_idx].min()) if len(train_idx) > 0 and not pd.isna(df_time.iloc[train_idx].min()) else None
            train_max = str(df_time.iloc[train_idx].max()) if len(train_idx) > 0 and not pd.isna(df_time.iloc[train_idx].max()) else None
            test_min = str(df_time.iloc[test_idx].min()) if len(test_idx) > 0 and not pd.isna(df_time.iloc[test_idx].min()) else None
            test_max = str(df_time.iloc[test_idx].max()) if len(test_idx) > 0 and not pd.isna(df_time.iloc[test_idx].max()) else None
            
            overlaps = False
            if train_max is not None and test_min is not None:
                overlaps = train_max >= test_min
                
            time_ranges = {
                "status": "performed",
                "reason_code": None,
                "train_min": train_min,
                "train_max": train_max,
                "test_min": test_min,
                "test_max": test_max,
                "overlaps": overlaps,
                "boundary_ties": boundary_ties
            }
            
            g_ov = _eval_group_overlap(train_idx, test_idx)
            r_ov = _eval_row_overlap(train_idx, test_idx)
            target_summ = _target_summary(train_idx, test_idx)
            
            modes_out["temporal"] = {
                "status": "performed",
                "reason_code": None,
                "n_train": len(train_idx),
                "n_test": len(test_idx),
                "test_fraction": round(len(test_idx) / n, 6),
                "train_row_indices_sha256": _row_hash(train_idx),
                "test_row_indices_sha256": _row_hash(test_idx),
                "row_overlap_count": r_ov,
                "group_overlap": g_ov,
                "time_ranges": time_ranges,
                "group_assignments": [],
                "target_summary": target_summ
            }

    # COMPARISON array
    comp = []
    checks = []
    warnings = []
    
    if spec.target is None:
        warnings.append("target_not_provided")
        
    ordered_warns = ["target_not_provided","group_not_provided","time_not_provided","insufficient_rows","insufficient_groups","zero_variance_target","boundary_ties","duplicate_rows_cross_split","truncated_input"]
        
    for m in ["random", "group", "temporal"]:
        if m in modes_out:
            obj = modes_out[m]
            
            comp.append({
                "mode": m,
                "n_train": obj["n_train"],
                "n_test": obj["n_test"],
                "test_fraction": obj["test_fraction"],
                "row_overlap_count": obj["row_overlap_count"] if obj["status"] == "performed" else 0,
                "group_overlap_count": obj["group_overlap"]["count"] if obj["status"] == "performed" and obj["group_overlap"]["status"] == "performed" else None,
                "time_ranges_overlap": obj["time_ranges"]["overlaps"] if obj["status"] == "performed" and obj["time_ranges"]["status"] == "performed" else None,
                "abs_std_mean_diff": obj["target_summary"]["abs_std_mean_diff"] if obj["status"] == "performed" and obj["target_summary"] is not None else None,
                "train_row_indices_sha256": obj["train_row_indices_sha256"]
            })
            
            if obj["status"] == "performed":
                # split_sizes_sane
                size_fail = (obj["n_train"] == 0 or obj["n_test"] == 0)
                checks.append({
                    "name": "split_sizes_sane",
                    "status": "performed",
                    "result": "fail" if size_fail else "pass",
                    "reason_code": None,
                    "detail": "Split has zero sizes" if size_fail else "",
                    "evidence": {"n_train": obj["n_train"], "n_test": obj["n_test"]}
                })
                
                # specific checks
                if m == "random":
                    # random_split_group_leakage
                    if spec.group is not None:
                        gfail = obj["group_overlap"]["count"] > 0
                        checks.append({
                            "name": "random_split_group_leakage",
                            "status": "performed",
                            "result": "fail" if gfail else "pass",
                            "reason_code": None,
                            "detail": "Groups leak across random split" if gfail else "",
                            "evidence": {
                                "count": obj["group_overlap"]["count"],
                                "ratio_of_smaller": obj["group_overlap"]["ratio_of_smaller"],
                                "groups": obj["group_overlap"]["groups"]
                            }
                        })
                    
                    # random_split_row_overlap
                    rfail = obj["row_overlap_count"] > 0
                    checks.append({
                        "name": "random_split_row_overlap",
                        "status": "performed",
                        "result": "fail" if rfail else "pass",
                        "reason_code": None,
                        "detail": "Exact rows leak across split" if rfail else "",
                        "evidence": {"count": obj["row_overlap_count"]}
                    })
                    
                    if rfail and "duplicate_rows_cross_split" not in warnings:
                        warnings.append("duplicate_rows_cross_split")
                            
                elif m == "group":
                    gfail = obj["group_overlap"]["count"] > 0
                    checks.append({
                        "name": "group_split_disjointness",
                        "status": "performed",
                        "result": "fail" if gfail else "pass",
                        "reason_code": None,
                        "detail": "Group split is not strictly disjoint" if gfail else "",
                        "evidence": {
                            "count": obj["group_overlap"]["count"],
                            "groups": obj["group_overlap"]["groups"]
                        }
                    })
                    
                elif m == "temporal":
                    ov = obj["time_ranges"]["overlaps"]
                    checks.append({
                        "name": "temporal_split_ordering",
                        "status": "performed",
                        "result": "fail" if ov else "pass",
                        "reason_code": None,
                        "detail": "Temporal split boundary is overlapped or reversed" if ov else "",
                        "evidence": {
                            "train_max": obj["time_ranges"]["train_max"],
                            "test_min": obj["time_ranges"]["test_min"],
                            "boundary_ties": obj["time_ranges"]["boundary_ties"]
                        }
                    })
                    if obj["time_ranges"]["boundary_ties"] > 0 and "boundary_ties" not in warnings:
                        warnings.append("boundary_ties")
                    
                    if spec.group is not None:
                        gfail = obj["group_overlap"]["count"] > 0
                        checks.append({
                            "name": "temporal_split_group_leakage",
                            "status": "performed",
                            "result": "fail" if gfail else "pass",
                            "reason_code": None,
                            "detail": "Groups overlap across temporal boundary" if gfail else "",
                            "evidence": {
                                "count": obj["group_overlap"]["count"],
                                "groups": obj["group_overlap"]["groups"]
                            }
                        })
                        
            if obj["status"] == "performed" and obj["target_summary"] is not None:
                if obj["target_summary"]["abs_std_mean_diff"] is None:
                    if "zero_variance_target" not in warnings:
                        warnings.append("zero_variance_target")
                        
            if obj["reason_code"] == "insufficient_groups":
                if "insufficient_groups" not in warnings:
                    warnings.append("insufficient_groups")
    
    if spec.group is None and mode in ["all", "group"] and "group_not_provided" not in warnings:
        warnings.append("group_not_provided")
    if spec.time is None and mode in ["all", "temporal"] and "time_not_provided" not in warnings:
        warnings.append("time_not_provided")
        
    return {
        "split_schema_version": 1,
        "config": {
            "mode": mode,
            "test_size": test_size,
            "seed": seed,
            "random_method": "numpy.random.default_rng(seed).permutation",
            "fingerprint_excludes": [spec.subset] if spec.subset else []
        },
        "modes": modes_out,
        "comparison": comp,
        "checks": checks,
        "warnings": [w for w in ordered_warns if w in warnings],
        "interpretation": "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage."
    }
