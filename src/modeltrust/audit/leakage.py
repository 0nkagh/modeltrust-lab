import pandas as pd
import numpy as np
import hashlib
from typing import Any
from modeltrust.schema import ColumnSpec

MIN_ROWS_FOR_COPY_CHECK = 5
MIN_PAIRS_FOR_CORRELATION = 20
MIN_ROWS_FOR_INDEX_CHECK = 10
EXACT_COPY_EQUALITY_RATIO = 1.0
NEAR_COPY_CORR_ABS_MIN = 0.999
INDEX_LIKE_UNIQUE_RATIO_MIN = 0.99
ATOL_NUMERIC_EQUALITY = 1e-12
EXAMPLE_LIMIT = 5

def build_leakage(df: pd.DataFrame, spec: ColumnSpec) -> dict[str, Any]:
    n_rows = len(df)
    
    special_cols = [spec.target, spec.prediction, spec.group, spec.time, spec.subset]
    special_cols = [c for c in special_cols if c is not None]
    feature_cols = [c for c in df.columns if c not in special_cols]
    
    checks = []
    
    # 1. target_copy_exact
    target_exact_fail = False
    exact_evidence = []
    if spec.target and spec.target in df.columns:
        if n_rows < MIN_ROWS_FOR_COPY_CHECK:
            checks.append({
                "name": "target_copy_exact",
                "status": "not_assessable",
                "result": None,
                "reason_code": "insufficient_rows",
                "detail": "Not enough rows for exact copy check",
                "evidence": None
            })
        else:
            target_s = df[spec.target]
            target_is_num = pd.api.types.is_numeric_dtype(target_s)
            target_na = target_s.isna()
            
            for col in feature_cols:
                col_s = df[col]
                col_na = col_s.isna()
                both_na = target_na & col_na
                
                if target_is_num and pd.api.types.is_numeric_dtype(col_s):
                    diff = (col_s - target_s).abs()
                    num_match = (diff <= ATOL_NUMERIC_EQUALITY)
                    match_ratio = (num_match | both_na).sum() / n_rows
                else:
                    match_ratio = ((col_s.astype(str) == target_s.astype(str)) | both_na).sum() / n_rows
                    
                if match_ratio >= EXACT_COPY_EQUALITY_RATIO:
                    target_exact_fail = True
                    exact_evidence.append({"column": str(col), "equality_ratio": round(float(match_ratio), 6)})
            
            checks.append({
                "name": "target_copy_exact",
                "status": "performed",
                "result": "fail" if target_exact_fail else "pass",
                "reason_code": None,
                "detail": "Target exact copy found" if target_exact_fail else "",
                "evidence": sorted(exact_evidence, key=lambda x: x["column"])[:EXAMPLE_LIMIT] if exact_evidence else None
            })
    else:
        checks.append({
            "name": "target_copy_exact",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": "",
            "evidence": None
        })

    # 2. target_copy_near
    target_near_fail = False
    near_evidence = []
    if spec.target and spec.target in df.columns:
        if n_rows < MIN_PAIRS_FOR_CORRELATION:
            checks.append({
                "name": "target_copy_near",
                "status": "not_assessable",
                "result": None,
                "reason_code": "insufficient_rows",
                "detail": "Not enough rows for near copy correlation check",
                "evidence": None
            })
        else:
            target_s = df[spec.target]
            target_na = target_s.isna()
            if pd.api.types.is_numeric_dtype(target_s):
                for col in feature_cols:
                    col_s = df[col]
                    if pd.api.types.is_numeric_dtype(col_s):
                        mask = target_s.notna() & col_s.notna()
                        if mask.sum() >= MIN_PAIRS_FOR_CORRELATION:
                            corr = target_s[mask].corr(col_s[mask])
                            if pd.notna(corr) and abs(corr) >= NEAR_COPY_CORR_ABS_MIN:
                                diff = (col_s - target_s).abs()
                                col_na = col_s.isna()
                                both_na = target_na & col_na
                                match_ratio = ((diff <= ATOL_NUMERIC_EQUALITY) | both_na).sum() / n_rows
                                if match_ratio < EXACT_COPY_EQUALITY_RATIO:
                                    target_near_fail = True
                                    near_evidence.append({"column": str(col), "abs_correlation": round(float(abs(corr)), 6), "equality_ratio": round(float(match_ratio), 6)})
            
            checks.append({
                "name": "target_copy_near",
                "status": "performed",
                "result": "fail" if target_near_fail else "pass",
                "reason_code": None,
                "detail": "Target near copy found" if target_near_fail else "",
                "evidence": sorted(near_evidence, key=lambda x: x["column"])[:EXAMPLE_LIMIT] if near_evidence else None
            })
    else:
        checks.append({
            "name": "target_copy_near",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": "",
            "evidence": None
        })

    # 3. index_like_feature
    index_like_fail = False
    index_evidence = []
    if n_rows < MIN_ROWS_FOR_INDEX_CHECK:
        checks.append({
            "name": "index_like_feature",
            "status": "not_assessable",
            "result": None,
            "reason_code": "insufficient_rows",
            "detail": "",
            "evidence": None
        })
    else:
        for col in feature_cols:
            col_s = df[col]
            is_int = pd.api.types.is_integer_dtype(col_s)
            if not is_int and pd.api.types.is_numeric_dtype(col_s):
                # Check if all non-null values are integers
                valid_mask = col_s.notna()
                if valid_mask.any():
                    is_int = (col_s[valid_mask] == col_s[valid_mask].astype(int)).all()

            n_unique = col_s.nunique(dropna=True)
            unique_ratio = n_unique / n_rows
            
            is_monotonic = False
            if is_int:
                valid_mask = col_s.notna()
                if valid_mask.any():
                    # check if strictly monotonically increasing
                    diffs = col_s[valid_mask].diff().dropna()
                    is_monotonic = bool((diffs > 0).all()) if len(diffs) > 0 else True
                    
            if is_int and unique_ratio >= INDEX_LIKE_UNIQUE_RATIO_MIN and is_monotonic:
                index_like_fail = True
                index_evidence.append({
                    "column": str(col), 
                    "unique_ratio": round(float(unique_ratio), 6),
                    "is_monotonic_increasing": True,
                    "is_integer_dtype": True
                })
        
        checks.append({
            "name": "index_like_feature",
            "status": "performed",
            "result": "fail" if index_like_fail else "pass",
            "reason_code": None,
            "detail": "Index-like feature found" if index_like_fail else "",
            "evidence": sorted(index_evidence, key=lambda x: x["column"])[:EXAMPLE_LIMIT] if index_evidence else None
        })

    # 4. subset_row_overlap
    if spec.subset and spec.subset in df.columns and n_rows > 0:
        cols_to_hash = [c for c in df.columns if c != spec.subset]
        def row_hash(row):
            return hashlib.sha256("".join(str(x) for x in row).encode("utf-8")).hexdigest()
            
        hashes = df[cols_to_hash].apply(row_hash, axis=1)
        temp_df = pd.DataFrame({"hash": hashes, "subset": df[spec.subset]})
        
        hash_subsets = temp_df.groupby("hash")["subset"].unique()
        overlapping_hashes = hash_subsets[hash_subsets.apply(len) > 1].index.tolist()
        
        overlap_count = int(temp_df["hash"].isin(overlapping_hashes).sum())
        if overlap_count > 0:
            subset_counts = temp_df["subset"].value_counts()
            pairs = []
            
            # Analyze pair-wise overlaps
            for h in overlapping_hashes:
                subs = sorted(list(hash_subsets[h]))
                for i in range(len(subs)):
                    for j in range(i + 1, len(subs)):
                        a, b = subs[i], subs[j]
                        # Find or create pair
                        pair = next((p for p in pairs if p["subset_a"] == a and p["subset_b"] == b), None)
                        if not pair:
                            pair = {"subset_a": a, "subset_b": b, "overlap_count": 0}
                            pairs.append(pair)
                        
                        # Add occurrences of this hash in both subsets
                        cnt_a = (temp_df[temp_df["hash"] == h]["subset"] == a).sum()
                        cnt_b = (temp_df[temp_df["hash"] == h]["subset"] == b).sum()
                        pair["overlap_count"] += min(cnt_a, cnt_b) # count distinct overlapping instances
                        
            # Finalize pairs
            for pair in pairs:
                a, b = pair["subset_a"], pair["subset_b"]
                smaller_size = min(subset_counts.get(a, 0), subset_counts.get(b, 0))
                pair["overlap_ratio_of_smaller"] = round(float(pair["overlap_count"] / smaller_size), 6) if smaller_size > 0 else 0.0
                
            pairs.sort(key=lambda x: (x["subset_a"], x["subset_b"]))
            
            checks.append({
                "name": "subset_row_overlap",
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": "Row overlaps across subsets",
                "evidence": {
                    "overlap_count": overlap_count,
                    "pairs": pairs[:EXAMPLE_LIMIT]
                }
            })
        else:
            checks.append({
                "name": "subset_row_overlap",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": "",
                "evidence": None
            })
    else:
        checks.append({
            "name": "subset_row_overlap",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": "",
            "evidence": None
        })
        
    # 5. subset_group_overlap
    if spec.subset and spec.group and spec.subset in df.columns and spec.group in df.columns and n_rows > 0:
        group_subsets = df.groupby(spec.group)[spec.subset].nunique()
        overlapping_groups = sorted(list(group_subsets[group_subsets > 1].index))
        overlap_group_count = len(overlapping_groups)
        
        if overlap_group_count > 0:
            checks.append({
                "name": "subset_group_overlap",
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": "Groups overlap across subsets",
                "evidence": {"overlap_group_count": overlap_group_count, "groups": overlapping_groups[:EXAMPLE_LIMIT]}
            })
        else:
            checks.append({
                "name": "subset_group_overlap",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": "",
                "evidence": None
            })
    else:
        checks.append({
            "name": "subset_group_overlap",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": "",
            "evidence": None
        })

    # 6. subset_time_ranges
    if spec.subset and spec.time and spec.subset in df.columns and spec.time in df.columns and n_rows > 0:
        time_s = pd.to_datetime(df[spec.time], errors="coerce")
        temp_df = pd.DataFrame({"time": time_s, "subset": df[spec.subset]}).dropna()
        
        has_overlap = False
        if not temp_df.empty:
            grouped = temp_df.groupby("subset")["time"].agg(["min", "max"])
            subsets = grouped.index.tolist()
            
            for i in range(len(subsets)):
                for j in range(i + 1, len(subsets)):
                    min_i, max_i = grouped.loc[subsets[i], "min"], grouped.loc[subsets[i], "max"]
                    min_j, max_j = grouped.loc[subsets[j], "min"], grouped.loc[subsets[j], "max"]
                    if min_i <= max_j and min_j <= max_i:
                        has_overlap = True
                        break
                if has_overlap:
                    break
                    
        if has_overlap:
            checks.append({
                "name": "subset_time_ranges",
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": "Time ranges overlap across subsets",
                "evidence": {"overlaps": True}
            })
        else:
            checks.append({
                "name": "subset_time_ranges",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": "",
                "evidence": {"overlaps": False}
            })
    else:
        checks.append({
            "name": "subset_time_ranges",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": "",
            "evidence": None
        })

    suspicion_count = sum(1 for c in checks if c["result"] == "fail")
    summary = {
        "performed": sum(1 for c in checks if c["status"] == "performed"),
        "not_assessable": sum(1 for c in checks if c["status"] == "not_assessable"),
        "skipped": sum(1 for c in checks if c["status"] == "skipped"),
        "fail": suspicion_count,
        "total": len(checks),
        "suspicion_count": suspicion_count
    }
    
    warnings = []
    if spec.target is None: warnings.append("target_not_provided")
    if spec.subset is None: warnings.append("subset_not_provided")
    if spec.group is None: warnings.append("group_not_provided")
    if spec.time is None: warnings.append("time_not_provided")
    if n_rows < 5: warnings.append("insufficient_rows")

    return {
        "leakage_schema_version": 1,
        "interpretation": "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.",
        "warnings": warnings,
        "checks": checks,
        "summary": summary,
        "thresholds": {
            "MIN_ROWS_FOR_COPY_CHECK": MIN_ROWS_FOR_COPY_CHECK,
            "MIN_PAIRS_FOR_CORRELATION": MIN_PAIRS_FOR_CORRELATION,
            "MIN_ROWS_FOR_INDEX_CHECK": MIN_ROWS_FOR_INDEX_CHECK,
            "EXACT_COPY_EQUALITY_RATIO": EXACT_COPY_EQUALITY_RATIO,
            "NEAR_COPY_CORR_ABS_MIN": NEAR_COPY_CORR_ABS_MIN,
            "INDEX_LIKE_UNIQUE_RATIO_MIN": INDEX_LIKE_UNIQUE_RATIO_MIN,
            "ATOL_NUMERIC_EQUALITY": ATOL_NUMERIC_EQUALITY,
            "EXAMPLE_LIMIT": EXAMPLE_LIMIT
        }
    }
