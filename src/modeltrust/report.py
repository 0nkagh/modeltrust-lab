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
    modules = ["schema", "profile", "leakage", "split"]
    for mod in modules:
        if not prov.get(mod): continue
        perf = not_assess = skip = fail = 0
        for c in prov[mod].get("checks", []):
            if c["status"] == "performed": perf += 1
            elif c["status"] == "not_assessable": not_assess += 1
            elif c["status"] == "skipped": skip += 1
            
            if c.get("result") == "fail": fail += 1
        md.append(f"| {mod} | {perf} | {not_assess} | {skip} | {fail} |")
        
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

    # 5. Leakage suspicions
    md.append("\n## 5. Leakage suspicions")
    leak_fails = []
    if prov.get("leakage"):
        for c in prov["leakage"].get("checks", []):
            if c.get("result") == "fail":
                leak_fails.append(f"- **{c['name']}**: {c.get('detail', '')}")
    if leak_fails:
        md.extend(leak_fails)
    else:
        md.append("- No leakage suspicions flagged.")
    md.append("\n> Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.")

    # 6. Split comparison
    md.append("\n## 6. Split comparison")
    if prov.get("split") and prov["split"].get("comparison"):
        md.append("| Mode | n_train | n_test | group_overlap | row_overlap | time_overlap | abs_std_mean_diff |")
        md.append("|---|---|---|---|---|---|---|")
        for comp in prov["split"]["comparison"]:
            mode = comp.get("mode")
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
    else:
        md.append("Split comparison not requested or not available.")

    # 7. Limitations & scope
    md.append("\n## 7. Limitations & scope")
    md.append("- Scope: Tabular regression only.")
    md.append("- Purpose: Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.")
    md.append("- Out of scope: Preprocessing and Feature Engineering leakage, Sampling bias, Label noise, Database join leakage, Temporal causality violations.")
    
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
    cmd_str = " ".join(cmd_args)
    md.append(f"`python -m modeltrust report --input \"{prov['input']['path']}\" --out-dir <DIR> {cmd_str}`")
    
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
