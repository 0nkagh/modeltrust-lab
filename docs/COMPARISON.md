# External Tool Comparison: Evidently

## 1. Purpose and honesty framing

This is not a benchmark.
This study aims to document the differences in contract, methodology, and output by placing ModelTrust Lab's diagnostic audit results side-by-side with Evidently, a current and popular open-source data drift tool.
The study is strictly limited to a single tool (Evidently), a single version (0.7.23), a single dataset (`case_study.csv`), and a single date (2026-09-29).
No claims of superiority ("better", "superior", "unrivaled") are made between the tools; only the directly observed values, method choices, and contract semantics are reported impartially.
Evidently was selected as the comparison tool because it is considered the most common reference for tabular data quality and drift monitoring in the open-source world.

## 2. Environment and versions

- **Date**: 2026-09-29
- **Platform**: Microsoft Windows 10.0.26200, Win32NT, PowerShell Core 7.6.6
- **ModelTrust Lab Version**: 0.0.1.dev0
- **Evidently Version**: 0.7.23 — Python 3.12.8, temporary virtual environment `$env:TEMP\mt_ev_venv`
- **Installation Command**: `& "$env:TEMP\mt_ev_venv\Scripts\python.exe" -m pip install --disable-pip-version-check "evidently==0.7.23"`
- **`pyvenv.cfg` content**:
  ```ini
  home = C:\Users\agah\AppData\Local\Programs\Python\Python312
  include-system-site-packages = false
  version = 3.12.8
  executable = C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe
  command = C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe -m venv C:\Users\agah\AppData\Local\Temp\mt_ev_venv
  ```
- **Pip dump (Evidently venv)**: 80 packages, SHA-256: `DD0004C1F9CBE8D279D28A1F0D897DEA7D2B519E158E595719033BA302BB7925`. Top 20 packages:
  ```text
  annotated-doc==0.0.5
  annotated-types==0.8.0
  anyio==4.15.1
  appdirs==1.4.4
  certifi==2026.7.22
  cffi==2.1.1
  charset-normalizer==3.5.1
  click==8.5.0
  cloudpickle==3.1.2
  colorama==0.4.6
  cryptography==50.0.1
  defusedxml==0.7.1
  deprecation==2.1.0
  distro==1.9.0
  dynaconf==3.3.5
  evidently==0.7.23
  Faker==40.40.0
  filelock==4.0.6
  formulaic==1.2.2
  fsspec==2026.9.0
  ```
- **Telemetry**: Runs were performed with `DO_NOT_TRACK=1` and `ITERATIVE_DO_NOT_TRACK=1`; the installed `iterative_telemetry` package reads the `DO_NOT_TRACK_ENV = "ITERATIVE_DO_NOT_TRACK"` key and uses the `os.environ.get(DO_NOT_TRACK_ENV, None) is None` condition in `is_enabled()` (source: `iterative_telemetry/__init__.py:29-30, 164-169`).

## 3. Input alignment

Both tools were provided with the exact same data rows and the exact same splits.

- **Source Data**: `examples/case_study/case_study.csv` (600 rows, 12 columns, SHA-256: `9587B66886A942EE9E9589FE65F000406F6F9F40F41BA7E7BF0B5E0CF9E942DA`)
- **Split Method**: Stable sorting by timestamp (`ts`), first 80% (480 rows) separated as reference/train, last 20% (120 rows) as test/current split.
- **ModelTrust Alignment**: In `report.json` under the `split.modes.temporal` (and `shift.split.mode: "temporal"`) field, `n_train: 480`, `n_test: 120`. `time_ranges`: `train_max: 2025-04-18`, `test_min: 2025-04-19`. The block does not explicitly state the sorting rule as text; however, by sorting the `ts` column in ascending order, the first 480 rows are separated as train, and the last 120 rows as test, and this is locked with `report.json:split.modes.temporal.train_row_indices_sha256`.
- **Evidently Alignment**: The `reference.csv` and `current.csv` splits were used in the `Report.run(reference_data=ref, current_data=cur)` call.
- **Split Files**:
  - `reference.csv`: 480 rows, SHA-256: `C8168216AAA1A859B25194A6AEE8D4F04774844FD82B71AD2D79FBFDEC3FD26D`
  - `current.csv`: 120 rows, SHA-256: `0F1502DF4EA780D77B70881C9A080CA2200F798139B88442ADA0CC02A724788D`
- **Columns**: `['row_id', 'ts', 'site', 'region', 'x1', 'x2', 'x3', 'y', 'pred', 'lo', 'hi', 'y_proxy']`

## 4. Measured results (side by side)

*Run Metadata: New API canonical run, 2026-09-29. Output file `drift.json` SHA-256: `9EE1D72256B63C45B7E0173F9959B25A4903BB4DC3D40AA885F987984FD2DEA1`.*

### 4.a ModelTrust Lab (temporal split) — column-based KS

| Column | KS statistic | Threshold | Decision | Source |
|---|---|---|---|---|
| `row_id` | 1.000000 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.row_id` |
| `x1` | 0.150000 | 0.25 | pass | `report.json:shift.drift.feature_ks.features.x1` |
| `x2` | 0.650000 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.x2` |
| `x3` | 0.123932 | 0.25 | pass | `report.json:shift.drift.feature_ks.features.x3` |
| `pred` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.pred` |
| `lo` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.lo` |
| `hi` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.hi` |
| `y_proxy` | 0.333333 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.y_proxy` |
| `y` (target, `drift.target_ks`) | 0.331250 | 0.25 | fail | `report.json:shift.drift.target_ks.ks_stat` |

*Note: The ModelTrust diagnostic report does not calculate the two-sample KS drift metric for categorical columns (`site`, `region`) and the timestamp column (`ts`).*

### 4.b Evidently (`DataDriftPreset`, New API) — column-based (12 columns)

| Column | Method | Value | Threshold | Decision | Source (`drift.json` metric configuration) |
|---|---|---|---|---|---|
| `row_id` | K-S p_value | 1.987767e-129 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `x1` | K-S p_value | 0.024860 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `x2` | K-S p_value | 3.722182e-39 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `x3` | K-S p_value | 0.096779 | 0.05 | No Drift | `evidently:metric_v2:ValueDrift` |
| `y` | K-S p_value | 8.309481e-10 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `pred` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `lo` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `hi` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `y_proxy` | K-S p_value | 6.293809e-10 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `site` | chi-square p_value | 0.999999 | 0.05 | No Drift | `evidently:metric_v2:ValueDrift` |
| `region` | chi-square p_value | 1.000000 | 0.05 | No Drift | `evidently:metric_v2:ValueDrift` |
| `ts` | Percentile text content drift | 0.933528 | 0.95 | Drift | `evidently:metric_v2:ValueDrift` |

### 4.c Reconciliation (summary ↔ column-based)

- **Evidently summary metric**: `DriftedColumnsCount(drift_share=0.5)` -> `{'count': 9.0, 'share': 0.75}` (9/12 columns drifted) [source: `drift.json:DriftedColumnsCount` — `evidently:metric_v2:DriftedColumnsCount`].
- **Column-based count**: Drift was detected as 8/12 numerical/categorical columns (`row_id, x1, x2, y, pred, lo, hi, y_proxy`) exceeded the threshold value (0.05).
- **Explanation of the Difference (9 ↔ 8)**: The 9th drifted column is the `ts` text column. When examining the library source code (`evidently/legacy/calculations/stattests/text_content_drift.py:10-15` and `evidently/legacy/utils/data_drift_utils.py:224-257`), it is observed that a domain classifier is trained for `ts`. The decision rule works as "ROC-AUC > random classifier percentile (~0.55)"; the ROC-AUC score for `ts` is 0.9335.
- **Unidentified run**: The source of the different values entered into the document in T20-R1 could not be determined: there is no `evidently.report` entry point in this version (`ModuleNotFoundError`), and the legacy calculation path (`evidently.legacy.calculations.data_drift`) could not be run with the same splits (`ValueError: column_mapping should be present`). The canonical path is in §4.b; numbers from unidentified sources are not used in this document.
- **ModelTrust side**: Out of 4 shift checks, 3 are `fail` (`drift.feature_ks`, `drift.target_ks`, `ood.feature_range`), 1 is `pass` (`ood.mahalanobis`).
- **Observation Notes**:
  - `x1`: While ModelTrust yields `pass` because it stays below the practical effect size threshold (KS stat 0.15 < 0.25); Evidently reported `Drift` due to statistical significance (p=0.0249 < 0.05). This reflects the methodological difference between the effect size approach and the hypothesis testing approach.
  - `x2` (injected shift): Strongly `fail` / `Drift` in both tools.
  - `row_id`: The monotonically increasing identity column artificially produced drift in both tools.
  - `OOD range and Mahalanobis`: While present as independent diagnostic checks in ModelTrust, they do not have a direct equivalent in the Evidently `DataDriftPreset`.
  - `Categorical columns`: While ModelTrust operates with a numerical focus, Evidently automatically applied the chi-square test.

- **Reproducibility of canonical run**: A new run with the exact same commands and splits bit-for-bit reproduced the `drift.json` recorded in T20 (sha256: `9EE1D72256B63C45B7E0173F9959B25A4903BB4DC3D40AA885F987984FD2DEA1`). [A6-B] The source of the different values that entered the document in T20-R1 **could not be determined**; those numbers are not used in this document.

## 5. Contract differences

1. **Assessability Semantics (`not_assessable`)**: In Evidently, there is no distinction of "this check cannot be performed with this input + reason" (`status: not_assessable`, `reason_code`); the tool runs when it finds suitable data types, and when it doesn't, it raises an error or stays silent. In ModelTrust Lab, missing parameters (e.g., not providing a time/group column) or the pipeline code requirement is an explicit contract state.
2. **Output Detail and Visualization**: Evidently produces detailed statistical distributions, histograms, and interactive HTML dashboards on a column basis. ModelTrust Lab, on the other hand, does not provide a visual interface; it produces machine-readable JSON, lightweight Markdown, and a single-page diagnostic card (`card`).
3. **Threshold Approach**: ModelTrust Lab uses predetermined heuristic thresholds focused on practical effect size (e.g., KS stat >= 0.25). Evidently, on the other hand, makes decisions based on the p-value (default alpha = 0.05) of the chosen statistical test. This situation can create decision differences in small deviations like `x1`; no claim is made as to which is correct, it is a methodology difference.
4. **Dependency Profile and Portability**: ModelTrust Lab carries only `numpy` and `pandas` dependencies; it contains no compilation, external C/Fortran libraries, or heavy visualization dependencies. Evidently relies on a broad ecosystem of 80 packages for visualization, statistics, and web services.

## 6. Unmeasured tools (document-based)

- **Deepchecks (AGPL)**: Not installed and not directly executed in this study. The AGPL license model may introduce different legal obligations in commercial/closed codebases. According to its published documentation, it provides a comprehensive data and model validation suite; includes train/test leakage, data integrity, and drift checks (`not measured (document)`).
- **NannyML (Apache-2.0)**: Not installed and not directly executed in this study. According to its published documentation, it focuses specifically on estimating model performance (CBPE method) and detecting drift timing in production environments, particularly in the face of delayed or missing labels (`not measured (document)`).

## 7. Why was it written from scratch?

ModelTrust Lab does not invent a new statistical method.
The tool is a focused diagnostic research prototype developed to avoid heavy dependencies (only `numpy` and `pandas`), to operate completely offline without telemetry and network access, to produce bit-for-bit deterministic manifests on the exact same input, and to provide an explicit assessability (`answered`/`partial`/`not_assessable`) contract on every check.
Its scope has been deliberately kept narrow.

## 8. Reproduction

The following steps can be used to reproduce the results in a temporary environment:

```powershell
# 1. Create a temporary venv and install Evidently
$ev = "$env:TEMP\mt_ev_venv"
python -m venv $ev
& "$ev\Scripts\python.exe" -m pip install --disable-pip-version-check "evidently==0.7.23"

# 2. Produce the data splits (to_csv uses \r\n line endings on Windows, hashes are platform-dependent)
$script = @'
import os, pandas as pd
df = pd.read_csv("examples/case_study/case_study.csv")
df_sorted = df.sort_values("ts").reset_index(drop=True)
cmp_dir = os.path.join(os.environ["TEMP"], "mt_cmp")
os.makedirs(cmp_dir, exist_ok=True)
df_sorted.iloc[:480].to_csv(os.path.join(cmp_dir, "reference.csv"), index=False)
df_sorted.iloc[480:].to_csv(os.path.join(cmp_dir, "current.csv"), index=False)
'@
python -c $script

# 3. Run the ModelTrust temporal report
python -m modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --split-mode temporal --shift --out-dir "$env:TEMP/mt_rep"

# 4. Run the Evidently report (New API canonical run)
$ev_script = @'
import os, json
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

temp = os.environ["TEMP"]
ref = pd.read_csv(os.path.join(temp, "mt_cmp", "reference.csv"))
cur = pd.read_csv(os.path.join(temp, "mt_cmp", "current.csv"))

rep = Report([DataDriftPreset()])
snap = rep.run(reference_data=ref, current_data=cur)

out_dir = os.path.join(temp, "mt_cmp_ev")
os.makedirs(out_dir, exist_ok=True)
snap.save_html(os.path.join(out_dir, "drift.html"))
data = snap.dict()
with open(os.path.join(out_dir, "drift.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
'@
$env:DO_NOT_TRACK = "1"
$env:ITERATIVE_DO_NOT_TRACK = "1"
& "$ev\Scripts\python.exe" -c $ev_script
```

## 9. Limitations

- **Scope**: The comparison was performed solely on a single synthetic dataset (`case_study.csv`) and temporal split scenario.
- **Version Dependency**: Findings apply to ModelTrust Lab `0.0.1.dev0` and Evidently `0.7.23` versions; testing methods or default thresholds may change in future releases.
- **Diagnostic Nature**: The obtained p-values or KS statistics are diagnostic indicators; they do not constitute an absolute guarantee of the model's overall reliability in a production environment.

- **Measurement version**: This document records the measurements made with the `0.0.1.dev0` development version installed at that time; `0.1.0` is the versioned state of the exact codebase for this document.
