import platform
import pandas as pd
import numpy as np

from modeltrust.dataio import LoadedTable
from modeltrust.schema import ColumnSpec, validate_input
from modeltrust import __version__

def build_provenance(loaded: LoadedTable, spec: ColumnSpec, *, seed: int, path_as_given: str) -> dict:
    schema_res = validate_input(loaded.frame, loaded.meta, spec)
    
    # Handle the meta.warnings correctly
    warnings = list(loaded.meta.get("warnings", []))
    
    return {
        "tool": {"name": "modeltrust", "version": __version__},
        "run_metadata": {"generated_at": None, "seed": seed},
        "input": {
            "path": path_as_given,
            "format": loaded.meta["format"],
            "sha256": loaded.meta["sha256"],
            "size_bytes": loaded.meta["size_bytes"],
            "encoding": loaded.meta["encoding"],
            "bom_stripped": loaded.meta.get("bom_stripped", False),
            "delimiter": loaded.meta["delimiter"],
            "decimal": loaded.meta.get("decimal", "dot"), # not strictly tracked in meta, default to dot or from meta if passed
            "nrows_total": loaded.meta["nrows_total"],
            "nrows_read": loaded.meta["nrows_read"],
            "truncated": loaded.meta["truncated"],
            "ncols": loaded.meta["ncols"],
            "columns": loaded.meta["columns"],
            "columns_sha256": loaded.meta["columns_sha256"],
            "duplicate_headers": loaded.meta.get("duplicate_headers", []),
            "unnamed_columns": loaded.meta.get("unnamed_columns", []),
            "warnings": warnings
        },
        "column_spec": {
            "target": spec.target,
            "prediction": spec.prediction,
            "group": spec.group,
            "time": spec.time
        },
        "schema": schema_res,
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "platform": platform.platform()
        }
    }
