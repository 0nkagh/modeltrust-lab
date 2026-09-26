import subprocess
import sys
from pathlib import Path

def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "modeltrust"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
