import hashlib
import json
import os
import subprocess
import sys


def test_manifest_written_and_hashes_match(tmpdir):
    out = str(tmpdir)
    input_file = "tests/fixtures/intervals_calibrated.csv"
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "--input", input_file,
        "--target-col", "y",
        "--lower-col", "lo", "--upper-col", "hi",
        "--nominal-coverage", "0.9",
        "--manifest",
        "--out-dir", out,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "manifest.json" in res.stderr
    assert f"wrote {os.path.join(out, 'card.json')}, {os.path.join(out, 'card.md')} and {os.path.join(out, 'manifest.json')}" in res.stderr

    card_json_p = os.path.join(out, "card.json")
    card_md_p = os.path.join(out, "card.md")
    manifest_p = os.path.join(out, "manifest.json")

    assert os.path.exists(card_json_p)
    assert os.path.exists(card_md_p)
    assert os.path.exists(manifest_p)

    with open(manifest_p, "r", encoding="utf-8") as f:
        man = json.load(f)

    with open(card_json_p, "rb") as f:
        actual_card_json_sha = hashlib.sha256(f.read()).hexdigest()
    with open(card_md_p, "rb") as f:
        actual_card_md_sha = hashlib.sha256(f.read()).hexdigest()
    with open(input_file, "rb") as f:
        actual_input_sha = hashlib.sha256(f.read()).hexdigest()

    assert man["outputs"]["card_json_sha256"] == actual_card_json_sha
    assert man["outputs"]["card_md_sha256"] == actual_card_md_sha
    assert man["input"]["sha256"] == actual_input_sha
    assert man["manifest_schema_version"] == 1


def test_manifest_determinism_same_outdir(tmpdir):
    out = str(tmpdir)
    input_file = "tests/fixtures/intervals_calibrated.csv"
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "--input", input_file,
        "--target-col", "y",
        "--lower-col", "lo", "--upper-col", "hi",
        "--nominal-coverage", "0.9",
        "--manifest",
        "--out-dir", out,
    ]

    res1 = subprocess.run(cmd, capture_output=True, text=True)
    assert res1.returncode == 0
    with open(os.path.join(out, "manifest.json"), "rb") as f:
        hash1 = hashlib.sha256(f.read()).hexdigest()

    res2 = subprocess.run(cmd, capture_output=True, text=True)
    assert res2.returncode == 0
    with open(os.path.join(out, "manifest.json"), "rb") as f:
        hash2 = hashlib.sha256(f.read()).hexdigest()

    assert hash1 == hash2


def test_manifest_golden(tmpdir):
    out = str(tmpdir)
    input_file = "tests/fixtures/intervals_calibrated.csv"
    cmd = [
        sys.executable, "-m", "modeltrust", "card",
        "--input", input_file,
        "--target-col", "y",
        "--lower-col", "lo", "--upper-col", "hi",
        "--nominal-coverage", "0.9",
        "--manifest",
        "--out-dir", out,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0

    with open(os.path.join(out, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if "command" in manifest:
        del manifest["command"]
    if "environment" in manifest:
        del manifest["environment"]
    if "git" in manifest:
        del manifest["git"]
    if "outputs" in manifest:
        manifest["outputs"]["card_json_sha256"] = "<STRIPPED>"
        manifest["outputs"]["card_md_sha256"] = "<STRIPPED>"
    if "input" in manifest and "path" in manifest["input"]:
        manifest["input"]["path"] = manifest["input"]["path"].replace("\\", "/")

    golden_path = "tests/golden/manifest.normalized.json"

    if os.environ.get("MODELTRUST_REGEN_GOLDEN") == "1":
        with open(golden_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")

    with open(golden_path, "r", encoding="utf-8") as f:
        golden = json.load(f)

    assert manifest == golden
