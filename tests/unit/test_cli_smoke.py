import subprocess
import sys

def test_version_flag():
    result = subprocess.run(
        [sys.executable, "-m", "modeltrust", "--version"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "modeltrust" in result.stdout

def test_help_flag():
    result = subprocess.run(
        [sys.executable, "-m", "modeltrust", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_subcommand_not_implemented():
    result = subprocess.run(
        [sys.executable, "-m", "modeltrust", "profile", "--input", "x.csv"],
        capture_output=True, text=True
    )
    assert result.returncode == 3
    assert "not implemented" in result.stderr

def test_unknown_command():
    result = subprocess.run(
        [sys.executable, "-m", "modeltrust", "bilinmeyen-komut"],
        capture_output=True, text=True
    )
    assert result.returncode == 2
