import json
import os

def build_report_md(prov: dict) -> str:
    md = []
    md.append("# ModelTrust Lab — Diagnostic Report")
    
    # 1. Input & provenance
    md.append("## 1. Input & provenance")
    i = prov["input"]
    md.append(f"- Path: {i['path']}")
    md.append(f"- SHA256: {i['sha256']}")
    md.append(f"- Rows: {i['nrows_total']}")
    md.append(f"- Columns: {i['ncols']}")
    md.append(f"- Columns SHA256: {i['columns_sha256']}")
    md.append(f"- Seed: {prov['run_metadata']['seed']}")
    md.append(f"- Python: {prov['environment']['python']}")
    md.append(f"- Pandas: {prov['environment']['pandas']}")
    
    # 2. Check summary
    md.append("\n## 2. Check summary")
    md.append("| Module | Performed | Not Assessable | Skipped | Fail |")
    md.append("|---|---|---|---|---|")
    modules = ["schema", "profile", "leakage", "split", "evaluation", "shift"]
    for mod in modules:
        if not prov.get(mod): continue
        perf = not_assess = skip = fail = 0
        for c in prov[mod].get("checks", []):
            if c["status"] == "performed":
                perf += 1
                if c.get("result") == "fail": fail += 1
            elif c["status"] == "not_assessable": not_assess += 1
            elif c["status"] == "skipped": skip += 1
        md.append(f"| {mod} | {perf} | {not_assess} | {skip} | {fail} |")
    md.append("\n* Checks marked as `not_assessable` are skipped when prerequisite conditions (e.g., target column variance, temporal column presence) are not met.")
    md.append("* Profile fail findings indicate data quality issues, not model leakage or split errors.")
        
    # 3. What could NOT be assessed
    md.append("\n## 3. What could NOT be assessed")
    md.append("| Reason | Module | Check |")
    md.append("|---|---|---|")
    has_not_assessable = False
    for mod in modules:
        if not prov.get(mod): continue
        for c in prov[mod].get("checks", []):
            if c["status"] != "performed":
                reason = c.get("reason_code") or "unknown"
                md.append(f"| {reason} | {mod} | {c['name']} |")
                has_not_assessable = True
    if not has_not_assessable:
        md.append("| - | - | None |")
        
    # 4. Data profile highlights
    md.append("\n## 4. Data profile highlights")
    p = prov.get("profile", {})
    md.append(f"- Rows/Columns: {p.get('row_count', 0)} / {p.get('column_count', 0)}")
    dups = p.get("duplicate_rows", {}).get("exact_duplicate_count", 0)
    md.append(f"- Duplicate rows: {dups}")
    md.append(f"- Constant columns: {len(p.get('constant_columns', []))}")
    md.append(f"- All-missing columns: {len(p.get('all_missing_columns', []))}")
    md.append(f"- High-cardinality columns: {len(p.get('high_cardinality_columns', []))}")
    
    non_finite = 0
    for c in p.get("columns", []):
        non_finite += (c.get("non_finite_count") or 0)
    md.append(f"- Non-finite values (numeric): {non_finite}")

    # 5. Flagged patterns
    md.append("\n## 5. Flagged patterns")
    flagged = []
    for mod in ["leakage", "split", "evaluation", "shift"]:
        if prov.get(mod):
            for c in prov[mod].get("checks", []):
                if c.get("status") == "performed" and c.get("result") == "fail":
                    flagged.append((mod, c["name"], c.get("detail", "")))
    
    if flagged:
        md.append("| Module | Check | Details |")
        md.append("|---|---|---|")
        for mod, check, detail in flagged:
            md.append(f"| {mod} | {check} | {detail} |")
    else:
        md.append("- No flagged patterns in the tested checks.")
    md.append("\n> Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.")

    # 6. Split comparison (and distribution shift if present)
    has_shift = prov.get("shift") is not None
    if has_shift:
        md.append("\n## 6. Split comparison and distribution shift")
    else:
        md.append("\n## 6. Split comparison")

    if prov.get("split") and prov["split"].get("comparison"):
        md.append("| Mode | n_train | n_test | group_overlap | row_overlap | time_overlap | abs_std_mean_diff |")
        md.append("|---|---|---|---|---|---|---|")
        modes_dict = prov["split"].get("modes", {})
        for comp in prov["split"]["comparison"]:
            mode = comp.get("mode")
            status = modes_dict.get(mode, {}).get("status", "performed")
            
            if status != "performed":
                row = [str(mode), "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
            else:
                n_tr = comp.get("n_train")
                n_te = comp.get("n_test")
                g_ov = comp.get("group_overlap_count")
                r_ov = comp.get("row_overlap_count")
                t_ov = comp.get("time_ranges_overlap")
                a_diff = comp.get("abs_std_mean_diff")
                
                row = [
                    str(mode),
                    str(n_tr) if n_tr is not None else "N/A",
                    str(n_te) if n_te is not None else "N/A",
                    str(g_ov) if g_ov is not None else "N/A",
                    str(r_ov) if r_ov is not None else "N/A",
                    str(t_ov) if t_ov is not None else "N/A",
                    f"{a_diff:.6f}" if isinstance(a_diff, (int, float)) else "N/A"
                ]
            md.append("| " + " | ".join(row) + " |")
        md.append("\n* Modes marked as N/A were not assessable (e.g., temporal split on a dataset without a time column).")
    else:
        md.append("Split comparison not requested or not available.")

    # Distribution shift & OOD table (only when --shift enabled)
    if has_shift:
        sh = prov["shift"]
        md.append("\n### Distribution shift & OOD")
        md.append("| Check | Result | Detail |")
        md.append("|---|---|---|")
        for c in sh.get("checks", []):
            check_name = c["name"]
            result = c.get("result", "N/A")
            status = c.get("status", "performed")
            detail = c.get("detail", "")
            if status != "performed":
                result_str = f"not_assessable ({c.get('reason_code', '')})"
            else:
                result_str = result
            md.append(f"| {check_name} | {result_str} | {detail} |")

        # Shift warnings
        warns = sh.get("warnings", [])
        if warns:
            md.append(f"\n> Shift warnings: {', '.join(warns)}")
        md.append(f"\n> {sh.get('interpretation', 'Diagnostic indicators only.')}")

    # 7. Limitations & scope
    md.append("\n## 7. Limitations & scope")
    md.append("- Scope: Tabular regression only.")
    md.append("- Purpose: Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.")
    md.append("- Out of scope: pipeline-code level preprocessing leakage (fit scope cannot be inspected from a file), feature engineering transformations, sampling bias, label noise, database join leakage, temporal causality violations.")
    
    # 8. How to reproduce
    md.append("\n## 8. How to reproduce")
    md.append("Reproducibility requires the same environment (Python, pandas, numpy versions) and the same random seed.")
    # Extract command args loosely for illustration
    cmd_args = []
    if prov["column_spec"].get("target"): cmd_args.extend(["--target-col", prov["column_spec"]["target"]])
    if prov["column_spec"].get("prediction"): cmd_args.extend(["--pred-col", prov["column_spec"]["prediction"]])
    if prov["column_spec"].get("group"): cmd_args.extend(["--group-col", prov["column_spec"]["group"]])
    if prov["column_spec"].get("time"): cmd_args.extend(["--time-col", prov["column_spec"]["time"]])
    if prov["column_spec"].get("subset"): cmd_args.extend(["--subset-col", prov["column_spec"]["subset"]])
    cmd_args.extend(["--seed", str(prov["run_metadata"]["seed"])])
    if prov.get("evaluation"):
        cmd_args.append("--evaluate")
    if has_shift:
        cmd_args.append("--shift")
    cmd_str = " ".join(cmd_args)
    md.append(f"`python -m modeltrust report --input \"{prov['input']['path']}\" --out-dir <DIR> {cmd_str}`")
    
    # 9. Model evaluation
    if prov.get("evaluation"):
        ev = prov["evaluation"]
        md.append("\n## 9. Model evaluation")
        
        # Models table
        md.append("### Models")
        md.append("| Model | MAE | RMSE | R² | n_scored |")
        md.append("|---|---|---|---|---|")
        for m in ev.get("models", []):
            m_name = m.get("name", "unknown")
            if m.get("status") == "performed":
                mae_str = f"{m['mae']:.6f}" if m.get("mae") is not None else "N/A"
                rmse_str = f"{m['rmse']:.6f}" if m.get("rmse") is not None else "N/A"
                r2_str = f"{m['r2']:.6f}" if m.get("r2") is not None else "N/A"
                n_scored = str(m.get("n_scored", "N/A"))
            else:
                mae_str = "N/A"
                rmse_str = "N/A"
                r2_str = "N/A"
                n_scored = f"N/A ({m.get('reason_code') or 'not_performed'})"
            md.append(f"| {m_name} | {mae_str} | {rmse_str} | {r2_str} | {n_scored} |")
            
        # CV table
        md.append("\n### Cross-validation")
        cv = ev.get("cv", {})
        md.append("| Fold | MAE | RMSE | R² |")
        md.append("|---|---|---|---|")
        if cv.get("status") == "performed":
            for f_info in cv.get("folds", []):
                f_num = f_info.get("fold", "N/A")
                f_mae = f"{f_info['mae']:.6f}" if f_info.get("mae") is not None else "N/A"
                f_rmse = f"{f_info['rmse']:.6f}" if f_info.get("rmse") is not None else "N/A"
                f_r2 = f"{f_info['r2']:.6f}" if f_info.get("r2") is not None else "N/A"
                md.append(f"| {f_num} | {f_mae} | {f_rmse} | {f_r2} |")
            agg = cv.get("aggregate", {})
            agg_mae = f"{agg['mae_mean']:.6f}" if agg.get("mae_mean") is not None else "N/A"
            agg_rmse = f"{agg['rmse_mean']:.6f}" if agg.get("rmse_mean") is not None else "N/A"
            agg_r2 = f"{agg['r2_mean']:.6f}" if agg.get("r2_mean") is not None else "N/A"
            md.append(f"| Aggregate | {agg_mae} | {agg_rmse} | {agg_r2} |")
        else:
            reason = cv.get("reason_code") or "not_provided"
            md.append(f"| N/A | N/A | N/A | N/A |")
            md.append(f"| Aggregate | N/A ({reason}) | N/A | N/A |")
            md.append(f"\n* Cross-validation not assessable: N/A ({reason}).")

        # Group errors table
        md.append("\n### Group errors")
        ge = ev.get("group_errors", {})
        md.append("| Group | n | MAE | RMSE |")
        md.append("|---|---|---|---|")
        if ge.get("status") == "performed":
            worst_names = set(ge.get("worst_by_mae", []))
            worst_groups = [g for g in ge.get("groups", []) if g.get("group") in worst_names]
            worst_groups.sort(key=lambda x: (-x.get("mae", 0.0), x.get("group", "")))
            if worst_groups:
                for wg in worst_groups:
                    md.append(f"| {wg['group']} | {wg['n']} | {wg['mae']:.6f} | {wg['rmse']:.6f} |")
            else:
                md.append("| None | 0 | N/A | N/A |")
            cov_ratio = ge.get("coverage_ratio", 0.0)
            md.append(f"\n- Coverage ratio: {cov_ratio:.6f}")
        else:
            reason = ge.get("reason_code") or "not_provided"
            md.append(f"| N/A | N/A | N/A | N/A |")
            md.append(f"\n* Group errors not assessable: N/A ({reason}).")
            cov_ratio = ge.get("coverage_ratio", 0.0)
            md.append(f"- Coverage ratio: {cov_ratio:.6f}")

        # Thresholds and Not assessable lines
        thresh = ev.get("thresholds", {})
        thresh_parts = [f"{k}={v}" for k, v in sorted(thresh.items())]
        md.append(f"\n- Thresholds: {', '.join(thresh_parts)}")
        
        not_assess = []
        for mod in ["leakage", "split", "evaluation"]:
            if prov.get(mod):
                for c in prov[mod].get("checks", []):
                    if c.get("status") == "not_assessable":
                        not_assess.append(f"{c['name']} ({c.get('reason_code') or 'unknown'})")
        not_assess_str = ", ".join(not_assess) if not_assess else "None"
        md.append(f"- Not assessable: {not_assess_str}")
    
    return "\n".join(md) + "\n"

def write_reports(prov: dict, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "report.json")
    md_path = os.path.join(out_dir, "report.md")
    
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(prov, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
        f.write("\n")
        
    md_content = build_report_md(prov)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    return json_path, md_path
