import os
import sys
import json
import subprocess
import hashlib
import pytest

def test_card_missing_outdir():
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/simple_ok.csv"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "Error: --out-dir is required" in res.stderr

def test_card_cli_success(tmpdir):
    out = str(tmpdir)
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/simple_ok.csv",
        "--out-dir", out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "wrote" in res.stderr
    assert "card.md" in res.stderr
    
    assert os.path.exists(os.path.join(out, "card.json"))
    assert os.path.exists(os.path.join(out, "card.md"))
    
    lines = res.stderr.strip().split("\n")
    assert len(lines) == 1

def test_card_determinism(tmpdir):
    out1 = os.path.join(str(tmpdir), "run1")
    out2 = os.path.join(str(tmpdir), "run2")
    
    cmd1 = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/eval_preds.csv",
        "--target-col", "y", "--pred-col", "pred",
        "--out-dir", out1
    ]
    cmd2 = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/eval_preds.csv",
        "--target-col", "y", "--pred-col", "pred",
        "--out-dir", out2
    ]
    
    subprocess.run(cmd1, capture_output=True, check=True)
    subprocess.run(cmd2, capture_output=True, check=True)
    
    with open(os.path.join(out1, "card.json"), "r", encoding="utf-8") as f:
        card1 = json.load(f)
    with open(os.path.join(out2, "card.json"), "r", encoding="utf-8") as f:
        card2 = json.load(f)
        
    if "environment" in card1:
        del card1["environment"]
    if "environment" in card2:
        del card2["environment"]
        
    if "reproduce_command" in card1:
        del card1["reproduce_command"]
    if "reproduce_command" in card2:
        del card2["reproduce_command"]
        
    if "run" in card1:
        del card1["run"]
    if "run" in card2:
        del card2["run"]
        
    assert card1 == card2

def test_card_full_golden(tmpdir):
    out = str(tmpdir)
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/eval_preds.csv",
        "--target-col", "y", "--pred-col", "pred",
        "--group-col", "grp",
        "--split-mode", "group", "--test-size", "0.2",
        "--out-dir", out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    
    with open(os.path.join(out, "card.json"), "r", encoding="utf-8") as f:
        card = json.load(f)
        
    # Remove environment which contains platform specific data
    if "environment" in card:
        del card["environment"]
        
    if "reproduce_command" in card:
        del card["reproduce_command"]
        
    if "run" in card:
        del card["run"]
        
    # Normalize paths
    card["input"]["path"] = card["input"]["path"].replace("\\", "/")
    
    golden_path = "tests/golden/card_full.normalized.json"
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(card, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
            
    with open(golden_path, "r", encoding="utf-8") as f:
        golden = json.load(f)
        
    assert card == golden

def test_card_real_cli_questions_answered(tmpdir):
    out = str(tmpdir)
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/eval_preds.csv",
        "--target-col", "y", "--pred-col", "pred", "--group-col", "grp",
        "--out-dir", out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    with open(os.path.join(out, "card.json"), "r", encoding="utf-8") as f:
        card = json.load(f)
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[1]["status"] == "answered"
    assert q_dict[2]["status"] == "answered"
    assert q_dict[3]["status"] == "answered"
    assert q_dict[5]["status"] == "answered"
    assert q_dict[9]["status"] == "answered"
    assert q_dict[10]["status"] == "partial"

def test_card_real_cli_minimal(tmpdir):
    out = str(tmpdir)
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/simple_ok.csv",
        "--target-col", "y",
        "--out-dir", out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    with open(os.path.join(out, "card.json"), "r", encoding="utf-8") as f:
        card = json.load(f)
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[1]["status"] == "answered"
    # Depending on row counts Q2 and Q3 may be not_assessable.
    assert q_dict[10]["status"] == "partial"

def test_card_real_cli_uncertainty_wired(tmpdir):
    out = str(tmpdir)
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/intervals_calibrated.csv",
        "--target-col", "y", "--lower-col", "lo", "--upper-col", "hi",
        "--out-dir", out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    with open(os.path.join(out, "card.json"), "r", encoding="utf-8") as f:
        card = json.load(f)
    q_dict = {q["id"]: q for q in card["questions"]}
    assert q_dict[8]["status"] == "answered"
    assert card["metrics"].get("interval_coverage") is not None


# --- Column existence validation tests (PHASE 4 / T14-R4 / D-079) ---

def test_card_column_validation_group_col_missing(tmpdir):
    """--group-col referencing a non-existent column -> exit 2 with clear message."""
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/intervals_calibrated.csv",
        "--target-col", "y",
        "--group-col", "grp",
        "--lower-col", "lo", "--upper-col", "hi",
        "--out-dir", str(tmpdir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "Error: --group-col 'grp' not found in input columns" in res.stderr


def test_card_column_validation_lower_col_missing(tmpdir):
    """--lower-col referencing a non-existent column -> exit 2 with clear message."""
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/simple_ok.csv",
        "--target-col", "y",
        "--lower-col", "no_such_col",
        "--upper-col", "no_such_col2",
        "--out-dir", str(tmpdir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "--lower-col" in res.stderr
    assert "not found in input columns" in res.stderr


def test_card_column_validation_pred_col_missing(tmpdir):
    """--pred-col referencing a non-existent column -> exit 2 with clear message."""
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/intervals_calibrated.csv",
        "--target-col", "y",
        "--pred-col", "no_pred",
        "--out-dir", str(tmpdir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "Error: --pred-col 'no_pred' not found in input columns" in res.stderr


def test_card_column_validation_positive(tmpdir):
    """All provided columns exist -> exit 0."""
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "-i", "tests/fixtures/intervals_calibrated.csv",
        "--target-col", "y",
        "--lower-col", "lo",
        "--upper-col", "hi",
        "--out-dir", str(tmpdir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert os.path.exists(os.path.join(str(tmpdir), "card.json"))
