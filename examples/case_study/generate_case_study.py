"""Deterministic case study dataset generator with deliberately injected defects.

This generator produces examples/case_study/case_study.csv under a fixed seed.
All defects are synthetic and injected according to the specification in docs/CASE_STUDY.md.
"""

import argparse
import hashlib
import os
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20260928


def generate_dataset(out_dir: Path) -> Path:
    rng = np.random.default_rng(SEED)

    n_base = 594
    n_dups = 6

    # 1. Monotonic timestamps (YYYY-MM-DD)
    dates = pd.date_range("2024-01-01", periods=n_base)
    ts_list = [d.strftime("%Y-%m-%d") for d in dates]

    # 2. Group column: site in S1..S10 with site effects on y (D5)
    sites = [f"S{(i % 10) + 1}" for i in range(n_base)]
    site_effects = {f"S{i}": (i - 5.5) * 0.8 for i in range(1, 11)}

    # 3. Stratification / subpopulation: region in {A, B, C} (D8)
    regions = ["A" if i % 3 == 0 else "B" if i % 3 == 1 else "C" for i in range(n_base)]

    # 4. Feature x1: standard normal
    x1 = rng.normal(0.0, 1.0, size=n_base)

    # 5. Feature x2: distribution drift in last 30% of rows (D6)
    shift_start = int(n_base * 0.70)
    x2 = np.zeros(n_base)
    x2[:shift_start] = rng.normal(0.0, 1.0, size=shift_start)
    x2[shift_start:] = rng.normal(2.0, 1.5, size=n_base - shift_start)

    # 6. Feature x3: missing values (12 NaNs) (D2)
    x3 = rng.normal(0.0, 1.0, size=n_base)
    nan_indices = [15, 45, 75, 105, 135, 165, 195, 225, 255, 285, 315, 345]
    for idx in nan_indices:
        x3[idx] = np.nan

    # 7. Target y: linear combination + site effect + noise
    site_eff_arr = np.array([site_effects[s] for s in sites])
    base_noise = rng.normal(0.0, 0.5, size=n_base)
    y = 2.0 * x1 + 1.5 * x2 + site_eff_arr + base_noise

    # 8. Label noise: large deviation in 4% random rows (D9)
    label_noise_indices = rng.choice(n_base, size=int(0.04 * n_base), replace=False)
    for idx in label_noise_indices:
        y[idx] += rng.choice([-1.0, 1.0]) * rng.uniform(15.0, 25.0)

    # 9. Model predictions: Region B has ~3x larger error (D8)
    pred = np.zeros(n_base)
    for i in range(n_base):
        reg = regions[i]
        if reg == "B":
            pred[i] = y[i] + rng.normal(0.0, 1.8)
        else:
            pred[i] = y[i] + rng.normal(0.0, 0.6)

    # 10. Overconfident prediction intervals (D7)
    w = 0.20
    lo = pred - w
    hi = pred + w

    # 11. Target near-copy proxy feature (D3)
    y_proxy = 0.98 * y + rng.normal(0.0, 0.005, size=n_base)

    # 12. Monotonic integer row identifier (D4)
    row_id = np.arange(1, n_base + 1)

    df_base = pd.DataFrame({
        "row_id": row_id,
        "ts": ts_list,
        "site": sites,
        "region": regions,
        "x1": x1,
        "x2": x2,
        "x3": x3,
        "y": y,
        "pred": pred,
        "lo": lo,
        "hi": hi,
        "y_proxy": y_proxy,
    })

    # 13. Exact duplicate rows (6 duplicates) (D1)
    dup_rows = df_base.iloc[[10, 20, 30, 40, 50, 60]].copy()
    df_final = pd.concat([df_base, dup_rows], ignore_index=True)

    os.makedirs(out_dir, exist_ok=True)
    out_csv = out_dir / "case_study.csv"
    df_final.to_csv(
        out_csv,
        index=False,
        lineterminator="\n",
        encoding="utf-8",
        float_format="%.6f",
    )
    return out_csv


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic case study dataset with deliberately injected defects."
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="examples/case_study",
        help="Output directory (default: examples/case_study)",
    )
    args = parser.parse_args()

    out_path = generate_dataset(Path(args.out_dir))
    with open(out_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    print(f"wrote {out_path}")
    print(f"sha256={file_hash}")


if __name__ == "__main__":
    main()
