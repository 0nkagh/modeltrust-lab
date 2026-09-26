# ModelTrust Lab

## 1. What this is / what this is NOT
Model-agnostic diagnostic audits for ML evaluation trustworthiness. Research prototype; not production-ready, not a compliance or safety certification tool.

## 2. Status
| Phase | Task | Status | Description |
|---|---|---|---|
| PHASE 2 | T1 | ✅ repo skeleton | Repo initialization |
| PHASE 2 | T2 | ✅ inspect | CSV/Parquet okuma, şema doğrulama, provenance |
| PHASE 2 | T3 | ✅ profile | Dataset profiling |
| PHASE 2 | T4 | ✅ leakage (this task) | Leakage audit |

**Unimplemented modules:** `split`, `report`.

## 3. Requirements
- Python >=3.10

## 4. Quickstart
```bash
python -m venv .venv
# Activate your venv, then:
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
modeltrust --version
pytest
```

## 5. Scope
- Tabular regression only
- No pickle/joblib model loading
- No external APIs
- No data download

## 6. Limitations & evidence status
- Current scenarios tested: Diagnostic indicator only.
- No untested safety claims.
## 7. Exit Codes
- `0`: Success
- `1`: Unexpected internal error
- `2`: Usage error (CLI arg mismatch)
- `3`: Not implemented yet
- `4`: Input or validation error (schema fail, file not found, bad format)

## 8. CLI Commands
### `inspect`
Validates schema and prints canonical JSON provenance to stdout:
```bash
modeltrust inspect --input data.csv --target-col y --delimiter "," --decimal dot
```

### `profile`
Generates comprehensive dataset profile along with schema validation and provenance:
```bash
modeltrust profile --input data.csv --target-col y
```

### `leakage`
Performs diagnostic checks for potential data leakage indicators (e.g., target copy, index-like features, subset row/group/time overlap).
```bash
modeltrust leakage --input data.csv --target-col y --subset-col subset --group-col grp
```
*Note: Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage.*
