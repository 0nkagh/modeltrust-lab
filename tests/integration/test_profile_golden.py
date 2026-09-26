import os
import json
import pytest
from pathlib import Path
from tests.conftest import run_cli

def test_profile_golden():
    res = run_cli(["profile", "--input", "tests/fixtures/simple_ok.csv", "--target-col", "y"])
    assert res.returncode == 0
    
    data = json.loads(res.stdout)
    data.pop("environment", None)
    
    golden_path = Path("tests/golden/profile_simple_ok.normalized.json")
    
    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        golden_path.parent.mkdir(exist_ok=True, parents=True)
        golden_path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print("GOLDEN REWRITTEN")
        return
        
    assert golden_path.exists(), "Golden file not found. Run with MODELTRUST_REGEN_GOLDEN=1"
    golden_data = json.loads(golden_path.read_text(encoding="utf-8"))
    
    assert data == golden_data
