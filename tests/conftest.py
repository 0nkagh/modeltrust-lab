import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def run_cli(args: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "modeltrust"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
