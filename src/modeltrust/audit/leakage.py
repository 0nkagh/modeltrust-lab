import hashlib
import pandas as pd
import numpy as np
from typing import Any
from modeltrust.schema import ColumnSpec

# Eşikler (D-034)
TARGET_COPY_EPS = 1e-5
TARGET_COPY_RATIO = 0.999
INDEX_LIKE_RATIO = 0.95

def build_leakage(df: pd.DataFrame, spec: ColumnSpec) -> dict[str, Any]:
    n_rows = len(df)
    
    # Exclude special columns from feature list
    special_cols = {spec.target, spec.prediction, spec.group, spec.time, spec.subset}
    special_cols = {c for c in special_cols if c is not None}
    feature_cols = [c for c in df.columns if c not in special_cols]
    
    target_copy = []
    if spec.target and spec.target in df.columns and n_rows > 0:
        target_s = df[spec.target]
        target_is_num = pd.api.types.is_numeric_dtype(target_s)
        
        for col in feature_cols:
            col_s = df[col]
            if target_is_num and pd.api.types.is_numeric_dtype(col_s):
                diff = (col_s - target_s).abs()
                match_ratio = (diff < TARGET_COPY_EPS).sum() / n_rows
            else:
                match_ratio = (col_s.astype(str) == target_s.astype(str)).sum() / n_rows
                
            if match_ratio > TARGET_COPY_RATIO:
                target_copy.append(col)
                
    index_like = []
    if n_rows > 0:
        for col in feature_cols:
            n_unique = df[col].nunique(dropna=True)
            if (n_unique / n_rows) > INDEX_LIKE_RATIO:
                index_like.append(col)
                
    # subset_row_overlap
    row_overlap: dict[str, Any] = {}
    if spec.subset and spec.subset in df.columns and n_rows > 0:
        row_overlap["status"] = "performed"
        # calculate row hashes excluding subset column
        cols_to_hash = [c for c in df.columns if c != spec.subset]
        
        def row_hash(row):
            return hashlib.sha256("".join(str(x) for x in row).encode("utf-8")).hexdigest()
            
        hashes = df[cols_to_hash].apply(row_hash, axis=1)
        
        temp_df = pd.DataFrame({"hash": hashes, "subset": df[spec.subset]})
        hash_subsets = temp_df.groupby("hash")["subset"].nunique()
        overlapping_hashes = hash_subsets[hash_subsets > 1].index
        
        if len(overlapping_hashes) > 0:
            row_overlap["has_overlap"] = True
            row_overlap["overlapping_row_count"] = int(temp_df["hash"].isin(overlapping_hashes).sum())
        else:
            row_overlap["has_overlap"] = False
            row_overlap["overlapping_row_count"] = 0
    else:
        row_overlap["status"] = "not_assessable"
        row_overlap["reason_code"] = "not_provided"
        
    # subset_group_overlap
    group_overlap: dict[str, Any] = {}
    if spec.subset and spec.group and spec.subset in df.columns and spec.group in df.columns and n_rows > 0:
        group_overlap["status"] = "performed"
        group_subsets = df.groupby(spec.group)[spec.subset].nunique()
        overlapping_groups = sorted(list(group_subsets[group_subsets > 1].index))
        group_overlap["overlapping_groups"] = overlapping_groups
    else:
        group_overlap["status"] = "not_assessable"
        group_overlap["reason_code"] = "not_provided"
        
    # subset_time_overlap
    time_overlap: dict[str, Any] = {}
    if spec.subset and spec.time and spec.subset in df.columns and spec.time in df.columns and n_rows > 0:
        time_overlap["status"] = "performed"
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
        time_overlap["has_overlap"] = has_overlap
    else:
        time_overlap["status"] = "not_assessable"
        time_overlap["reason_code"] = "not_provided"
        
    return {
        "interpretation": "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.",
        "target_copy_suspicion": sorted(target_copy),
        "index_like_columns": sorted(index_like),
        "subset_row_overlap": row_overlap,
        "subset_group_overlap": group_overlap,
        "subset_time_overlap": time_overlap,
        "thresholds": {
            "target_copy_eps": TARGET_COPY_EPS,
            "target_copy_ratio": TARGET_COPY_RATIO,
            "index_like_ratio": INDEX_LIKE_RATIO
        }
    }
