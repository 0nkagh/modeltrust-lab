# ModelTrust Lab

[![CI](https://github.com/0nkagh/modeltrust-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/0nkagh/modeltrust-lab/actions/workflows/ci.yml)

## 1. What this is / what this is NOT
Model-agnostic diagnostic audits for ML evaluation trustworthiness. Research prototype; not production-ready, not a compliance or safety certification tool.

## 2. Status

Version `0.1.0` — first release; the `v0.1.0` tag is created when the repository is published. All ten diagnostic questions are addressable;
see `docs/ASSESSABILITY.md` for the per-question accessibility matrix (Q10 is `partial` by design,
because it reports on the report itself).

| Area | State |
|---|---|
| CLI surface (8 commands) | implemented; contract-locked by tests |
| Deterministic JSON + Markdown output | implemented; scope documented above |
| Answerability semantics (`answered` / `partial` / `not_assessable`) | implemented |
| Controls that cannot run | recorded with a `reason_code`; never silently skipped |
| Case study on deliberately corrupted data | `docs/CASE_STUDY.md` |
| Measured comparison with Evidently | `docs/COMPARISON.md` |
| Evidence status | research prototype; diagnostic indicators only; no production, compliance or safety claim |

Phase history and governance records: `docs/DECISIONS.md`, `docs/INCIDENTS.md`, `CHANGELOG.md`.

## 3. Requirements
- Python >=3.11

## 4. Quickstart
```bash
python -m venv .venv
# Activate your venv, then:
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
modeltrust --version
pytest
```

**Determinism scope.** Re-running the same command with the same input and the *same* `--out-dir`
produces byte-identical outputs (`report.json`, `report.md`, `card.json`, `card.md`, `manifest.json`).
Output files embed the invocation string, so changing `--out-dir` changes their hashes; `manifest.json`
also records the current `git.commit`, so a new commit changes its hash.

## Documentation

- Changelog: `CHANGELOG.md`
- Methods, thresholds and limitations: `docs/METHODS.md`
- Question accessibility matrix: `docs/ASSESSABILITY.md`
- Case study (deliberately corrupted synthetic data): `docs/CASE_STUDY.md`
- Real-data case study (UCI Student Performance, CC BY 4.0): `docs/CASE_STUDY_REAL.md`
- External tool comparison (Evidently): `docs/COMPARISON.md`
- Environment and setup evidence: `docs/ENVIRONMENT.md`
- Decision log: `docs/DECISIONS.md` *(kept in Turkish: append-only historical record)*
- Incident log: `docs/INCIDENTS.md` *(kept in Turkish: append-only historical record)*

`docs/PHASE-1-PLAN.md` and `docs/PHASE-3-EXIT.md` are also kept in Turkish for the same reason. See `D-110` in the decision log.

## 5. Scope
- Tabular regression only
- No pickle/joblib model loading
- No external APIs
- No data download (the tool never downloads data; the repository ships one real dataset for the case study)

## 6. Limitations & evidence status
- Current scenarios tested: Diagnostic indicator only.
- No untested safety claims.
- If a column named by `--group-col` / `--time-col` / `--pred-col` does not exist, the run fails with a non-zero exit code and an explicit message; the card/report is not produced.
## 7. Exit Codes
- `0`: Success
- `1`: Unexpected internal error
- `2`: Usage error (CLI arg mismatch)
- `3`: Reserved/unused (formerly not implemented)
- `4`: Input or validation error (schema fail, file not found, bad format)

## 8. CLI Commands

The commands below use `data.csv` as a placeholder for your own file. To try them
without preparing data, use the fixtures shipped with the repository (for example
`tests/fixtures/simple_ok.csv`, `tests/fixtures/eval_preds.csv`, `tests/fixtures/shift_drift.csv`).

```powershell
modeltrust inspect --input tests/fixtures/simple_ok.csv --target-col y --delimiter "," --decimal dot
modeltrust card --input tests/fixtures/eval_preds.csv --target-col y --pred-col pred --group-col grp --out-dir ./reports/card_example
modeltrust report --input tests/fixtures/shift_drift.csv --target-col y --time-col ts --shift --evaluate --card --out-dir ./reports/full_example
```
All three commands exit with code 0 and write their outputs to the given --out-dir.
A worked example on deliberately corrupted synthetic data: see docs/CASE_STUDY.md.

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
Generates full JSON and Markdown diagnostic reports, writing them to a directory. A single command runs profiling, leakage, split and model-error auditing.
```bash
modeltrust report --input data.csv --target-col y --group-col grp --out-dir ./reports

# With evaluation enabled (single command profile + leakage + split + model error evaluation):
modeltrust report --input data.csv --target-col y --group-col grp --pred-col my_preds --evaluate --out-dir ./reports
# Produces: ./reports/report.json and ./reports/report.md

# To generate a diagnostic card simultaneously (single load):
modeltrust report --input data.csv --target-col y --card --out-dir ./reports
# Produces: report.json, report.md, card.json, and card.md
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
  "environment": {"python": "3.12.8", "pandas": "3.0.6", "numpy": "2.5.3", "platform": "win32"},
  "seed": 42,
  "git": {"commit": "...", "dirty": false},
  "config": {"thresholds": {"MIN_ROWS_FOR_COPY_CHECK": 5}},
  "outputs": {"card_json_sha256": "...", "card_md_sha256": "..."},
  "warnings": []
}
```

*Note: The card is a diagnostic summary, not a certificate. It contains no performance guarantee and no compliance claim.*
## Related tools and positioning

ModelTrust Lab does not invent a new statistical method; most of the questions this tool addresses are also answered by other tools:

| Tool | What it does | Overlapping questions |
|---|---|---|
| [Evidently](https://github.com/evidentlyai/evidently) (Apache-2.0) | Drift tests, data quality, performance dashboards | missing/duplicate records, drift, OOD |
| [Deepchecks](https://github.com/deepchecks/deepchecks) (AGPL) | Validation suite (data integrity, train/test leakage, drift) | missing/duplicate records, target/group leakage, split, drift, OOD |
| [NannyML](https://github.com/NannyML/nannyML) (Apache-2.0) | Label-free performance estimation, drift timing | drift |
| [Great Expectations](https://greatexpectations.io/) | Schema and data validation (expectation suites) | missing/duplicate records |

Three deliberate differences:

- **Dependency discipline:** only `numpy` + `pandas`. No scipy/sklearn/torch; the KS test and Wilson intervals are implemented by hand.
- **Determinism and offline operation:** two runs into the same output directory are byte-identical; the manifest carries the input's sha256; there is no telemetry, no network access and no model loading.
- **Answerability semantics:** every check returns `answered` / `partial` / `not_assessable` with a `reason_code` and an evidence pointer. "This check cannot be run on this input, and here is why" is part of the contract.

A measured side-by-side run, version metadata and scope differences: [`docs/COMPARISON.md`](docs/COMPARISON.md).

## Continuous integration

Every push to `main` and every pull request runs GitHub Actions (`.github/workflows/ci.yml`):

- the full test suite on Python 3.11, 3.12 and 3.13 (Ubuntu) and Python 3.12 (Windows);
- a sha256 integrity check of the committed case-study data (`examples/case_study/case_study.csv`);
- a wheel build, a clean-venv install and a CLI smoke test of the built artifact;
- a byte-level determinism check that runs the canonical case-study command twice into the same output directory and compares file hashes.

Requires Python >= 3.11. Only the versions listed above are tested; no other version is claimed as supported.

## License

MIT — see [LICENSE](LICENSE).
