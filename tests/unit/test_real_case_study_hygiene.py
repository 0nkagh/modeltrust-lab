import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CSV = REPO_ROOT / "examples" / "case_study_real" / "student-por.csv"
EXPECTED_SHA256 = "a7594a11d7771c0efe1a740824e0e833da9c4cad07c39a9766a874575563fb3f"
EXPECTED_BYTES = 93220
EXPECTED_DATA_ROWS = 649
EXPECTED_COLUMNS = 33

def test_real_dataset_integrity():
    raw = CSV.read_bytes()
    assert len(raw) == EXPECTED_BYTES
    assert hashlib.sha256(raw).hexdigest().lower() == EXPECTED_SHA256
    assert raw[:3] != bytes((239, 187, 191))  # No BOM
    assert raw.count(b"\r\n") == 0  # No CRLF
    
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    assert len(lines) - 1 == EXPECTED_DATA_ROWS
    assert lines[0].count(";") + 1 == EXPECTED_COLUMNS

def test_real_dataset_provenance_and_honesty():
    readme = (REPO_ROOT / "examples" / "case_study_real" / "README.md").read_text(encoding="utf-8")
    assert "CC BY 4.0" in readme
    assert "10.24432/C5TG7T" in readme
    assert EXPECTED_SHA256.upper() in readme
    
    case_study = (REPO_ROOT / "docs" / "CASE_STUDY_REAL.md").read_text(encoding="utf-8")
    assert "not a benchmark" in case_study
