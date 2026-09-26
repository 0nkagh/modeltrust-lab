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

if __name__ == "__main__":
    out_dir = Path(__file__).parent
    generate_leak_clean(out_dir / "leak_clean.csv")
    generate_leak_nearcopy(out_dir / "leak_nearcopy.csv")
    print("Fixtures generated.")
