import json
import os
import tempfile
from tests.conftest import run_cli
import pandas as pd
from modeltrust.report import build_report_md

def test_report_files_created_and_canonical():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        assert res.returncode == 0
        
        json_path = os.path.join(tmpdir, "report.json")
        md_path = os.path.join(tmpdir, "report.md")
        
        assert os.path.exists(json_path)
        assert os.path.exists(md_path)
        
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            
        assert "schema" in data
        assert "profile" in data
        assert "leakage" in data
        
        # Test canonical format string matches
        canonical = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        assert content == canonical
        
def test_report_section_3_not_assessable():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        md_path = os.path.join(tmpdir, "report.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
            
        # target_available_for_summary should be listed because --target-col is not provided
        assert "target_available_for_summary" in md
        assert "not_provided" in md
        assert "What could NOT be assessed" in md

def test_report_no_forbidden_language():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        md_path = os.path.join(tmpdir, "report.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
            
        forbidden_words = ["production-ready", "leakage-proof", "fully reliable", "guaranteed", "regulatory compliant", "all failure modes detected", "model is safe", "low risk"]
        md_lower = md.lower()
        for w in forbidden_words:
            assert w not in md_lower, f"Forbidden word '{w}' found in report"
            
        assert "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage." in md

def test_report_out_dir_required():
    res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv"])
    assert res.returncode == 2
    assert "Error: --out-dir is required" in res.stderr

def test_report_split_null_if_not_requested():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_cli(["report", "--input", "tests/fixtures/simple_ok.csv", "--out-dir", tmpdir])
        assert res.returncode == 0
        json_path = os.path.join(tmpdir, "report.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            
        assert data.get("split") is None
        assert "split_not_requested" in data["input"]["warnings"]
