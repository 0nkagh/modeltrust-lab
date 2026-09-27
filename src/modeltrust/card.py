import os
import json

def build_card_json(prov, reproduce_command):
    questions = []
    
    # Q1
    p = prov.get("profile", {})
    if p and p.get("status") == "performed":
        dupes = p.get("duplicate_rows", 0)
        questions.append({"id": 1, "question": "Missing or duplicate records?", "status": "answered", "evidence": f"profile: duplicate_rows={dupes}, missing cells reported"})
    else:
        questions.append({"id": 1, "question": "Missing or duplicate records?", "status": "not_assessable", "evidence": "profile not performed"})
        
    # Q2
    lk = prov.get("leakage", {})
    if lk and lk.get("status") == "performed":
        exact = lk.get("checks", {}).get("target_copy_exact", {}).get("result", "not_assessable")
        near = lk.get("checks", {}).get("target_copy_near", {}).get("result", "not_assessable")
        if exact != "not_assessable" or near != "not_assessable":
            questions.append({"id": 2, "question": "Target leakage suspicion?", "status": "answered", "evidence": f"leakage.target_copy_exact={exact}, target_copy_near={near}"})
        else:
            questions.append({"id": 2, "question": "Target leakage suspicion?", "status": "not_assessable", "evidence": "checks not performed"})
    else:
        questions.append({"id": 2, "question": "Target leakage suspicion?", "status": "not_assessable", "evidence": "leakage not performed"})
        
    # Q3
    sp = prov.get("split", {}) or {}
    rand_status = "not_assessable"
    if sp and sp.get("status") == "performed":
        for m in sp.get("modes", []):
            if m.get("mode") == "random":
                rand_status = m.get("result", "performed")
                break
    if rand_status != "not_assessable":
        questions.append({"id": 3, "question": "Train/test or group leakage?", "status": "answered", "evidence": f"split.modes.random={rand_status}"})
    else:
        questions.append({"id": 3, "question": "Train/test or group leakage?", "status": "not_assessable", "evidence": "split.modes.random not performed"})
        
    # Q4
    modes_performed = 0
    if sp and sp.get("status") == "performed":
        for m in sp.get("modes", []):
            if m.get("mode") in ["random", "group", "temporal"] and m.get("result", "not_assessable") != "not_assessable":
                modes_performed += 1
    if modes_performed >= 2:
        questions.append({"id": 4, "question": "Split strategy difference?", "status": "answered", "evidence": f"multiple split modes performed ({modes_performed})"})
    else:
        questions.append({"id": 4, "question": "Split strategy difference?", "status": "partial", "evidence": "not enough split modes for comparison"})
        
    # Q5
    ev = prov.get("evaluation", {})
    if ev and ev.get("status") == "performed":
        ge = ev.get("group_errors", {})
        if ge and ge.get("status") == "performed":
            questions.append({"id": 5, "question": "Which groups have higher error?", "status": "answered", "evidence": "evaluation.group_errors performed"})
        else:
            questions.append({"id": 5, "question": "Which groups have higher error?", "status": "not_assessable", "evidence": "group_errors not performed"})
    else:
        questions.append({"id": 5, "question": "Which groups have higher error?", "status": "not_assessable", "evidence": "evaluation not performed"})
        
    # Q6 & Q7
    sh = prov.get("shift", {})
    drift_status = sh.get("drift", {}).get("feature_ks", {}).get("status", "not_assessable") if sh else "not_assessable"
    if drift_status == "performed":
        questions.append({"id": 6, "question": "Distribution drift?", "status": "answered", "evidence": "shift.drift.feature_ks performed"})
    else:
        questions.append({"id": 6, "question": "Distribution drift?", "status": "not_assessable", "evidence": "shift.drift.feature_ks not performed"})
        
    ood_status = sh.get("ood", {}).get("feature_range", {}).get("status", "not_assessable") if sh else "not_assessable"
    if ood_status == "performed":
        questions.append({"id": 7, "question": "Out-of-distribution (OOD) data?", "status": "answered", "evidence": "shift.ood.feature_range performed"})
    else:
        questions.append({"id": 7, "question": "Out-of-distribution (OOD) data?", "status": "not_assessable", "evidence": "shift.ood.feature_range not performed"})
        
    # Q8
    unc_status = ev.get("uncertainty", {}).get("status", "not_assessable") if ev else "not_assessable"
    if unc_status == "performed":
        u = ev.get("uncertainty", {})
        cov = u.get("coverage", 0)
        wl = u.get("wilson_low", 0)
        wh = u.get("wilson_high", 0)
        nom = u.get("nominal", 0)
        questions.append({"id": 8, "question": "Are uncertainty intervals calibrated?", "status": "answered", "evidence": f"uncertainty.coverage={cov:.3f} (Wilson [{wl:.3f}, {wh:.3f}]), nominal={nom}"})
    else:
        questions.append({"id": 8, "question": "Are uncertainty intervals calibrated?", "status": "not_assessable", "evidence": "uncertainty not performed"})
        
    # Q9
    questions.append({"id": 9, "question": "Which checks could not be performed?", "status": "answered", "evidence": "see not_assessable"})
    
    # Q10
    questions.append({"id": 10, "question": "How much can this report be trusted?", "status": "partial", "evidence": "see limitations and not_assessable"})

    checks_summary = []
    not_assessable = []
    
    # Collect not_assessable from leakage, split, evaluation, shift
    if lk and lk.get("status") == "performed":
        total = 0; performed = 0; fail = 0; na = 0
        for chk, d in lk.get("checks", {}).items():
            total += 1
            if d.get("result") == "not_assessable":
                na += 1
                not_assessable.append({"module": "leakage", "check": chk, "reason_code": d.get("reason_code", "unknown")})
            elif d.get("result") == "fail":
                fail += 1
                performed += 1
            else:
                performed += 1
        checks_summary.append({"module": "leakage", "total": total, "performed": performed, "fail": fail, "not_assessable": na})
        
    if sp and sp.get("status") == "performed":
        total = 0; performed = 0; fail = 0; na = 0
        for m in sp.get("modes", []):
            total += 1
            if m.get("result") == "not_assessable":
                na += 1
                not_assessable.append({"module": "split", "check": f"modes.{m.get('mode')}", "reason_code": m.get("reason_code", "unknown")})
            elif m.get("result") == "fail":
                fail += 1
                performed += 1
            else:
                performed += 1
        checks_summary.append({"module": "split", "total": total, "performed": performed, "fail": fail, "not_assessable": na})
        
    if sh and sh.get("status") == "performed":
        total = 0; performed = 0; fail = 0; na = 0
        for cat in ["drift", "ood"]:
            if cat in sh:
                for chk, d in sh[cat].items():
                    if isinstance(d, dict) and "status" in d:
                        total += 1
                        if d["status"] == "not_assessable":
                            na += 1
                            not_assessable.append({"module": "shift", "check": f"{cat}.{chk}", "reason_code": d.get("reason_code", "unknown")})
                        elif d["status"] == "fail":
                            fail += 1
                            performed += 1
                        else:
                            performed += 1
        if total > 0:
            checks_summary.append({"module": "shift", "total": total, "performed": performed, "fail": fail, "not_assessable": na})
            
    # Collect metrics
    metrics = {
        "models": ev.get("models", []) if ev else [],
        "cv_aggregate": ev.get("cv_aggregate") if ev else None,
        "worst_groups_by_mae": ev.get("group_errors", {}).get("worst_groups_by_mae") if ev else None,
        "interval_coverage": ev.get("uncertainty") if ev and ev.get("uncertainty", {}).get("status") == "performed" else None
    }
    
    # Collect thresholds
    thresholds = {}
    try:
        from modeltrust.audit.leakage import MIN_ROWS_FOR_COPY_CHECK
        thresholds["MIN_ROWS_FOR_COPY_CHECK"] = MIN_ROWS_FOR_COPY_CHECK
    except ImportError:
        pass
    
    try:
        from modeltrust.audit.shift import OOD_MAHALANOBIS_RATIO_MIN
        thresholds["OOD_MAHALANOBIS_RATIO_MIN"] = OOD_MAHALANOBIS_RATIO_MIN
    except ImportError:
        pass
        
    try:
        from modeltrust.evaluate import COVERAGE_GAP_TOL
        thresholds["COVERAGE_GAP_TOL"] = COVERAGE_GAP_TOL
    except ImportError:
        pass

    try:
        from modeltrust.evaluate import MIN_ROWS_FOR_METRICS
        thresholds["MIN_ROWS_FOR_METRICS"] = MIN_ROWS_FOR_METRICS
    except ImportError:
        pass
        
    env = prov.get("environment", {})
    env_clean = {k: v for k, v in env.items() if k in ["python", "pandas", "numpy", "platform"]}
    
    run_meta = prov.get("run_metadata", {})
    run_meta["command"] = reproduce_command

    card = {
        "tool": prov.get("tool"),
        "environment": env_clean,
        "input": prov.get("input", {}),
        "run": run_meta,
        "scope": {"task": "tabular_regression", "model_loaded": False, "external_data_downloaded": False, "user_code_executed": False},
        "questions": questions,
        "checks_summary": checks_summary,
        "not_assessable": not_assessable,
        "metrics": metrics,
        "thresholds": thresholds,
        "limitations": [
            "Scope: tabular regression only.",
            "Diagnostic indicators only. Absence of a flag does not establish absence of leakage.",
            "Heuristic thresholds; no significance testing is performed.",
            "Single split; finite sample; no distribution-free guarantee."
        ],
        "reproduce_command": reproduce_command,
        "interpretation": "This card is a diagnostic summary, not a certificate. It contains no performance guarantee and no compliance claim."
    }
    
    return card

def build_card_md(card):
    lines = []
    lines.append("# ModelTrust Lab - Diagnostic Card")
    lines.append("")
    lines.append("## 1. Scope & disclaimer")
    lines.append(card["interpretation"])
    lines.append("")
    
    lines.append("## 2. Data provenance")
    inp = card.get("input", {})
    run = card.get("run", {})
    lines.append(f"- **Path:** {inp.get('path', 'unknown')}")
    lines.append(f"- **SHA256:** {inp.get('sha256', 'unknown')}")
    lines.append(f"- **Rows/Cols:** {inp.get('nrows_total', 0)} / {inp.get('ncols', 0)}")
    lines.append(f"- **Seed:** {run.get('seed', 'unknown')}")
    lines.append("")
    
    lines.append("## 3. Questions answered")
    lines.append("| # | Question | Status | Evidence |")
    lines.append("|---|---|---|---|")
    for q in card["questions"]:
        lines.append(f"| {q['id']} | {q['question']} | {q['status']} | {q['evidence']} |")
    lines.append("")
    
    lines.append("## 4. Checks summary")
    lines.append("| Module | Total | Performed | Fail | Not Assessable |")
    lines.append("|---|---|---|---|---|")
    for cs in card["checks_summary"]:
        lines.append(f"| {cs['module']} | {cs['total']} | {cs['performed']} | {cs['fail']} | {cs['not_assessable']} |")
    if not card["checks_summary"]:
        lines.append("| (none) | 0 | 0 | 0 | 0 |")
    lines.append("")
    
    lines.append("## 5. Not assessable")
    lines.append("| Module | Check | Reason |")
    lines.append("|---|---|---|")
    for na in card["not_assessable"]:
        lines.append(f"| {na['module']} | {na['check']} | {na['reason_code']} |")
    if not card["not_assessable"]:
        lines.append("| (all) | All requested checks were assessable. | - |")
    lines.append("")
    
    lines.append("## 6. Metrics")
    metrics = card.get("metrics", {})
    models = metrics.get("models", [])
    if models:
        # Note: we use n_scored (split) as we just added to the report
        lines.append("| Model | MAE | RMSE | R² | n_scored (split) |")
        lines.append("|---|---|---|---|---|")
        for m in models:
            lines.append(f"| {m['name']} | {m.get('mae', 'N/A')} | {m.get('rmse', 'N/A')} | {m.get('r2', 'N/A')} | {m.get('n_scored', 'N/A')} |")
    else:
        lines.append("not provided")
    lines.append("")
    
    cv = metrics.get("cv_aggregate")
    if cv:
        lines.append("### Cross-validation")
        lines.append("| Fold | MAE | RMSE | R² |")
        lines.append("|---|---|---|---|")
        for f in cv:
            lines.append(f"| {f.get('fold', 'N/A')} | {f.get('mae', 'N/A')} | {f.get('rmse', 'N/A')} | {f.get('r2', 'N/A')} |")
        lines.append("")
        
    worst = metrics.get("worst_groups_by_mae")
    if worst:
        lines.append("### Worst groups by MAE")
        lines.append("| Group | MAE | N |")
        lines.append("|---|---|---|")
        for w in worst:
            lines.append(f"| {w.get('group')} | {w.get('mae')} | {w.get('n')} |")
        lines.append("")
        
    interval = metrics.get("interval_coverage")
    if interval:
        lines.append("### Interval coverage")
        lines.append("| Coverage | Wilson Low | Wilson High | Nominal | Mean Width |")
        lines.append("|---|---|---|---|---|")
        lines.append(f"| {interval.get('coverage')} | {interval.get('wilson_low')} | {interval.get('wilson_high')} | {interval.get('nominal')} | {interval.get('mean_width')} |")
        lines.append("")
        
    lines.append("## 7. Thresholds")
    lines.append(", ".join([f"{k}={v}" for k, v in card["thresholds"].items()]))
    lines.append("")
    
    lines.append("## 8. Limitations")
    for lim in card["limitations"]:
        lines.append(f"- {lim}")
    lines.append("")
    
    lines.append("## 9. Reproduce")
    lines.append("```bash")
    lines.append(card["reproduce_command"])
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)

def write_card(prov, out_dir, reproduce_command):
    os.makedirs(out_dir, exist_ok=True)
    card = build_card_json(prov, reproduce_command)
    md = build_card_md(card)
    
    json_path = os.path.join(out_dir, "card.json")
    md_path = os.path.join(out_dir, "card.md")
    
    with open(json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
        f.write("\n")
        
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
        
    return json_path, md_path
