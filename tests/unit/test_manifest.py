import json
import re
from unittest.mock import patch
from modeltrust.manifest import build_manifest, write_manifest


def _dummy_prov():
    return {
        "tool": {"name": "modeltrust", "version": "0.2.0"},
        "input": {
            "path": "tests/fixtures/simple_ok.csv",
            "sha256": "97cbacf19b1474861bafe4ad7dd3f34a98ec7759d812eeedc34a8a4d84246529",
            "nrows_total": 2,
            "ncols": 3,
        },
        "environment": {
            "python": "3.12.8",
            "pandas": "3.0.6",
            "numpy": "2.2.6",
            "platform": "win32",
        },
        "run_metadata": {"seed": 42},
    }


def test_manifest_no_timestamp():
    prov = _dummy_prov()
    cmd = "python -m modeltrust card -i tests/fixtures/simple_ok.csv --target-col y --out-dir ./out"
    outputs = {"card_json_sha256": "abc123", "card_md_sha256": "def456"}
    man = build_manifest(prov, cmd, "tests/fixtures/simple_ok.csv", outputs)
    text = json.dumps(man)
    assert re.search(r"\d{4}-\d{2}-\d{2}", text) is None
    assert re.search(r"\d{2}:\d{2}:\d{2}", text) is None


def test_manifest_deterministic():
    prov = _dummy_prov()
    cmd = "python -m modeltrust card -i tests/fixtures/simple_ok.csv --target-col y --out-dir ./out"
    outputs = {"card_json_sha256": "abc123", "card_md_sha256": "def456"}
    man1 = build_manifest(prov, cmd, "tests/fixtures/simple_ok.csv", outputs)
    man2 = build_manifest(prov, cmd, "tests/fixtures/simple_ok.csv", outputs)
    assert man1 == man2


def test_manifest_git_unavailable():
    prov = _dummy_prov()
    cmd = "python -m modeltrust card -i tests/fixtures/simple_ok.csv --target-col y --out-dir ./out"
    outputs = {"card_json_sha256": "abc123", "card_md_sha256": "def456"}
    with patch("subprocess.run", side_effect=OSError("git not found")):
        man = build_manifest(prov, cmd, "tests/fixtures/simple_ok.csv", outputs)
    git_block = man["git"]
    assert git_block["commit"] is None
    assert git_block["dirty"] is None
    assert git_block["reason_code"] == "not_available"
