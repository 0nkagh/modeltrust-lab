import json
from tests.conftest import run_cli
from pathlib import Path

def test_inspect_simple_ok():
    res = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"], cwd=Path("."))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["run_metadata"]["generated_at"] is None
    assert data["input"]["nrows_total"] == 2
    
def test_inspect_byte_identical():
    res1 = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"], cwd=Path("."))
    res2 = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"], cwd=Path("."))
    assert res1.returncode == 0
    assert res1.stdout == res2.stdout

def test_inspect_file_not_found():
    res = run_cli(["inspect", "--input", "nonexistent.csv"], cwd=Path("."))
    assert res.returncode == 4
    assert "file not found" in res.stderr
    assert not res.stdout.strip()
    
def test_inspect_max_rows_and_outdir():
    res = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--max-rows", "1", "--out-dir", "out"], cwd=Path("."))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["input"]["truncated"] is True
    assert "--out-dir is reserved" in res.stderr
    
def test_profile_not_implemented():
    res = run_cli(["profile", "--input", "tests/fixtures/simple_ok.csv"], cwd=Path("."))
    assert res.returncode == 3
    assert "not implemented" in res.stderr
