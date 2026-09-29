from dataclasses import dataclass, field
import hashlib
import io
import csv
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from modeltrust.errors import InputError

@dataclass(frozen=True)
class LoadedTable:
    frame: pd.DataFrame
    meta: dict[str, Any]

def _sniff_delimiter(lines: list[str]) -> tuple[Optional[str], list[str]]:
    candidates = [",", ";", "\t", "|"]
    valid_candidates = []
    
    for cand in candidates:
        try:
            reader = csv.reader(lines, delimiter=cand)
            field_counts = []
            for row in reader:
                field_counts.append(len(row))
            # Must be > 1 field and consistent
            if len(field_counts) > 0 and all(c > 1 for c in field_counts) and len(set(field_counts)) == 1:
                valid_candidates.append(cand)
        except Exception:
            pass
            
    warnings = []
    if len(valid_candidates) == 1:
        return valid_candidates[0], warnings
    elif len(valid_candidates) > 1:
        raise InputError("ambiguous delimiter; pass --delimiter")
    else:
        warnings.append("single_column_file")
        return None, warnings

def _check_decimal_comma(df: pd.DataFrame, delimiter: str) -> Optional[str]:
    if delimiter == ",":
        return None
    
    pattern = re.compile(r"^-?\d+,\d+$")
    suspect_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        non_nulls = df[col].dropna()
        if len(non_nulls) == 0:
            continue
        matches = non_nulls.astype(str).str.match(pattern).sum()
        if matches / len(non_nulls) >= 0.8:
            suspect_cols.append(col)
                
    if suspect_cols:
        return suspect_cols[0]
    return None

def _count_csv_lines(content_str: str) -> int:
    # Use csv.reader to count lines accurately ignoring newlines in quotes
    reader = csv.reader(io.StringIO(content_str))
    count = 0
    for _ in reader:
        count += 1
    # subtract header
    return max(0, count - 1)

def read_table(
    path: str | Path,
    *,
    fmt: Optional[str] = None,
    delimiter: Optional[str] = None,
    encoding: str = "utf-8-sig",
    decimal: Optional[str] = None,
    max_rows: Optional[int] = None,
    chunk_rows: Optional[int] = None,
    exclude_cols: Optional[list[str]] = None,
) -> LoadedTable:
    path_obj = Path(path)
    if not path_obj.exists():
        raise InputError(f"file not found: {path_obj}")
        
    raw_bytes = path_obj.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    size_bytes = len(raw_bytes)
    
    if fmt is None:
        if path_obj.suffix.lower() == ".parquet":
            fmt = "parquet"
        else:
            fmt = "csv"
            
    warnings = []
    meta = {
        "path": str(path),
        "format": fmt,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "nrows_total": 0,
        "nrows_read": 0,
        "truncated": False,
        "ncols": 0,
        "columns": [],
        "columns_sha256": "",
        "duplicate_headers": [],
        "unnamed_columns": [],
        "warnings": warnings,
    }
    
    if fmt == "parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise InputError("parquet support requires the optional extra: pip install -e .[parquet]")
            
        meta["delimiter"] = None
        meta["encoding"] = None
        
        pq_file = pq.ParquetFile(path_obj)
        nrows_total = pq_file.metadata.num_rows
        meta["nrows_total"] = nrows_total
        

        df = pd.read_parquet(path_obj)
        if max_rows is not None:
            df = df.head(max_rows)
            
        meta["nrows_read"] = len(df)

    else:
        # CSV
        try:
            content_str = raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            raise InputError(f"file is not valid {encoding.upper()}; re-save as {encoding.upper()} or pass --encoding <name>")
            
        has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
        meta["bom_stripped"] = has_bom if encoding.lower() == "utf-8-sig" else False
        meta["encoding"] = encoding
        
        # Sniff delimiter
        lines_for_sniff = []
        reader_sniff = io.StringIO(content_str)
        for i, line in enumerate(reader_sniff):
            if i >= 50:
                break
            lines_for_sniff.append(line)
            
        sniffed_delim, sniff_warnings = _sniff_delimiter(lines_for_sniff)
        warnings.extend(sniff_warnings)
        
        if delimiter is None:
            delimiter = sniffed_delim
            if delimiter is None:
                delimiter = ","
        meta["delimiter"] = delimiter
        
        if decimal == "comma" and delimiter == ",":
            raise InputError("decimal comma and delimiter comma is ambiguous")
            
        # Count total rows
        meta["nrows_total"] = _count_csv_lines(content_str)
        
        # Read df
        read_kwargs = {
            "sep": delimiter,
            "encoding": encoding,
            "index_col": False,
        }
        if decimal:
            read_kwargs["decimal"] = "." if decimal == "dot" else ","
        if max_rows is not None:
            read_kwargs["nrows"] = max_rows
            
        try:
            df = pd.read_csv(io.StringIO(content_str), **read_kwargs)
        except Exception as e:
            raise InputError(f"Failed to parse CSV: {e}")
            
        meta["nrows_read"] = len(df)

        # Check decimal comma
        if decimal is None:
            suspect_col = _check_decimal_comma(df, delimiter)
            if suspect_col:
                raise InputError(f"decimal comma suspected in column {suspect_col}; pass --decimal comma (or --decimal dot)")
                
        # Manually check duplicate headers from raw string before they are mangled
        reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
        try:
            headers = next(reader)
        except StopIteration:
            headers = []
        
        seen = set()
        dups = set()
        for h in headers:
            if h in seen:
                dups.add(h)
            seen.add(h)
        if dups:
            meta["duplicate_headers"] = sorted(list(dups))
            raise InputError(f"duplicate column names found: {meta['duplicate_headers']}")

    # Record original file columns for validation
    meta["file_columns"] = list(df.columns)

    if exclude_cols is not None:
        deduped = list(dict.fromkeys(exclude_cols))
        cols_to_drop = [c for c in deduped if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        meta["excluded_columns"] = deduped

    # Columns check
    cols = list(df.columns)
    meta["ncols"] = len(cols)
    meta["columns"] = cols
    
    # Check unnamed/empty
    unnamed = [c for c in cols if not str(c).strip() or str(c).startswith("Unnamed: ")]
    if unnamed:
        meta["unnamed_columns"] = unnamed
        warnings.append("unnamed_columns")
        
    meta["columns_sha256"] = hashlib.sha256("\n".join(str(c) for c in cols).encode("utf-8")).hexdigest()
    
    meta["truncated"] = (max_rows is not None) and (meta["nrows_total"] > max_rows)
    
    return LoadedTable(frame=df, meta=meta)


load = read_table

