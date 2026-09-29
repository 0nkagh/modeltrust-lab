# Methods and Threshold Rationale

## Thresholds (exact from code)
| Constant Name | Value |
| --- | --- |
| `MIN_ROWS_FOR_COPY_CHECK` | 5 |
| `MIN_PAIRS_FOR_CORRELATION` | 20 |
| `EXACT_COPY_EQUALITY_RATIO` | 1.0 |
| `NEAR_COPY_CORR_ABS_MIN` | 0.999 |
| `INDEX_LIKE_UNIQUE_RATIO_MIN` | 0.99 |
| `ATOL_NUMERIC_EQUALITY` | 1e-12 |
| `EXAMPLE_LIMIT` | 5 |
| `PREPROCESS_MIN_ROWS` | 10 |
| `PREPROCESS_NUMERIC_TOL` | 1e-9 |
| `FEATURE_TARGET_DET_MIN` | 0.999 |
| `REDUNDANT_PAIR_MIN` | 0.999 |

## Out of Scope
The following leakage types are deliberately excluded as they cannot be reliably audited via static inspection (CSV only):
- Leakage during Preprocessing and Feature Engineering
- Sampling bias
- Label noise
- Leakage resulting from database "join" operations
- Temporal causality violations (leakage from future to past)

## 1. Target Copy Suspicion
- **What it measures:** Whether any feature is exactly identical to the target variable.
- **How it measures:** It checks whether the absolute value of numerical differences between the target and the feature is less than or equal to the `ATOL_NUMERIC_EQUALITY` threshold (1e-12) (NaN and NaN are considered equal), or if string/categorical values are exactly equal.
- **Rationale for threshold:** The ratio threshold is `EXACT_COPY_EQUALITY_RATIO (=1.0)`, meaning the columns are expected to be exactly identical.

### Target Copy Near Suspicion
- **What it measures:** Whether any feature is similar to the target variable with a very high linear correlation.
- **How it measures:** It checks the absolute value of the Pearson correlation coefficient between the target variable and the feature.
- **Rationale for threshold:** If the absolute value of the correlation coefficient is `NEAR_COPY_CORR_ABS_MIN (=0.999)` and above, it is considered suspicious (to allow for minor rounding errors or a small number of outliers).

## 2. Index-Like Column
- **What it measures:** Whether there is an identity (ID) or index column that is almost unique for each row, rather than a signal the model can learn from.
- **How it measures:** It calculates the ratio of the number of unique elements in the column to the total number of rows. Additionally, it requires the column to be strictly of integer type and strictly monotonically increasing.
- **Rationale for threshold:** The threshold is 0.99. Columns containing more than 99% unique values, with integer types and monotonically increasing values, are considered suspicious as they cause the model to memorize (strict rules are added to reduce false positives).

## 3. Subset Row Overlap
- **What it measures:** Whether there are exactly identical rows among subsets like train, validation, or test.
- **How it measures:** A SHA-256 fingerprint is extracted over the concatenation of the string representations of all columns (excluding the subset column). It counts in pairs whether the same fingerprint is present in multiple subsets. In the output, overlap_count and its ratio to the size of the smaller set in that pair (overlap_ratio_of_smaller) are reported for each pair.
- **Rationale for threshold:** 0; the number of exactly overlapping rows in different subsets must be 0. At least 1 overlap is reported.

## 4. Subset Group Overlap
- **What it measures:** When a group column (e.g. patient_id) is used, whether rows belonging to the same group are distributed across multiple subsets.
- **How it measures:** The distribution of group identities according to subset values is examined. If a group ID is present in both the train and test sets, it is counted as an overlap.
- **Rationale for threshold:** 0; groups must be disjoint across subsets (strict split).

## 5. Temporal Subset Leakage Suspicion
- **What it measures:** When a temporal split is expected, whether some examples in the train set are more recent (later date) than the test set.
- **How it measures:** If the `subset_col` contains a time sequence assumption like train/test (it cannot verify this directly, but can issue a warning), it checks whether there is a clear overlap or reversal between the max/min timestamps of the subsets.
- **Rationale for threshold:** If the oldest (min) date of the test set is older than the newest (max) date of the Train set, a warning is triggered (overlap > 0).
 
## Preprocessing Signature Checks

| Check Name | Scope / Explanation | Threshold / Rule | Result / Behavior |
| --- | --- | --- | --- |
| `preprocess.fit_scope` | Pipeline fit scope (whether train-only fit is performed) | Cannot be detected from CSV | Always `not_assessable`, `reason_code="requires_pipeline_code"` |
| `preprocess.global_standardization_signature` | Standardization (z-score) signature over all data | `abs(mean) <= PREPROCESS_NUMERIC_TOL (1e-9)` and (`abs(std_ddof0 - 1) <= PREPROCESS_NUMERIC_TOL` or `abs(std_ddof1 - 1) <= PREPROCESS_NUMERIC_TOL`) (`n >= PREPROCESS_MIN_ROWS (10)`) | `fail` (diagnostic indicator) |
| `preprocess.global_minmax_signature` | Min-max scaling signature over all data | `min ≈ 0` and `max ≈ 1` (`atol=PREPROCESS_NUMERIC_TOL (1e-9)`, `n >= PREPROCESS_MIN_ROWS (10)`) | `fail` (diagnostic indicator) |
| `preprocess.feature_target_near_deterministic` | Near-deterministic linear relationship between feature and target | `abs(corr) >= FEATURE_TARGET_DET_MIN (0.999)` (`n >= MIN_PAIRS_FOR_CORRELATION (20)`) | `fail` (diagnostic indicator) |
| `preprocess.redundant_feature_pair` | Extremely high correlation between two numerical features | `abs(corr) >= REDUNDANT_PAIR_MIN (0.999)` (`n >= MIN_PAIRS_FOR_CORRELATION (20)`) | `pass` (for informational purposes), warning: `redundant_features` |
| `preprocess.suspicious_feature_name` | Suspicious feature name patterns (`target`, `_mean`, `zscore` etc.) | Pattern match (case-insensitive) | `pass` (never fail), warning: `suspicious_feature_names` |

These checks are signature-based; they do not prove that the pipeline code performed a train-only fit. What cannot be detected: features derived from the target, imputation using test statistics, feature selection performed with all data. → these appear as `not_assessable` in the report.

## Interpretation
All these audit outputs are **diagnostic indicators only**. A flagged rule does not mean there is definitely an error in the data (it could be a legitimate case). Similarly, the absence of a flag does not guarantee the absence of leakage or error.

## 6. Split Audit
- **What it measures:** Comparatively diagnoses the leakage and instability characteristics of splits created on the same data with random, group, and temporal strategies (deterministic).
- **What it does not measure:** Model-based comparisons (error margins - MAE/RMSE/R²), CV (Cross-Validation) loop, or statistical significance tests are out of the scope of this phase (they are PHASE 3 topics). Only split characteristics are examined.
- **Algorithms and Methods:**
  - **Rounding Rule:** The test set size is determined by `n_test = int(round(test_size * n))` and is clamped to be at least 1 and at most `n-1`.
  - **Random Split:** The method `numpy.random.default_rng(seed).permutation` is used. **Scope of reproducibility:** Only the same environment and the same numpy version (D-010); stability across numpy versions is not guaranteed.
  - **Group Split (Greedy):** Groups are sorted in descending order of row count, and ascending order of group name. Starting from the most crowded group, groups are sequentially assigned to the test set until the total number of rows in the test set reaches the `n_test` target. (If the `n_test` limit is exceeded with the last added group, that group is also included in the test; therefore, the actual `test_fraction` may not always be exactly identical to `test_size`). All remaining groups are assigned to the train set. It is a deterministic approach.
  - **Temporal Split:** Data is split by sorting according to the time column and then the original row index.

## 7. Report Generation
- **Scope and Content:** Produces a canonical JSON containing the `tool`, `run_metadata`, `environment`, `input`, `column_spec`, `schema`, `profile`, `leakage`, and optional `split` blocks. When the `--evaluate` argument is provided (it is off by default), a top-level `evaluation` block and a `## 9. Model evaluation` section in the Markdown report are added (the behavior is exactly identical to the `evaluate` command). When the `--shift` argument is provided (it is off by default), a top-level `shift` block is added to the JSON; in Markdown, the `## 6. Split comparison` header expands to `## 6. Split comparison and distribution shift` and a `### Distribution shift & OOD` table (`| Check | Result | Detail |`) is added. When the `--card` flag is provided, `card.json` and `card.md` files are also produced in the same directory, over the same read (`prov`). These flags are independent and can be used together.
- **Markdown Projection:** The `report.md` file, created alongside JSON, is a direct projection of the JSON output. No additional information not present in the JSON structure is added to Markdown.
- **Determinism:** Lists and tables in the Markdown report are kept in a deterministic order, decimals are formatted, and controls that are `not_assessable` are not skipped, but reported in a special section (`What could NOT be assessed`).
- **Interpretation Language:** The report does not contain definitive conclusive sentences stating that the model is safe or that there is no leakage (such as "leakage-proof", "safe", "fully reliable", etc.). It only contains warnings indicating that it is a diagnostic indicator.

## 8. Evaluation
- **Models (Baseline):**
  - **mean_baseline:** Returns the arithmetic mean of the target variable in the train set as the prediction for all test examples.
  - **ols_baseline:** Applies multiple linear regression with Ordinary Least Squares (OLS) over all numerical features (by adding a constant term).
  - **supplied_predictions:** If the user provides a ready-made prediction column from the outside (`--pred-col`), model training is skipped and this column is directly used for test/evaluation.
- **Metrics and Methods:**
  - **MAE (Mean Absolute Error):** The mean of the absolute values of the errors. `mean(|y - y_pred|)`
  - **RMSE (Root Mean Square Error):** The square root of the mean of the squares of the errors. `sqrt(mean((y - y_pred)^2))`
  - **R² (R-squared):** The ratio of variance explained by the model. Calculated with the formula `1 - (SS_res / SS_tot)`. If SS_tot is zero, a `not_assessable` status is returned and a `zero_variance_target` warning is issued.
- **Missing Data (NaN) Behavior:**
  - Test rows that are NaN in the target variable or in the provided prediction (if `supplied_predictions` is used) are not included in scoring (n_scored).
  - During OLS training, rows that are NaN in the target or any feature are dropped from the training set.
- **Cross-Validation (CV):** K-fold cross validation (CV) modules (random, group, temporal) are supported. Module-specific splitting logics (e.g., greedy group allocation that does not break group integrity) are applied. If the data in the test set is too small (`CV_MIN_FOLD_SIZE < 3`), the fold is not evaluated (`not_assessable`).
- **Group Error:** In group mode (`--split-mode group`), test errors (n, MAE, RMSE, mean residual) are independently calculated and listed for each group present in the test set. Groups are ranked according to MAE value and the worst performing groups (`TOP_WORST_GROUPS = 3`) are identified. Groups that do not have enough examples (`n < 5`) are excluded from this ranking.
  - **Definition of `coverage_ratio`:** Calculated as `coverage_ratio = n_rows_evaluated / n_rows_scored`. It expresses the ratio of valid rows that satisfy the minimum group size threshold (`MIN_GROUP_ROWS_FOR_ERROR = 5`) and are included in the group error ranking, out of the total scored rows. Numerical fields that cannot be evaluated (not_assessable) are not shown as 0.000000 in the report; they are shown with N/A and reason_code (e.g. `N/A (not_provided)`).

### 8.x Thresholds
| Constant Name | Value | Explanation |
| --- | --- | --- |
| `MIN_ROWS_FOR_METRICS` | 10 | Minimum number of rows required to calculate metrics |
| `MIN_GROUP_ROWS_FOR_ERROR` | 5 | Minimum number of rows required to include a group in the error ranking (worst_by_mae) |
| `TOP_WORST_GROUPS` | 3 | Maximum number of groups to list with the highest MAE value |
| `CV_MIN_FOLD_SIZE` | 3 | Minimum number of test rows required to evaluate a CV fold |
| `MIN_ROWS_FOR_COPY_CHECK` | 5 | Minimum number of rows for target copy suspicion audit |
| `MIN_ROWS_FOR_INDEX_CHECK` | 10 | Minimum number of rows for ID-like feature audit |
| `PREPROCESS_MIN_ROWS` | 10 | Minimum number of rows for preprocessing signature audits |
| `MIN_PAIRS_FOR_CORRELATION` | 20 | Minimum number of rows for correlation and deterministic feature-target relationship |
| `MIN_ROWS_FOR_INTERVAL` | 20 | Minimum number of rows for uncertainty calculation |
| `WILSON_Z` | 1.96 | Wilson score interval z-value (95% confidence) |
| `COVERAGE_GAP_TOL` | 0.05 | Tolerable gap between nominal coverage and empirical coverage |
| `GROUP_COVERAGE_RANGE_MAX` | 0.30 | Maximum coverage ratio difference between groups (uniformity tolerance) |
| `WIDTH_BINS` | 4 | Interval width histogram breakdown (number of bins) |

### 8.y Uncertainty
If the `--lower-col` and `--upper-col` arguments are provided together to the `evaluate` (or `report --evaluate`) command, the model's predictive uncertainty performance is measured and an `uncertainty` section is added inside the evaluation block.

- **Coverage:** The ratio of the target variable remaining within the lower and upper bounds (`[lower, upper]`) in the test set. It is calculated empirically (observed coverage).
- **Wilson Score:** The 95% confidence interval of the coverage ratio is estimated with $z=1.96$ (Wilson Score Interval) for small sample stability.
- **Group Coverage:** If the data is split into groups, the coverage ratio of each group is also reported separately. Using the `MAX_GROUP_COVERAGE_GAP (0.10)` threshold, it is checked whether the maximum coverage difference between groups (max - min) is too high (`interval.group_coverage_uniformity`).
- **Nominal Coverage Comparison:** If the user provides `--nominal-coverage` (e.g. 0.95), it is checked whether the lower bound of the empirical coverage reaches this value (`interval.coverage_gap`). If it does not reach it, a `non_nominal_coverage` warning is issued.

**Interpretation (What it does not measure):** 
Uncertainty indicators operate under the "single split, no distribution-free guarantee" scope. The calculated ratios belong only to the obtained test set (single split), they do not carry a distribution-free statistical validity (e.g., no Conformal Prediction guarantee is provided). The fact that the coverage ratio is close to the nominal value does not mean that the model intervals are "fully reliable" or "production-ready", it is only a diagnostic indicator.

*Radius/error scale note: In `intervals_*` synthetic data (fixture), the target variable's noise standard deviation ($\sigma=1.0$) is taken as a baseline, and the radius width in confidence interval calculations is directly related to this noise scale (e.g. for `90%` coverage the ideal radius is approximately `1.645 * 1.0`). Fixtures are directly produced with this principle and tests are tied to the measured empirical coverage ratios with a tolerance margin.*

### 8.z What it does not measure
This block does not measure the overall performance of the user's model. When `--pred-col` is provided, **all rows** are scored, there is no holdout. Hyperparameter search, classification metrics, and model calibration guarantees are out of scope. OLS and mean baselines are only internal tool references.

## 9. Distribution shift and OOD (Diagnostic indicator)

The ModelTrust Lab `shift` module (`src/modeltrust/audit/shift.py`) diagnoses data distribution differences and Out-of-Distribution (OOD) examples between the train and test splits using statistical and geometric indicators:

- **Audits:**
  - **`ood.feature_range`:** Calculates the minimum and maximum (`[train_min, train_max]`) value limits of numerical features in the train set. It measures the ratio of values falling outside these limits in the test set (`outside_ratio`) and the ratio of test rows where at least one feature falls outside the limits (`row_outside_ratio`). If `max_feature_outside_ratio >= OOD_FEATURE_OUTSIDE_RATIO_MIN (0.10)`, it is considered a `fail`.
  - **`ood.mahalanobis`:** Calculates the mean vector $\mu$ and covariance matrix $\Sigma$ over the train set (`ddof=1`, Moore-Penrose pseudo-inverse $\Sigma^+$ for singular matrices). Determines the Mahalanobis distance $d(x) = \sqrt{(x-\mu)^T \Sigma^+ (x-\mu)}$ median ratio (`ratio = median_test / median_train`) of test and train rows. If `ratio >= OOD_MAHALANOBIS_RATIO_MIN (2.0)`, it is considered a `fail`.
  - **`drift.feature_ks`:** Calculates the two-sample Kolmogorov-Smirnov ($D$) statistic between numerical features of the train and test sets with the formula $D = \max |F_{\text{train}}(x) - F_{\text{test}}(x)|$. If the highest feature KS value `max_ks_stat >= DRIFT_KS_STAT_MIN (0.25)`, it is considered a `fail`.
  - **`drift.target_ks`:** Calculates the Kolmogorov-Smirnov ($D$) statistic between the target variables of the train and test sets. If `ks_stat >= DRIFT_KS_STAT_MIN (0.25)`, it is considered a `fail`.
- **Constant Column Policy:** Constant columns with zero variance (`std == 0`) in the train set are excluded from the shift analysis and listed with a `constant_features_excluded` warning.
- **Time Column Condition:** Since drift checks (`drift.feature_ks`, `drift.target_ks`) are meaningful on a time series axis, if `--time-col` is not provided, drift checks are marked as `not_assessable` (`not_provided`); OOD checks can still be executed on random or group splits.

### 9.x Thresholds
| Constant Name | Value | Explanation |
| --- | --- | --- |
| `SHIFT_MIN_ROWS` | 20 | Minimum number of rows required in the train set for shift analysis |
| `CV_MIN_FOLD_SIZE` | 3 | Minimum number of rows required in the test set for shift analysis |
| `OOD_FEATURE_OUTSIDE_RATIO_MIN` | 0.10 | OOD range exceedance fail threshold for a feature |
| `OOD_MAHALANOBIS_RATIO_MIN` | 2.0 | Mahalanobis median distance ratio fail threshold |
| `DRIFT_KS_STAT_MIN` | 0.25 | Kolmogorov-Smirnov drift statistic fail threshold |

### 9.y What it does not measure (Honesty framing and Limitations)
- **No p-value and Statistical Significance:** The module does not calculate parametric tests or p-values (there is no scipy dependency). The reported values are empirical distances, not definitive hypothesis test results.
- **Heuristic Thresholds:** The determined thresholds (0.10, 2.0, 0.25) are rule-based diagnostic indicators; they do not represent an absolute accept/reject boundary.
- **No Causality and Failure Guarantee:** Providing an OOD or drift flag does not exclude the possibility that a data originates from a legitimate regime change; similarly, the absence of a flag does not mean that there is definitely no distribution shift ("Absence of a flag does not establish absence of shift").
- **No Claim of Model Crash:** Finding out-of-distribution examples or a high KS statistic does not guarantee that the user's model will definitely produce erroneous predictions on these examples.

### 9.z `shift` Command Contract (CLI Rules)
- **`--target-col` is required** (for the `shift` command and `report --shift`). If missing, it returns `exit 2` (`Error: --target-col is required`). Rationale: The `drift.target_ks` check is calculated over the target column; if there is no column, the check becomes meaningless.
- **`--split-mode group`** requires **`--group-col`**; if missing it returns `exit 4` (`Error: --split-mode group requires --group-col`).
- **`--split-mode temporal`** requires **`--time-col`**; if missing it returns `exit 4` (`Error: --split-mode temporal requires --time-col`).
- **If `--time-col` is missing**, drift checks (`drift.feature_ks`, `drift.target_ks`) are marked as `not_assessable (not_provided)`; OOD checks (`ood.feature_range`, `ood.mahalanobis`) continue to operate.
- **`--split-mode`/`--test-size`** can be used together with **`report --shift`**; these flags now require the presence of `--evaluate` or `--shift`, not just `--evaluate`. If neither is present, it returns `exit 2` (`Error: {flag} requires --evaluate or --shift`).



## 11. Model Card (Summary Report)

The `modeltrust card` command produces a card containing the data provenance, tested scenarios, measured metrics, and the diagnostic summary of unperformed audits. 

### 11.1 Card Sections
1. **Scope & disclaimer:** It is stated that the card is not a certification and does not offer performance guarantees.
2. **Data provenance:** Contains the input data path, row/column counts, data hash, used version and seed information.
3. **Questions answered:** The table of answers (status and evidence) given to 10 critical questions based on the operability status of the modules. The split module only works when `--group-col` or `--time-col` is provided; otherwise, checks are skipped and recorded with a reason_code.
4. **Checks summary:** The count of performed, failed, and not_assessable audits on a module basis (e.g., `leakage`). When a module is skipped (e.g., split is not run), the module is recorded in the summary as total check count, performed=0, fail=0, and not_assessable.
5. **Not assessable:** The list of unperformed audits and their reasons (reason_code). Checks of skipped modules are listed here with the relevant reason_code (e.g. `not_provided`).
6. **Metrics:** The model's measured error metrics, cross-validation (CV) results, and uncertainty interval coverage if any.
7. **Thresholds:** The used configuration and threshold values (e.g., `OOD_MAHALANOBIS_RATIO_MIN`).
8. **Limitations:** Limitations of the tool (only tabular regression, no p-value, etc.) and warnings.
9. **Reproduce:** The CLI command required to reproduce the report exactly with the same seed and settings. (Can be produced with the standalone `card` command or embedded in the report by providing the `--card` flag to the `report` command.)

### 11.2 "Questions Answered" Status Rules
The card uses the following strict rules (deterministic) to determine the evaluation status:

| # | Question | `answered` condition | Otherwise |
|---|---|---|---|
| 1 | Missing or duplicate records? | profile performed | — |
| 2 | Target leakage suspicion? | `leakage.target_copy_exact` **or** `target_copy_near` performed | `not_assessable` |
| 3 | Train/test or group leakage? | `split.modes.random` performed | `not_assessable` |
| 4 | Split strategy difference? | ≥2 of random/group/temporal performed | `partial` |
| 5 | Errors in which groups? | `evaluation.group_errors.status == "performed"` | `not_assessable` |
| 6 | Drift? | `shift.drift.feature_ks.status == "performed"` | `not_assessable` |
| 7 | Out-of-distribution (OOD) data? | `shift.ood.feature_range.status == "performed"` | `not_assessable` |
| 8 | Uncertainty calibrated? | `uncertainty.status == "performed"` | `not_assessable` |
| 9 | Which checks could not be assessed? | always `answered` | — |
| 10 | How much can the report be trusted? | always `partial` | — |

### 11.3 What it does not claim (Limitations)
A model card is **not a certification**. It does not claim that any model is "production-ready", "compliant", or carries a performance/reliability guarantee. It is only a diagnostic summary produced with the specified dataset and the executed arguments.

### 11.4 `n_scored` Scope — Supplied Predictions Mode

When `--pred-col` is provided, the CLI assumes that the predictions have been calculated externally by the user. In this mode:

- **Split is not applied.** All provided rows (that are not NaN) are included in the metric.
- The `n_scored (all rows provided)` column in the metric table reflects this fact: the value is the number of non-NaN rows in the provided dataset; it is not the size of a test split.
- The `--split-mode` and `--test-size` arguments do not produce train/test split metrics in this mode. The split module only operates when `--group-col` or `--time-col` is provided; otherwise, split is skipped and recorded in the checks summary and not_assessable list with reason_code=not_provided.

### 11.5 `n_scored` Dynamic Scope Rule

The `n_scored` column header in the metrics table is determined dynamically according to the model rows (`scored_scope_label` helper function — single source of truth, defined in `report.py`, shared by card and report):

| n_train status | Header |
|---|---|
| `n_train == 0` on all rows | `n_scored (all rows provided)` |
| `n_train > 0` on all rows | `n_scored (split)` |
| Mixed set (both 0 and >0) | `n_scored (scope varies)` + warnings note |

`n_train == 0`: supplied_predictions mode; split is not applied, score is on all rows. `n_train > 0`: internal model training; score is only on the test split. In the card output, if the model list is empty, the metrics table is not printed; the label is not observed. In the report output, if the evaluation block is present but the model list is empty, the table header is printed and per D-078 the label becomes 'n_scored (all rows provided)'.

### 11.6 Embedding Card into Report (`--card`)
If the `--card` argument is provided to the `report` command, `card.json` and `card.md` files are also produced in the same directory using the data loaded into memory once and the generated `prov` object to create the report. During this process, data is not re-read, and modules are not re-run. Block equality with the card is expected only within the same module set (D-085); consistency is tested with the test_report_card_consistency_with_card_command test. The `reproduce_command` field in the card output reflects the actual command that produced the card (the `report --card` form if produced from within the report).

## 12. Reproducibility Manifest

When the `--manifest` flag is provided, the `card` command produces a reproducibility manifest file (`manifest.json`) alongside the card outputs (`manifest_schema_version = 1`).

### 12.1 Manifest Fields
- **`manifest_schema_version`:** Schema version (integer, 1).
- **`tool`:** The name of the tool (`name`) and its version (`version`).
- **`command`:** The reproduction CLI command listed in §9 Reproduce of the card (from single source; includes `--out-dir` path).
- **`input`:** The input file path provided by the user (`path`), the SHA-256 byte digest of the input file (`sha256`), total row count (`rows`), and column count (`columns`).
- **`environment`:** Operating environment information (`python` version, `pandas` version, `numpy` version, `platform`).
- **`seed`:** Random number generator seed (`seed`).
- **`git`:** Local git information (`commit`: 40-character hex commit hash, `dirty`: boolean value indicating whether there are uncommitted changes in the working tree).
- **`config`:** Used threshold values (`thresholds`).
- **`outputs`:** SHA-256 byte digests of the produced card files (`card_json_sha256`, `card_md_sha256`).
- **`warnings`:** Warning list.

### 12.2 Determinism and Timestamp Rule
- The manifest never contains a date or timestamp under any circumstances.
- `manifest.json` produced in consecutive runs with the exact same input, seed, environment, and same out-dir is byte-for-byte identical (hash-identical determinism; since the command field will change when a different out-dir is provided, the manifest hash will differ).

### 12.3 Behavior if Git is Inaccessible
- When Git is not installed, the `.git` directory is not found, or `git` commands fail, the run is not interrupted.
- The `git` field is populated as follows: `{"commit": null, "dirty": null, "reason_code": "not_available"}`.

### 12.4 Out of Scope Items
- `manifest.json` is only within the scope of the `modeltrust card` command; manifest generation for `report`, `evaluate`, and `shift` commands is out of scope.
- Directory scanning, multi-fixture bulk hashing, and cryptographic signing are out of the scope of this release.
