# ModelTrust Question Assessability

## 1. Purpose and Rule
Each of the 10 diagnostic questions in the ModelTrust model card (`card.json`) output reaches the `answered` status in at least one documented input combination.
- **Rule:** There is a valid and supported data/parameter combination for each of the 10 questions.
- **Q10 Contract:** Question 10 ("How much can this report be trusted?") always returns `partial` by rule and according to system design. The model card is not a compliance certificate; it does not claim certainty or flawlessness (D-074, D-076, D-077).
- **Not Assessable Cases:** When an input or parameter is not provided or the number of rows is insufficient, the relevant question goes into the `not_assessable` state and is justified with a structured `reason_code`.

## 2. Question Assessability Matrix

| # | card.json question text (EXACT) | minimum command | status | evidence field | note |
|---|---|---|---|---|---|
| 1 | Missing or duplicate records? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | answered | profile: duplicate_rows=0, missing cells reported | Profile module is executed in every run. |
| 2 | Target leakage suspicion? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | answered | leakage.target_copy_exact=None, target_copy_near=None | Leakage module is executed when the target column is provided. |
| 3 | Train/test or group leakage? | `modeltrust card --input tests/fixtures/leak_clean.csv --target-col y --group-col grp --out-dir <DIR>` | answered | split.modes.random=performed | Split module operates when `--group-col` or `--time-col` is provided (D-081). |
| 4 | Split strategy difference? | `modeltrust card --input tests/fixtures/leak_clean.csv --target-col y --group-col grp --out-dir <DIR>` | answered | multiple split modes performed (2) | The comparison is completed when at least two split modes (random + group/temporal) are executed. |
| 5 | Which groups have higher error? | `modeltrust card --input tests/fixtures/eval_preds.csv --target-col y --pred-col pred --group-col grp --out-dir <DIR>` | answered | evaluation.group_errors performed | Group errors are analyzed when a prediction column and a group column (`--group-col`) are provided. |
| 6 | Distribution drift? | `modeltrust card --input tests/fixtures/shift_drift.csv --target-col y --time-col ts --out-dir <DIR>` | answered | shift.drift.feature_ks performed | Drift analysis is executed when time column (`--time-col`) and numerical feature columns are provided. |
| 7 | Out-of-distribution (OOD) data? | `modeltrust card --input tests/fixtures/leak_clean.csv --target-col y --group-col grp --out-dir <DIR>` | answered | shift.ood.feature_range performed | OOD check is performed when split data and numerical features are present. |
| 8 | Are uncertainty intervals calibrated? | `modeltrust card --input tests/fixtures/intervals_calibrated.csv --target-col y --lower-col lo --upper-col hi --nominal-coverage 0.9 --out-dir <DIR>` | answered | uncertainty.coverage=0.910 (Wilson [0.862, 0.942]), nominal=0.9, mean_width=3.290 | Coverage analysis is executed when lower/upper interval limits and nominal coverage level are provided. |
| 9 | Which checks could not be performed? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | answered | see not_assessable | Always returns `answered`; all unperformed checks are transferred to the `not_assessable` block. |
| 10 | How much can this report be trusted? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | partial | see limitations and not_assessable | Always returns `partial`; the report is evaluated within the scope of limitations and unperformed checks. |

## 3. reason_code Dictionary

The `reason_code` inside `card.json` is located in the `not_assessable` block and within the question `evidence` text, **not in the question object**.

### Observed (module, check, reason_code) Triplets
- `('leakage', 'index_like_feature', 'insufficient_rows')`
- `('leakage', 'preprocess.feature_target_near_deterministic', 'insufficient_rows')`
- `('leakage', 'preprocess.fit_scope', 'requires_pipeline_code')`
- `('leakage', 'preprocess.global_minmax_signature', 'insufficient_rows')`
- `('leakage', 'preprocess.global_standardization_signature', 'insufficient_rows')`
- `('leakage', 'preprocess.redundant_feature_pair', 'insufficient_rows')`
- `('leakage', 'subset_group_overlap', 'not_provided')`
- `('leakage', 'subset_row_overlap', 'not_provided')`
- `('leakage', 'subset_time_ranges', 'not_provided')`
- `('leakage', 'target_copy_exact', 'insufficient_rows')`
- `('leakage', 'target_copy_near', 'insufficient_rows')`
- `('shift', 'drift.feature_ks', 'not_provided')`
- `('shift', 'drift.target_ks', 'not_provided')`
- `('shift', 'ood.feature_range', 'insufficient_rows')`
- `('shift', 'ood.mahalanobis', 'insufficient_rows')`
- `('split', 'modes.group', 'not_provided')`
- `('split', 'modes.random', 'not_provided')`
- `('split', 'modes.temporal', 'not_provided')`

### Observed Codes and Meanings
- **`not_provided`**:
  - **Meaning:** The input flag / data column required for the relevant check or module was not provided by the user on the command line.
  - **Observed Cases:**
    - `split.modes.random`, `split.modes.group`, `split.modes.temporal`: When `--group-col` and `--time-col` are not specified (split module is skipped per D-081) or when the required time/group column for the relevant mode is not provided.
    - `leakage.subset_row_overlap`, `leakage.subset_group_overlap`, `leakage.subset_time_ranges`: Subset overlap checks are skipped when `--subset-col` is not provided.
    - `shift.drift.feature_ks`, `shift.drift.target_ks`: Distribution shift check is skipped when `--time-col` or relevant split columns are not specified.
- **`insufficient_rows`**:
  - **Meaning:** The number of rows in the dataset is below the minimum threshold (`thresholds`) required for the relevant statistical test or check to run.
  - **Observed Cases:**
    - `leakage.target_copy_exact`, `leakage.target_copy_near`, `leakage.index_like_feature`, `leakage.preprocess.global_standardization_signature`, `leakage.preprocess.global_minmax_signature`, `leakage.preprocess.feature_target_near_deterministic`, `leakage.preprocess.redundant_feature_pair`: The number of rows in the dataset is below the minimum check threshold (e.g., `MIN_ROWS_FOR_COPY_CHECK` etc.).
    - `shift.ood.feature_range`, `shift.ood.mahalanobis`: When split row count is insufficient for OOD checks.
- **`requires_pipeline_code`**:
  - **Meaning:** The check cannot be performed solely by looking at the data table; it requires examining the data preprocessing or model training code.
  - **Observed Cases:** The `leakage.preprocess.fit_scope` check requires training pipeline analysis, not just the dataset table.

## 4. Cases We Cannot Measure (Input Deficiencies and Rationale)

The code lines and stable check keys that cause specific input deficiencies to put which questions into the `not_assessable` state are fixed:

- **Question 3 (`Train/test or group leakage?`):**
  - When `--group-col` or `--time-col` is not provided, the split module is skipped and the question returns `not_assessable` (`split.modes.random not performed (reason_code=not_provided)`). Rationale: `src/modeltrust/card.py:78 (check: split.modes.random)`, `src/modeltrust/card.py:204 (check: split.modes)`, D-081.
- **Question 5 (`Which groups have higher error?`):**
  - Returns `not_assessable` when `--group-col` is not provided or group error analysis is not executed (`group_errors not performed`). Rationale: `src/modeltrust/card.py:100 (check: group_errors)`.
- **Question 6 (`Distribution drift?`):**
  - Returns `not_assessable` when `--time-col` is not provided or when no suitable numerical feature column is found for drift analysis (`shift.drift.feature_ks not performed`). Rationale: `src/modeltrust/card.py:111 (check: shift.drift)`.
- **Question 7 (`Out-of-distribution (OOD) data?`):**
  - Returns `not_assessable` when split data or numerical feature ranges cannot be calculated (`shift.ood.feature_range not performed`). Rationale: `src/modeltrust/card.py:117 (check: shift.ood)`.
- **Question 8 (`Are uncertainty intervals calibrated?`):**
  - Returns `not_assessable` when `--lower-col` and `--upper-col` limit columns are not provided (`uncertainty not performed`). Rationale: `src/modeltrust/card.py:151 (check: uncertainty)`.
- **Question 10 (`How much can this report be trusted?`):**
  - Always returns `partial` since the model card is not a certificate/compliance document and does not carry a claim of certainty (`see limitations and not_assessable`). Rationale: `src/modeltrust/card.py:159 (check: q10_by_rule)`, `docs/METHODS.md:201`, D-074, D-076, D-077.

## 5. Limitations
The assessability results and statuses in this matrix are verified only for the specified test fixtures and CLI parameter combinations. Check results and statuses may vary on external datasets with different schemas, data distributions, or missing column structures. ModelTrust diagnostic tools do not provide absolute assurance; they offer empirical diagnostic signals for data and model evaluation processes.
