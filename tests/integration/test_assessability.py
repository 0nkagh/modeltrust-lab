import os
import sys
import json
import subprocess

def _run_card_questions(fixture: str, args: list[str], tmp_path) -> dict[int, dict]:
    out_dir = str(tmp_path / fixture.replace(".csv", ""))
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", f"tests/fixtures/{fixture}",
        "--target-col", "y",
        "--out-dir", out_dir
    ] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Command failed: {res.stderr}"
    
    card_path = os.path.join(out_dir, "card.json")
    assert os.path.exists(card_path), f"card.json not found at {card_path}"
    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)
    return {q["id"]: q for q in card["questions"]}


def test_q6_q7_answered_with_time_col(tmp_path):
    questions = _run_card_questions("shift_drift.csv", ["--time-col", "ts"], tmp_path)
    assert questions[6]["status"] == "answered"
    assert questions[7]["status"] == "answered"
    assert "shift.drift.feature_ks performed" in questions[6]["evidence"]
    assert "shift.ood.feature_range performed" in questions[7]["evidence"]


def test_q5_answered_with_predictions_and_group(tmp_path):
    questions = _run_card_questions("eval_preds.csv", ["--pred-col", "pred", "--group-col", "grp"], tmp_path)
    assert questions[5]["status"] == "answered"
    assert "evaluation.group_errors performed" in questions[5]["evidence"]


def test_q8_answered_with_intervals(tmp_path):
    questions = _run_card_questions(
        "intervals_calibrated.csv",
        ["--lower-col", "lo", "--upper-col", "hi", "--nominal-coverage", "0.9"],
        tmp_path
    )
    assert questions[8]["status"] == "answered"
    assert "uncertainty.coverage=" in questions[8]["evidence"]


def test_q10_partial_by_rule(tmp_path):
    questions_simple = _run_card_questions("simple_ok.csv", [], tmp_path)
    assert questions_simple[10]["status"] == "partial"
    assert "see limitations and not_assessable" in questions_simple[10]["evidence"]

    questions_drift = _run_card_questions("shift_drift.csv", ["--time-col", "ts"], tmp_path)
    assert questions_drift[10]["status"] == "partial"


def test_q1_to_q7_answered_in_declared_runs(tmp_path):
    q_b1 = _run_card_questions("simple_ok.csv", [], tmp_path)
    assert q_b1[1]["status"] == "answered"
    assert "profile:" in q_b1[1]["evidence"]

    assert q_b1[2]["status"] == "answered"
    assert "leakage.target_copy_exact=" in q_b1[2]["evidence"]

    q_b2 = _run_card_questions("leak_clean.csv", ["--group-col", "grp"], tmp_path)
    assert q_b2[3]["status"] == "answered"
    assert "split.modes.random=performed" in q_b2[3]["evidence"]

    assert q_b2[4]["status"] == "answered"
    assert "multiple split modes performed" in q_b2[4]["evidence"]

    assert q_b2[7]["status"] == "answered"
    assert "shift.ood.feature_range performed" in q_b2[7]["evidence"]
