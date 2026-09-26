import pandas as pd
import numpy as np
from modeltrust.schema import ColumnSpec

def _round(val) -> float:
    if pd.isna(val) or np.isinf(val):
        return None
    return round(float(val), 6)

def build_profile(frame: pd.DataFrame, meta: dict, spec: ColumnSpec) -> dict:
    row_count = len(frame)
    column_count = len(frame.columns)
    
    # 1. Duplicate rows
    if row_count > 0:
        dups = frame.duplicated(keep="first")
        exact_duplicate_count = int(dups.sum())
        duplicate_row_ratio = _round(exact_duplicate_count / row_count)
        # Fix index conversion to int
        example_row_indices = [int(x) for x in dups[dups].head(5).index.tolist()]
    else:
        exact_duplicate_count = 0
        duplicate_row_ratio = 0.0
        example_row_indices = []
        
    duplicate_rows = {
        "exact_duplicate_count": exact_duplicate_count,
        "duplicate_row_ratio": duplicate_row_ratio,
        "example_row_indices": example_row_indices,
        "null_equals_null": True
    }
    
    # Variables for warnings and checks
    constant_columns = []
    all_missing_columns = []
    high_cardinality_columns = []
    has_non_finite = False
    
    columns_info = []
    
    for col_name in frame.columns:
        col_series = frame[col_name]
        
        # Determine role
        if spec.target == col_name:
            role = "target"
        elif spec.prediction == col_name:
            role = "prediction"
        elif spec.group == col_name:
            role = "group"
        elif spec.time == col_name:
            role = "time"
        else:
            role = "feature"
            
        observed_dtype = str(col_series.dtype)
        is_numeric = pd.api.types.is_numeric_dtype(col_series)
        
        missing_count = int(col_series.isna().sum())
        missing_ratio = _round(missing_count / row_count) if row_count > 0 else 0.0
        
        n_unique = int(col_series.nunique(dropna=True))
        unique_ratio = _round(n_unique / row_count) if row_count > 0 else 0.0
        
        is_all_missing = (missing_count == row_count and row_count > 0) or row_count == 0
        
        if is_all_missing:
            is_constant = None
            all_missing_columns.append(col_name)
        elif n_unique <= 1:
            is_constant = True
            constant_columns.append(col_name)
        else:
            is_constant = False
            
        if not is_numeric and not is_all_missing and unique_ratio >= 0.95:
            high_cardinality_columns.append(col_name)
            
        col_info = {
            "name": col_name,
            "role": role,
            "observed_dtype": observed_dtype,
            "is_numeric": is_numeric,
            "missing_count": missing_count,
            "missing_ratio": missing_ratio,
            "n_unique": n_unique,
            "unique_ratio": unique_ratio,
            "is_all_missing": is_all_missing,
            "is_constant": is_constant,
            "non_finite_count": None,
            "stats": None,
            "top_values": []
        }
        
        if is_numeric:
            inf_mask = np.isinf(col_series)
            non_finite_count = int(inf_mask.sum())
            col_info["non_finite_count"] = non_finite_count
            if non_finite_count > 0:
                has_non_finite = True
                
            if not is_all_missing:
                # filter out non-finite for stats
                finite_series = col_series[~inf_mask].dropna()
                if not finite_series.empty:
                    col_info["stats"] = {
                        "mean": _round(finite_series.mean()),
                        "std": _round(finite_series.std()),
                        "min": _round(finite_series.min()),
                        "q05": _round(finite_series.quantile(0.05)),
                        "q25": _round(finite_series.quantile(0.25)),
                        "q50": _round(finite_series.quantile(0.50)),
                        "q75": _round(finite_series.quantile(0.75)),
                        "q95": _round(finite_series.quantile(0.95)),
                        "max": _round(finite_series.max())
                    }
        else:
            if not is_all_missing:
                vc = col_series.value_counts(dropna=True)
                top_items = []
                for val, cnt in vc.items():
                    top_items.append({
                        "value": str(val),
                        "raw_type": type(val).__name__,
                        "count": int(cnt)
                    })
                # Sort descending by count, then ascending by string value
                top_items.sort(key=lambda x: (-x["count"], x["value"]))
                col_info["top_values"] = top_items[:5]
                
        columns_info.append(col_info)
        
    target_summary = None
    if spec.target and spec.target in frame.columns:
        target_col_info = next((c for c in columns_info if c["name"] == spec.target), None)
        if target_col_info and target_col_info["is_numeric"]:
            target_summary = {
                "count": row_count,
                "missing_count": target_col_info["missing_count"],
                "non_finite_count": target_col_info["non_finite_count"]
            }
            if target_col_info["stats"]:
                target_summary.update(target_col_info["stats"])
            else:
                target_summary.update({
                    "mean": None, "std": None, "min": None,
                    "q05": None, "q25": None, "q50": None, "q75": None, "q95": None, "max": None
                })
                
    # Checks
    checks = []
    
    def add_check(name, condition, count=None):
        if condition:
            checks.append({
                "name": name,
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": str(count) if count is not None else ""
            })
        else:
            checks.append({
                "name": name,
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": ""
            })
            
    add_check("rows_present", row_count == 0, 0)
    add_check("columns_present", column_count == 0, 0)
    
    total_missing = sum(c["missing_count"] for c in columns_info)
    add_check("missing_values_observed", total_missing > 0, total_missing)
    
    add_check("duplicate_rows_observed", exact_duplicate_count > 0, exact_duplicate_count)
    add_check("constant_columns_observed", len(constant_columns) > 0, len(constant_columns))
    add_check("all_missing_columns_observed", len(all_missing_columns) > 0, len(all_missing_columns))
    add_check("high_cardinality_columns_observed", len(high_cardinality_columns) > 0, len(high_cardinality_columns))
    
    total_inf = sum(c.get("non_finite_count") or 0 for c in columns_info)
    add_check("non_finite_values_observed", total_inf > 0, total_inf)
    
    if spec.target is None:
        checks.append({
            "name": "target_available_for_summary",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": ""
        })
    else:
        add_check("target_available_for_summary", target_summary is None)
        
    # Warnings
    warnings = []
    if exact_duplicate_count > 0: warnings.append("duplicate_rows_present")
    if constant_columns: warnings.append("constant_columns_present")
    if all_missing_columns: warnings.append("all_missing_columns_present")
    if high_cardinality_columns: warnings.append("high_cardinality_columns_present")
    if has_non_finite: warnings.append("non_finite_values_present")
    if meta.get("truncated"): warnings.append("truncated_input")
    if "single_group" in meta.get("warnings", []): warnings.append("single_group")
    
    return {
        "profile_schema_version": 1,
        "row_count": row_count,
        "column_count": column_count,
        "duplicate_rows": duplicate_rows,
        "constant_columns": constant_columns,
        "all_missing_columns": all_missing_columns,
        "high_cardinality_columns": high_cardinality_columns,
        "columns": columns_info,
        "target_summary": target_summary,
        "checks": checks,
        "warnings": warnings
    }
