import json
import os
import subprocess
import sys
from modeltrust.card import get_card_thresholds


def _get_git_info() -> dict:
    try:
        res_rev = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res_rev.returncode != 0:
            return {"commit": None, "dirty": None, "reason_code": "not_available"}
        commit = res_rev.stdout.strip()
        if len(commit) != 40 or not all(c in "0123456789abcdefABCDEF" for c in commit):
            return {"commit": None, "dirty": None, "reason_code": "not_available"}

        res_status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res_status.returncode != 0:
            return {"commit": None, "dirty": None, "reason_code": "not_available"}
        dirty = bool(res_status.stdout.strip())
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return {"commit": None, "dirty": None, "reason_code": "not_available"}


def build_manifest(prov: dict, command: str, input_path: str, outputs_sha256: dict) -> dict:
    tool_info = prov.get("tool", {})
    tool = {
        "name": tool_info.get("name", "modeltrust"),
        "version": tool_info.get("version", "0.1.0"),
    }

    inp = prov.get("input", {})
    given_path = input_path or inp.get("path", "")
    sha256_val = inp.get("sha256")
    if not sha256_val and given_path and os.path.exists(given_path):
        import hashlib
        with open(given_path, "rb") as f:
            sha256_val = hashlib.sha256(f.read()).hexdigest()

    rows = inp.get("nrows_total", inp.get("nrows_read", 0))
    cols = inp.get("ncols", 0)

    input_block = {
        "path": given_path,
        "sha256": sha256_val or "",
        "rows": rows,
        "columns": cols,
    }

    env_prov = prov.get("environment", {})
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    import pandas as pd
    import numpy as np

    environment = {
        "python": py_ver,
        "pandas": env_prov.get("pandas", getattr(pd, "__version__", "")),
        "numpy": env_prov.get("numpy", getattr(np, "__version__", "")),
        "platform": sys.platform,
    }

    seed = prov.get("run_metadata", {}).get("seed", 42)
    git_info = _get_git_info()
    thresholds = get_card_thresholds()

    manifest = {
        "manifest_schema_version": 1,
        "tool": tool,
        "command": command,
        "input": input_block,
        "environment": environment,
        "seed": seed,
        "git": git_info,
        "config": {
            "thresholds": thresholds,
        },
        "outputs": {
            "card_json_sha256": outputs_sha256.get("card_json_sha256", ""),
            "card_md_sha256": outputs_sha256.get("card_md_sha256", ""),
        },
        "warnings": [],
    }

    return manifest


def write_manifest(path: str, manifest: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
