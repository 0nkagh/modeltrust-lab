import pytest
import hashlib
from pathlib import Path
from modeltrust.dataio import read_table
from modeltrust.errors import InputError

def test_simple_ok():
    path = Path("tests/fixtures/simple_ok.csv")
    loaded = read_table(path)
    assert loaded.meta["nrows_total"] == 2
    assert loaded.meta["nrows_read"] == 2
    assert loaded.meta["truncated"] is False
    assert loaded.meta["ncols"] == 3
    assert loaded.meta["columns"] == ["id", "y", "grp"]
    
def test_turkish_bom_semicolon():
    path = Path("tests/fixtures/turkish_bom_semicolon.csv")
    loaded = read_table(path)
    assert loaded.meta["bom_stripped"] is True
    assert loaded.meta["delimiter"] == ";"
    assert loaded.meta["columns"] == ["id", "hedef", "grup"]
    
def test_decimal_comma_fail():
    path = Path("tests/fixtures/decimal_comma.csv")
    with pytest.raises(InputError, match="--decimal comma"):
        read_table(path)
        
def test_decimal_comma_ok():
    path = Path("tests/fixtures/decimal_comma.csv")
    loaded = read_table(path, decimal="comma", delimiter=";")
    assert loaded.frame["y"].iloc[0] == 2.5
    
def test_duplicate_headers():
    path = Path("tests/fixtures/dup_headers.csv")
    with pytest.raises(InputError, match="duplicate column names"):
        read_table(path)
        
def test_quoted_commas():
    path = Path("tests/fixtures/quoted_commas.csv")
    loaded = read_table(path)
    assert loaded.meta["delimiter"] == ","
    assert loaded.meta["ncols"] == 3
    assert loaded.meta["nrows_total"] == 2

def test_sha256_match():
    path = Path("tests/fixtures/simple_ok.csv")
    loaded = read_table(path)
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert loaded.meta["sha256"] == expected

def test_max_rows():
    path = Path("tests/fixtures/simple_ok.csv")
    loaded = read_table(path, max_rows=1)
    assert loaded.meta["nrows_read"] == 1
    assert loaded.meta["nrows_total"] == 2
    assert loaded.meta["truncated"] is True

def test_parquet_support():
    path = Path("tests/fixtures/dummy.parquet")
    # if pyarrow is installed, this will fail on file not found
    # if not, it will fail on pyarrow missing
    try:
        import pyarrow
    except ImportError:
        with pytest.raises(InputError, match=r"\[parquet\]"):
            read_table(path, fmt="parquet")
    else:
        pytest.skip("pyarrow installed, skipping absent-extra test")

def test_columns_sha256_order():
    from modeltrust.dataio import LoadedTable
    import pandas as pd
    
    df1 = pd.DataFrame(columns=["a", "b"])
    df2 = pd.DataFrame(columns=["b", "a"])
    
    # manual creation or writing a dummy to file...
    # instead of writing, we can just test the hashing logic via mock or writing two files
    # Actually dataio hashes '\n'.join(cols). Let's write two files and read.
    p1 = Path("tests/fixtures/tmp1.csv")
    p2 = Path("tests/fixtures/tmp2.csv")
    p1.write_text("a,b\n1,2", encoding="utf-8")
    p2.write_text("b,a\n2,1", encoding="utf-8")
    
    try:
        l1 = read_table(p1)
        l2 = read_table(p2)
        assert l1.meta["columns_sha256"] != l2.meta["columns_sha256"]
    finally:
        p1.unlink(missing_ok=True)
        p2.unlink(missing_ok=True)
