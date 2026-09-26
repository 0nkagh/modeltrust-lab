from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass(frozen=True)
class ColumnSpec:
    target: Optional[str] = None
    prediction: Optional[str] = None
    group: Optional[str] = None
    time: Optional[str] = None
    subset: Optional[str] = None

def validate_input(frame: pd.DataFrame, meta: dict, spec: ColumnSpec) -> dict:
    checks = []
    
    # 1. frame_not_empty
    result = "pass" if not frame.empty and not frame.columns.empty else "fail"
    checks.append({
        "name": "frame_not_empty",
        "status": "performed",
        "result": result,
        "reason_code": None,
        "detail": "0 rows or 0 columns" if result == "fail" else ""
    })
    
    # 2. columns_unique
    result = "fail" if meta.get("duplicate_headers") else "pass"
    checks.append({
        "name": "columns_unique",
        "status": "performed",
        "result": result,
        "reason_code": None,
        "detail": str(meta.get("duplicate_headers")) if result == "fail" else ""
    })
    
    # 3. column_names_nonempty
    result = "fail" if meta.get("unnamed_columns") else "pass"
    checks.append({
        "name": "column_names_nonempty",
        "status": "performed",
        "result": result,
        "reason_code": None,
        "detail": str(meta.get("unnamed_columns")) if result == "fail" else ""
    })
    
    # 4. target_present
    if spec.target is None:
        checks.append({
            "name": "target_present",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": ""
        })
    else:
        result = "pass" if spec.target in frame.columns else "fail"
        checks.append({
            "name": "target_present",
            "status": "performed",
            "result": result,
            "reason_code": None,
            "detail": f"Missing column: {spec.target}" if result == "fail" else ""
        })
        
    # 5. target_numeric
    if spec.target is not None and spec.target in frame.columns:
        s = pd.to_numeric(frame[spec.target], errors="coerce")
        original_na = frame[spec.target].isna().sum()
        coerced_na = s.isna().sum()
        failed_parse = coerced_na - original_na
        
        if failed_parse >= 1:
            fails_mask = s.isna() & frame[spec.target].notna()
            bad_vals = frame.loc[fails_mask, spec.target].head(3).tolist()
            checks.append({
                "name": "target_numeric",
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": f"{failed_parse} rows failed to parse as numeric. Examples: {bad_vals}"
            })
        else:
            checks.append({
                "name": "target_numeric",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": ""
            })
    else:
        checks.append({
            "name": "target_numeric",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": ""
        })
        
    # 6. optional_columns_present
    missing_opts = []
    if spec.prediction and spec.prediction not in frame.columns: missing_opts.append(spec.prediction)
    if spec.group and spec.group not in frame.columns: missing_opts.append(spec.group)
    if spec.time and spec.time not in frame.columns: missing_opts.append(spec.time)
    
    has_any_opt = any([spec.prediction, spec.group, spec.time])
    if not has_any_opt:
        checks.append({
            "name": "optional_columns_present",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": ""
        })
    else:
        if missing_opts:
            checks.append({
                "name": "optional_columns_present",
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": f"Missing columns: {missing_opts}"
            })
        else:
            checks.append({
                "name": "optional_columns_present",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": ""
            })
            
    # 7. time_column_parseable
    if spec.time is not None and spec.time in frame.columns:
        s = pd.to_datetime(frame[spec.time], errors="coerce")
        fails = s.isna() & frame[spec.time].notna()
        if fails.any():
            bad_vals = frame.loc[fails, spec.time].head(3).tolist()
            checks.append({
                "name": "time_column_parseable",
                "status": "performed",
                "result": "fail",
                "reason_code": None,
                "detail": f"{fails.sum()} rows failed to parse as datetime. Examples: {bad_vals}"
            })
        else:
            checks.append({
                "name": "time_column_parseable",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": ""
            })
    else:
        checks.append({
            "name": "time_column_parseable",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": ""
        })
        
    # 8. group_column_cardinality
    session_warnings = []
    if spec.group is not None and spec.group in frame.columns:
        n_groups = frame[spec.group].nunique(dropna=True)
        if n_groups <= 1:
            session_warnings.append("single_group")
            checks.append({
                "name": "group_column_cardinality",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": "single_group"
            })
        else:
            checks.append({
                "name": "group_column_cardinality",
                "status": "performed",
                "result": "pass",
                "reason_code": None,
                "detail": ""
            })
    else:
        checks.append({
            "name": "group_column_cardinality",
            "status": "not_assessable",
            "result": None,
            "reason_code": "not_provided",
            "detail": ""
        })

    summary = {
        "performed": sum(1 for c in checks if c["status"] == "performed"),
        "skipped": sum(1 for c in checks if c["status"] == "skipped"),
        "not_assessable": sum(1 for c in checks if c["status"] == "not_assessable"),
        "fail": sum(1 for c in checks if c["result"] == "fail"),
        "total": len(checks)
    }
    
    return {"checks": checks, "summary": summary, "session_warnings": session_warnings}
