# ModelTrust Lab

## 1. What this is / what this is NOT
Model-agnostic diagnostic audits for ML evaluation trustworthiness. Research prototype; not production-ready, not a compliance or safety certification tool.

## 2. Status
| Phase | Task | Status | Description |
|---|---|---|---|
| PHASE 2 | T1 | Repo skeleton only | Audit modules not implemented |

## 3. Requirements
- Python >=3.10

## 4. Quickstart
```bash
python -m venv .venv
# Activate your venv, then:
pip install -e ".[dev]"
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
