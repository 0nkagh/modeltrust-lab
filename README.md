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
- See docs for more details.
