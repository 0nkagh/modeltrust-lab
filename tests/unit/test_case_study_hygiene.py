import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "examples" / "case_study" / "generate_case_study.py"
COMMITTED = REPO_ROOT / "examples" / "case_study" / "case_study.csv"


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_case_study_dataset_matches_generator(tmp_path):
    subprocess.run(
        [sys.executable, str(GENERATOR), "--out-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    regenerated = tmp_path / "case_study.csv"
    assert regenerated.exists(), "generator did not write case_study.csv"
    assert _sha256(regenerated) == _sha256(COMMITTED), "committed CSV differs from a fresh generation"
