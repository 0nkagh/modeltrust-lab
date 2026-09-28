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

def test_subcommand_usage_error():
    result = subprocess.run(
        [sys.executable, "-m", "modeltrust", "report", "--input", "x.csv"],
        capture_output=True, text=True
    )
    assert result.returncode == 2
    assert "Error: --out-dir is required" in result.stderr

def test_unknown_command():
    result = subprocess.run(
        [sys.executable, "-m", "modeltrust", "bilinmeyen-komut"],
        capture_output=True, text=True
    )
    assert result.returncode == 2


def test_all_subcommands_help_exit_zero():
    subcommands = ["inspect", "profile", "leakage", "split", "report", "evaluate", "shift", "card"]
    for sc in subcommands:
        result = subprocess.run(
            [sys.executable, "-m", "modeltrust", sc, "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"{sc} --help returned {result.returncode}: {result.stderr}"
        assert result.stderr == "", f"{sc} --help wrote to stderr: {result.stderr}"


def test_help_texts_format_safe():
    subcommands = ["inspect", "profile", "leakage", "split", "report", "evaluate", "shift", "card"]
    for sc in subcommands:
        result = subprocess.run(
            [sys.executable, "-m", "modeltrust", sc, "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"{sc} --help crashed: {result.stderr}"
        assert "usage:" in result.stdout, f"{sc} --help output missing 'usage:'"
