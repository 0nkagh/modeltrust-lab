# ModelTrust Lab

## 1. What this is / what this is NOT
Model-agnostic diagnostic audits for ML evaluation trustworthiness. Research prototype; not production-ready, not a compliance or safety certification tool.

## 2. Status
| Phase | Task | Status | Description |
|---|---|---|---|
| PHASE 2 | T1 | ✅ repo skeleton | Repo initialization |
| PHASE 2 | T2 | ✅ inspect | CSV/Parquet okuma, şema doğrulama, provenance |
| PHASE 2 | T3 | ✅ profile | Dataset profiling |
| PHASE 2 | T5 | ✅ split | Data splitting |
| PHASE 2 | T6 | ✅ report (this task) | JSON and Markdown report generation |

**Unimplemented modules:** None.

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
- `3`: Reserved/unused (formerly not implemented)
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

### `split`
Performs data splitting logic and overlap checks (random, group, temporal).
```bash
modeltrust split --input data.csv --target-col y --group-col grp --time-col ts
```

### `report`
Generates full JSON and Markdown diagnostic reports, writing them to a directory. Tek komutta profil + leakage + split + model hatası denetimi gerçekleştirilebilir.
```bash
modeltrust report --input data.csv --target-col y --group-col grp --out-dir ./reports

# With evaluation enabled (single command profile + leakage + split + model error evaluation):
modeltrust report --input data.csv --target-col y --group-col grp --pred-col my_preds --evaluate --out-dir ./reports
# Produces: ./reports/report.json and ./reports/report.md
```
*Note: This tool produces diagnostic indicators. It is not a certificate.*

### `evaluate`
Evaluates models against simple baselines (mean, ols) and computes test metrics (MAE, RMSE, R²). Also supports CV, group-level error analysis, and uncertainty interval coverage.
```bash
modeltrust evaluate --input data.csv --target-col y --pred-col my_preds --split-mode random --cv random --folds 5
# Or to evaluate baselines:
modeltrust evaluate --input data.csv --target-col y --model both

# Uncertainty interval coverage evaluation:
# Calibrated fixture (measured coverage: 0.910 vs nominal 0.90):
modeltrust evaluate --input tests/fixtures/intervals_calibrated.csv --target-col y --lower-col lo --upper-col hi --nominal-coverage 0.9
# Overconfident fixture (measured coverage: 0.325 vs nominal 0.90):
modeltrust evaluate --input tests/fixtures/intervals_overconfident.csv --target-col y --lower-col lo --upper-col hi --nominal-coverage 0.9
```
- `--model`: `mean`, `ols`, `both` (default). If `--pred-col` is given, the supplied predictions are evaluated.
- `--split-mode`: `random` (default), `group`, `temporal`. Determines single holdout test allocation.
- `--cv`: `none` (default), `random`, `group`, `temporal`. Performs cross-validation.
- `--folds`: number of folds for CV (default 5).
- `--lower-col`, `--upper-col`: Specify columns containing prediction interval bounds to calculate empirical coverage.
- `--nominal-coverage`: Expected coverage probability (default 0.95).

*Note: Diagnostic indicators only. Evaluated empirical coverage on a single split is not a distribution-free calibration guarantee.*

### `shift`
Runs OOD and distribution shift diagnostics by splitting data and comparing train vs test distributions.
```bash
modeltrust shift --input data.csv --target-col y --time-col ts --split-mode temporal
# Or with random split:
modeltrust shift --input data.csv --target-col y
```
- `--split-mode`: `random` (default), `group`, `temporal`. Determines train/test split for OOD and drift checks.
- `--test-size`: fraction of data for test set (default 0.2).
*Note: Heuristic thresholds; no significance testing. Diagnostic indicators only.*

### `report --shift`
Add `--shift` to include OOD and distribution shift diagnostics in the report. Section 6 expands to two tables (split comparison + distribution shift & OOD):
```bash
modeltrust report --input data.csv --target-col y --time-col ts --shift --out-dir ./reports

# Combined with evaluation:
modeltrust report --input data.csv --target-col y --time-col ts --shift --evaluate --out-dir ./reports
```
*Note: `--split-mode` and `--test-size` are valid with either `--evaluate` or `--shift`.*

### `card`
Generates a diagnostic summary card (JSON and Markdown) containing data provenance, test coverage, and evaluated metrics. This command automatically executes schema validation, dataset profiling, and leakage detection. Splitting checks are performed when a group or time column is provided; otherwise, they are recorded as skipped.
```bash
modeltrust card --input data.csv --target-col y --out-dir ./card_reports
```
- `--manifest`: Generates a `manifest.json` reproducibility manifest in the output directory.

Example `manifest.json`:
```json
{
  "manifest_schema_version": 1,
  "tool": {"name": "modeltrust", "version": "0.1.0"},
  "command": "python -m modeltrust card --input data.csv --target-col y --manifest --out-dir ./card_reports",
  "input": {"path": "data.csv", "sha256": "...", "rows": 200, "columns": 3},
  "environment": {"python": "3.12.8", "pandas": "3.0.6", "numpy": "2.2.6", "platform": "win32"},
  "seed": 42,
  "git": {"commit": "...", "dirty": false},
  "config": {"thresholds": {"MIN_ROWS_FOR_COPY_CHECK": 5}},
  "outputs": {"card_json_sha256": "...", "card_md_sha256": "..."},
  "warnings": []
}
```

*Note: The card is a diagnostic summary, not a certificate. It contains no performance guarantee and no compliance claim.*
