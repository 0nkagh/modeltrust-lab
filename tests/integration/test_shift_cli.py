import os
import json
from pathlib import Path
from tests.conftest import run_cli

def test_shift_cli_missing_group_or_time_col():
    # 11. --split-mode group without --group-col -> exit 4; --split-mode temporal without --time-col -> exit 4
    res_grp = run_cli(["shift", "--input", "tests/fixtures/shift_drift.csv", "--target-col", "y", "--split-mode", "group"])
    assert res_grp.returncode == 4
    assert res_grp.stdout.strip() == ""
    assert "Error: --split-mode group requires --group-col" in res_grp.stderr

    res_time = run_cli(["shift", "--input", "tests/fixtures/shift_drift.csv", "--target-col", "y", "--split-mode", "temporal"])
    assert res_time.returncode == 4
    assert res_time.stdout.strip() == ""
    assert "Error: --split-mode temporal requires --time-col" in res_time.stderr

def test_shift_cli_byte_identical():
    # 12. Two consecutive CLI runs are byte-identical
    cmd = ["shift", "--input", "tests/fixtures/shift_drift.csv", "--target-col", "y", "--time-col", "ts", "--split-mode", "temporal"]
    res1 = run_cli(cmd)
    res2 = run_cli(cmd)

    assert res1.returncode == 0
    assert res2.returncode == 0
    assert res1.stdout == res2.stdout

def test_shift_cli_golden():
    # 13. Golden tests/golden/shift_drift.normalized.json (excluding environment)
    cmd = ["shift", "--input", "tests/fixtures/shift_drift.csv", "--target-col", "y", "--time-col", "ts", "--split-mode", "temporal"]
    res = run_cli(cmd)
    assert res.returncode == 0

    actual_data = json.loads(res.stdout)
    actual_data.pop("environment", None)

    golden_path = Path("tests/golden/shift_drift.normalized.json")

    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        golden_path.parent.mkdir(exist_ok=True, parents=True)
        golden_path.write_text(json.dumps(actual_data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    with open(golden_path, "r", encoding="utf-8") as f:
        golden_norm = json.load(f)

    assert actual_data == golden_norm
