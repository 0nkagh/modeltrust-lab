import json
import tempfile
from tests.conftest import run_cli
from pathlib import Path

def test_inspect_simple_ok():
    res = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["run_metadata"]["generated_at"] is None
    assert data["input"]["nrows_total"] == 2
    
def test_inspect_byte_identical():
    res1 = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"])
    res2 = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"])
    assert res1.returncode == 0
    assert res1.stdout == res2.stdout

def test_inspect_file_not_found():
    res = run_cli(["inspect", "--input", "nonexistent.csv"])
    assert res.returncode == 4
    assert "file not found" in res.stderr
    assert not res.stdout.strip()
    
def test_inspect_max_rows_and_outdir():
    res = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--max-rows", "1", "--out-dir", "out"])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["input"]["truncated"] is True
    assert "--out-dir is reserved" in res.stderr

def test_run_cli_is_cwd_independent():
    # Call with default cwd
    res1 = run_cli(["inspect", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"])
    
    # Call with temp directory cwd and absolute path
    from tests.conftest import REPO_ROOT
    abs_input = str(REPO_ROOT / "tests" / "fixtures" / "simple_ok.csv")
    res2 = run_cli(
        ["inspect", "--input", abs_input, "--target-col", "y"], 
        cwd=Path(tempfile.gettempdir())
    )
    
    
    data1 = json.loads(res1.stdout)
    data2 = json.loads(res2.stdout)
    
    assert data1["input"]["path"] == "tests/fixtures/simple_ok.csv"
    assert data2["input"]["path"] == abs_input
    
    # Ignore path difference
    data1["input"]["path"] = ""
    data2["input"]["path"] = ""
    
    assert data1 == data2
