import pytest
import numpy as np
from modeltrust.audit.split import build_split
from modeltrust.schema import ColumnSpec
from modeltrust.dataio import read_table

def test_split_random_sizes():
    loaded = read_table("tests/fixtures/split_groups.csv")
    spec = ColumnSpec()
    res = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    
    rm = res["modes"]["random"]
    assert rm["n_train"] + rm["n_test"] == len(loaded.frame)
    assert abs(rm["test_fraction"] - 0.2) <= 0.05

def test_split_random_seed():
    loaded = read_table("tests/fixtures/split_groups.csv")
    spec = ColumnSpec()
    r1 = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    r2 = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    r3 = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=99)
    
    h1 = r1["modes"]["random"]["train_row_indices_sha256"]
    h2 = r2["modes"]["random"]["train_row_indices_sha256"]
    h3 = r3["modes"]["random"]["train_row_indices_sha256"]
    
    assert h1 == h2
    assert h1 != h3

def test_split_random_group_leakage():
    loaded = read_table("tests/fixtures/split_groups.csv")
    spec = ColumnSpec(group="grp")
    res = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    
    rm = res["modes"]["random"]
    assert rm["group_overlap"]["count"] > 0
    
    c = next(x for x in res["checks"] if x["name"] == "random_split_group_leakage")
    assert c["result"] == "fail"

def test_split_group_disjointness():
    loaded = read_table("tests/fixtures/split_groups.csv")
    spec = ColumnSpec(group="grp")
    res = build_split(loaded.frame, spec, mode="group", test_size=0.2, seed=42)
    
    gm = res["modes"]["group"]
    assert gm["group_overlap"]["count"] == 0
    
    c = next(x for x in res["checks"] if x["name"] == "group_split_disjointness")
    assert c["result"] == "pass"
    
    assert len(gm["group_assignments"]) > 0

def test_split_group_pinning():
    loaded = read_table("tests/fixtures/split_time.csv")
    spec = ColumnSpec(group="grp")
    res = build_split(loaded.frame, spec, mode="group", test_size=0.2, seed=42)
    
    gm = res["modes"]["group"]
    test_groups = [g["group"] for g in gm["group_assignments"] if g["side"] == "test"]
    assert test_groups == ["G1"]
    assert gm["n_train"] == 24
    assert gm["test_fraction"] == 0.2

def test_split_temporal_ordering():
    loaded = read_table("tests/fixtures/split_time.csv")
    spec = ColumnSpec(time="ts")
    res = build_split(loaded.frame, spec, mode="temporal", test_size=0.2, seed=42)
    
    tm = res["modes"]["temporal"]
    assert tm["time_ranges"]["overlaps"] is False
    assert tm["time_ranges"]["boundary_ties"] == 0
    
    c = next(x for x in res["checks"] if x["name"] == "temporal_split_ordering")
    assert c["result"] == "pass"

def test_split_temporal_group_leakage():
    loaded = read_table("tests/fixtures/split_time.csv")
    spec = ColumnSpec(time="ts", group="grp")
    res = build_split(loaded.frame, spec, mode="temporal", test_size=0.2, seed=42)
    
    tm = res["modes"]["temporal"]
    assert tm["group_overlap"]["count"] > 0
    
    c = next(x for x in res["checks"] if x["name"] == "temporal_split_group_leakage")
    assert c["result"] == "fail"

def test_split_random_row_overlap():
    loaded = read_table("tests/fixtures/split_dupes.csv")
    spec = ColumnSpec()
    res = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    
    rm = res["modes"]["random"]
    assert rm["row_overlap_count"] > 0
    print(f"DEBUG: row overlap count was {rm['row_overlap_count']}")

def test_split_all_modes_missing_cols():
    loaded = read_table("tests/fixtures/split_groups.csv")
    # no time col, no group col
    spec = ColumnSpec()
    res = build_split(loaded.frame, spec, mode="all", test_size=0.2, seed=42)
    
    assert res["modes"]["group"]["status"] == "not_assessable"
    assert res["modes"]["group"]["reason_code"] == "not_provided"
    
    assert res["modes"]["temporal"]["status"] == "not_assessable"
    assert res["modes"]["temporal"]["reason_code"] == "not_provided"

def test_split_abs_std_mean_diff_missing_target():
    loaded = read_table("tests/fixtures/split_groups.csv")
    spec = ColumnSpec()
    res = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    
    assert res["modes"]["random"]["target_summary"] is None
    assert "target_not_provided" in res["warnings"]

def test_split_target_summary_coincidental_zero_diff():
    loaded = read_table("tests/fixtures/profile_dirty.csv")
    spec = ColumnSpec(target="y", group="grp")
    res = build_split(loaded.frame, spec, mode="random", test_size=0.2, seed=42)
    ts = res["modes"]["random"]["target_summary"]
    assert ts is not None
    assert ts["train"]["mean"] == 11.25
    assert ts["test"]["mean"] == 11.25
    assert ts["abs_std_mean_diff"] == 0.0

def test_split_target_summary_known_diff():
    # Synthetic data: train mean=10, std=2; test mean=13, std=2 -> abs_std_mean_diff == 1.5
    import pandas as pd
    n = 10
    y = np.zeros(n)
    train_vals = [7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 12.0, 13.0]
    test_vals = [13.0 - np.sqrt(2), 13.0 + np.sqrt(2)]
    
    rng = np.random.default_rng(42)
    perm = rng.permutation(n).tolist()
    test_idx = sorted(perm[:2])
    train_idx = sorted(perm[2:])
    
    for i, idx in enumerate(train_idx):
        y[idx] = train_vals[i]
    for i, idx in enumerate(test_idx):
        y[idx] = test_vals[i]
        
    df = pd.DataFrame({"y": y})
    spec = ColumnSpec(target="y")
    res = build_split(df, spec, mode="random", test_size=0.2, seed=42)
    ts = res["modes"]["random"]["target_summary"]
    assert ts is not None
    assert abs(ts["train"]["mean"] - 10.0) < 1e-9
    assert abs(ts["train"]["std"] - 2.0) < 1e-9
    assert abs(ts["test"]["mean"] - 13.0) < 1e-9
    assert abs(ts["test"]["std"] - 2.0) < 1e-9
    assert abs(ts["abs_std_mean_diff"] - 1.5) < 1e-9


