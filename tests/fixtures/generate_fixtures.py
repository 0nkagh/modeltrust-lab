"""
Fixture generator for ModelTrust Lab leakage tests.
Seeds used:
- leak_clean.csv: 42
- leak_nearcopy.csv: (no RNG needed)
"""
import pandas as pd
import numpy as np
from pathlib import Path

def generate_leak_clean(path: Path):
    np.random.seed(42)
    x1 = np.random.rand(30)
    x2 = np.random.rand(30)
    i = np.arange(30) % 3
    y = 0.8 * x1 + 0.4 * x2 + 0.2 * i + np.random.randn(30) * 0.5
    
    grp = [f'G{j//4}' for j in range(20)] + [f'G{5+j//4}' for j in range(10)]
    subset = ['train'] * 20 + ['test'] * 10
    
    df = pd.DataFrame({
        'y': y,
        'x1': x1,
        'x2': x2,
        'grp': grp,
        'subset': subset
    })
    
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_leak_nearcopy(path: Path):
    i = np.arange(25)
    y = 10 + 5 * i
    x1 = y * 1.0001
    
    df = pd.DataFrame({
        'y': y,
        'x1': x1
    })
    
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_split_groups(path: Path):
    np.random.seed(7)
    x = np.arange(40, dtype=float)
    y = 5 + 0.5 * x + np.random.randn(40)
    grp = []
    for i in range(1, 9):
        grp.extend([f"G{i}"] * 5)
    
    df = pd.DataFrame({"y": y, "grp": grp, "x": x})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_split_time(path: Path):
    ts = pd.date_range("2024-01-01", periods=30)
    grp = [f"G{(i % 5) + 1}" for i in range(30)]
    y = np.arange(30, dtype=float)
    
    df = pd.DataFrame({"y": y, "grp": grp, "ts": ts.strftime('%Y-%m-%d')})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_eval_exact_linear(path: Path):
    x = np.arange(1, 41, dtype=float)
    y = 2 * x + 1
    df = pd.DataFrame({'x': x, 'y': y})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_eval_preds(path: Path):
    y = np.arange(1, 31, dtype=float)
    pred = np.copy(y)
    pred[20:] += 3.0
    grp = ['G1'] * 10 + ['G2'] * 10 + ['G3'] * 10
    df = pd.DataFrame({'y': y, 'pred': pred, 'grp': grp})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_eval_nan(path: Path):
    x1 = np.arange(25, dtype=float)
    x2 = np.arange(25, dtype=float)
    y = np.arange(25, dtype=float)
    
    # x2'de 4 NaN
    x2[2] = np.nan
    x2[7] = np.nan
    x2[12] = np.nan
    x2[17] = np.nan
    
    # y'de 3 NaN
    y[5] = np.nan
    y[10] = np.nan
    y[15] = np.nan
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_eval_const_target(path: Path):
    x = np.arange(25, dtype=float)
    y = np.full(25, 5.0)
    df = pd.DataFrame({'x': x, 'y': y})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_leak_std_full(path: Path):
    x_raw = np.arange(1, 31, dtype=float)
    x_z = (x_raw - x_raw.mean()) / x_raw.std(ddof=0)
    y = x_raw * 0.5 + 3.0
    df = pd.DataFrame({'x_raw': x_raw, 'x_z': x_z, 'y': y})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_leak_minmax_full(path: Path):
    x_raw = np.arange(1, 26, dtype=float)
    x_norm = (x_raw - x_raw.min()) / (x_raw.max() - x_raw.min())
    y = x_raw * 2.0 + 1.0
    df = pd.DataFrame({'x_raw': x_raw, 'x_norm': x_norm, 'y': y})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_leak_det_feature(path: Path):
    rng = np.random.RandomState(42)
    y = np.arange(1, 31, dtype=float)
    x = rng.randn(30)
    x_det = 2.0 * y + 1.0
    df = pd.DataFrame({'x': x, 'x_det': x_det, 'y': y})
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

def generate_leak_name_hints(path: Path):
    rng1 = np.random.RandomState(1)
    rng2 = np.random.RandomState(2)
    rng3 = np.random.RandomState(3)
    y = np.arange(1, 21, dtype=float)
    y_mean_3 = rng1.randn(20)
    x_ratio = rng2.randn(20)
    z_score_x = rng3.randn(20)
    df = pd.DataFrame({
        'y_mean_3': y_mean_3,
        'x_ratio': x_ratio,
        'z_score_x': z_score_x,
        'y': y
    })
    csv_str = df.to_csv(index=False, lineterminator='\n')
    path.write_bytes(csv_str.encode('utf-8'))

if __name__ == "__main__":
    out_dir = Path(__file__).parent
    generate_leak_clean(out_dir / "leak_clean.csv")
    generate_leak_nearcopy(out_dir / "leak_nearcopy.csv")
    generate_split_groups(out_dir / "split_groups.csv")
    generate_split_time(out_dir / "split_time.csv")
    generate_eval_exact_linear(out_dir / "eval_exact_linear.csv")
    generate_eval_preds(out_dir / "eval_preds.csv")
    generate_eval_nan(out_dir / "eval_nan.csv")
    generate_eval_const_target(out_dir / "eval_const_target.csv")
    generate_leak_std_full(out_dir / "leak_std_full.csv")
    generate_leak_minmax_full(out_dir / "leak_minmax_full.csv")
    generate_leak_det_feature(out_dir / "leak_det_feature.csv")
    generate_leak_name_hints(out_dir / "leak_name_hints.csv")
    print("Fixtures generated.")

