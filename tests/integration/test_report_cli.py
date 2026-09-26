import json
import os
import tempfile
from tests.conftest import run_cli

def test_report_byte_identical_runs():
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        res1 = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir1])
        res2 = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir2])
        
        assert res1.returncode == 0
        assert res2.returncode == 0
        
        with open(os.path.join(tmpdir1, "report.json"), "rb") as f:
            j1 = f.read()
        with open(os.path.join(tmpdir2, "report.json"), "rb") as f:
            j2 = f.read()
            
        with open(os.path.join(tmpdir1, "report.md"), "rb") as f:
            m1 = f.read()
        with open(os.path.join(tmpdir2, "report.md"), "rb") as f:
            m2 = f.read()
            
        # JSON might have different generated_at, but we didn't use --run-timestamp so it should be null.
        # But wait, environment might differ? environment is static per machine.
        assert j1 == j2
        assert m1 == m2

def test_report_golden():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y", "--out-dir", tmpdir])
        assert res.returncode == 0
        
        with open(os.path.join(tmpdir, "report.json"), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            
        if "environment" in data:
            del data["environment"]
            
        normalized = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        golden_path = "tests/golden/report_simple_ok.normalized.json"
        
        if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
            with open(golden_path, "w", encoding="utf-8") as f:
                f.write(normalized)
                
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()
            
        assert normalized == golden

def test_report_input_not_found():
    res = run_cli(["report", "--input", "nonexistent.csv", "--out-dir", "out"])
    assert res.returncode == 4
    assert "file not found" in res.stderr
    assert not res.stdout.strip()
