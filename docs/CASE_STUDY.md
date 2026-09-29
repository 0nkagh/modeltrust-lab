# Case Study: Diagnostic Audit on Deliberately Corrupted Synthetic Data

## 1. Purpose and Honesty Framing

This is not a benchmark.
Flaws have been deliberately injected into the data; detection success cannot be generalized to real-world distributions.
Results apply only to this dataset, this tool version, and these commands.

The purpose of this study is to document, with transparent and concrete evidence, the behavior of ModelTrust Lab diagnostic modules (`inspect`, `profile`, `leakage`, `split`, `evaluate`, `shift`, `card`, `report`) against known data and model flaws, which flaws they can detect, and which flaws they leave out of scope.

## 2. Dataset Metadata

- **File path**: `examples/case_study/case_study.csv`
- **Row count**: 600 data rows (601 rows including header)
- **Column count**: 12 columns (`row_id, ts, site, region, x1, x2, x3, y, pred, lo, hi, y_proxy`)
- **RNG Seed**: `20260928`
- **Generator command**: `python examples/case_study/generate_case_study.py --out-dir examples/case_study`
- **CSV SHA-256**: `9587b66886a942ee9e9589fe65f000406f6f9f40f41ba7e7bf0b5e0cf9e942da`
- **Timestamp (`ts`) format**: `YYYY-MM-DD` (ISO-8601 calendar day, between `2024-01-01` and `2025-08-16`)
- **Numerical format**: Decimal point, `float_format="%.6f"`, UTF-8 encoding, LF line ending.

## 3. Injected Flaws

| # | Flaw Type | How it was Injected (Code / Scale) | Scale Reference |
|---|---|---|---|
| D1 | **Duplicate rows** | Exact copy of 6 rows with all columns (rows 10, 20, 30, 40, 50, 60 copied and appended to the end) | `split_dupes.csv` / `profile_dirty.csv` |
| D2 | **Missing cells** | 12 cells in the `x3` column were set to `NaN` | `profile_dirty.csv` |
| D3 | **Target near copy** | `y_proxy = 0.98 * y + N(0, 0.005)` (correlation with target > 0.999) | `leak_nearcopy.csv` |
| D4 | **High cardinality id** | `row_id = 1..N` (unique integer identity) | `high_card_id.csv` |
| D5 | **Group leakage** | `site` ∈ {S1..S10}; constant `y` shift for each site (site effect); in random split, groups fall on both sides | `leak_group_overlap.csv`, `split_groups.csv` |
| D6 | **Distribution shift** | In the last 30% of rows (time-ordered) `x2 += 2.0` and noise scale 1.0 → 1.5; `ts` increasing | `shift_drift.csv` |
| D7 | **Overly narrow intervals** | `lo = pred - 0.2`, `hi = pred + 0.2`; interval width is narrower than the model residual scale | `intervals_overconfident.csv` |
| D8 | **Regional error concentration** | `region` ∈ {A, B, C}; true error in region B is ~3× higher | `eval_preds.csv` |
| D9 | **Label noise** | Large deviation (±15..25) added to `y` value in random 4% of rows | — (the tool does not perform this check; no detection) |

## 4. Observed Detections

### D1 — Duplicate Rows
- **Relevant Question**: Q1 ("Missing or duplicate records?")
- **Executed Command**: `modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --pred-col pred --group-col site --evaluate --shift --card --out-dir $t/cs_report`
- **Status**: `answered` (detected)
- **Raw Evidence Excerpt**:
  ```json
  "duplicate_rows": {
    "duplicate_row_ratio": 0.01,
    "exact_duplicate_count": 6,
    "example_row_indices": [594, 595, 596, 597, 598],
    "null_equals_null": true
  }
  ```
  Also observed as `warnings: ["duplicate_rows_cross_split"]` in the `split` command and `row_overlap_count: 3` in `random` mode.
- **Interpretation**: The tool detected 6 duplicate rows with all columns identical during the profiling phase and produced a cross-leakage warning in the split audit.

### D2 — Missing Cells
- **Relevant Question**: Q1 ("Missing or duplicate records?")
- **Executed Command**: `modeltrust report` (and `card`)
- **Status**: `answered` (detected)
- **Raw Evidence Excerpt**:
  ```json
  {
    "name": "x3",
    "role": "feature",
    "observed_dtype": "float64",
    "is_numeric": true,
    "missing_count": 12,
    "missing_ratio": 0.02
  }
  ```
- **Interpretation**: The 12 missing values in the `x3` column (ratio: 2.0%) were reported as exact count and ratio in the profile summary.

### D3 — Target Near Copy
- **Relevant Question**: Q2 ("Target leakage or future leakage?")
- **Executed Command**: `modeltrust leakage --input examples/case_study/case_study.csv --target-col y --group-col site`
- **Status**: `answered` (check: `fail`, detected)
- **Raw Evidence Excerpt**:
  ```json
  {
    "name": "target_copy_near",
    "status": "performed",
    "result": "fail",
    "detail": "Target near copy found",
    "evidence": [
      {
        "abs_correlation": 1.0,
        "column": "y_proxy",
        "equality_ratio": 0.0
      }
    ]
  }
  ```
- **Interpretation**: Since `y_proxy` has an absolute correlation with the target above the 0.999 threshold, it was flagged as a diagnostic indicator of leakage by `target_copy_near`.

### D4 — High Cardinality Identity
- **Relevant Question**: Q2 ("Target leakage or future leakage?")
- **Executed Command**: `modeltrust leakage` / `report`
- **Status**: `performed` (check: `pass`, **not detected**)
- **Raw Evidence Excerpt**:
  ```json
  {
    "name": "index_like_feature",
    "status": "performed",
    "result": "pass",
    "detail": "",
    "evidence": null
  }
  ```
- **Interpretation**: The `row_id` column is an integer; however, due to the duplicate rows added by the D1 flaw, not all consecutive differences in the series remained strictly positive (`diffs > 0`), therefore `index_like_feature` was not triggered because the strict monotonicity condition could not be satisfied. The specification was strictly followed, no artificial correction was made to the data.

### D5 — Group Leakage
- **Relevant Question**: Q3 ("Train/test split strategy and group/time leakage?")
- **Executed Command**: `modeltrust split --input examples/case_study/case_study.csv --target-col y --group-col site --time-col ts`
- **Status**: `answered` (`fail` in random split, `pass` in group split)
- **Raw Evidence Excerpt**:
  ```json
  "random": {
    "group_overlap": {
      "count": 10,
      "groups": ["S1", "S10", "S2", "S3", "S4"],
      "ratio_of_smaller": 1.0,
      "status": "performed"
    }
  },
  "group": {
    "group_overlap": {
      "count": 0,
      "groups": [],
      "ratio_of_smaller": 0.0,
      "status": "performed"
    }
  }
  ```
- **Interpretation**: In the `random` mode, all 10 sites leaked between the train and test sets (`ratio_of_smaller: 1.0`), whereas in the `group` mode, the strict disjointness of the groups (`count: 0`) was verified.

### D6 — Distribution Shift
- **Relevant Question**: Q6 ("Distribution drift?") and Q7 ("Out-of-distribution (OOD) data?")
- **Executed Commands**:
  - Default (random split): `modeltrust shift --input examples/case_study/case_study.csv --target-col y --time-col ts`
  - Temporal split: `modeltrust report --input ... --target-col y --time-col ts --split-mode temporal --shift --out-dir $t/t19r1_temporal`
- **Status**:
  - In default (random) mode: `pass` (below threshold, not detected)
  - In temporal mode: `fail` (detected)
- **Raw Evidence Excerpt (default mode)**:
  ```json
  {
    "name": "drift.feature_ks",
    "status": "performed",
    "result": "pass",
    "detail": "Diagnostic indicator: max KS stat=0.114583 across features (heuristic threshold 0.25)"
  },
  {
    "name": "ood.feature_range",
    "status": "performed",
    "result": "pass",
    "detail": "Diagnostic indicator: 0.008333 max outside ratio (heuristic threshold 0.10)"
  }
  ```
- **Raw Evidence Excerpt (temporal mode)**:
  ```json
  {
    "name": "drift.feature_ks",
    "status": "performed",
    "result": "fail",
    "detail": "Diagnostic indicator: max KS stat=1.000000 across features (heuristic threshold 0.25)"
  },
  {
    "name": "drift.target_ks",
    "status": "performed",
    "result": "fail",
    "detail": "Diagnostic indicator: target KS stat=0.331250 (heuristic threshold 0.25)"
  },
  {
    "name": "ood.feature_range",
    "status": "performed",
    "result": "fail",
    "detail": "Diagnostic indicator: 1.000000 max outside ratio (heuristic threshold 0.10)"
  }
  ```
  In temporal mode, the highest KS statistic is 0.65 in the `x2` column (excluding `row_id`, which is already an integer identity); target KS is 0.331250; OOD has one row each outside the training range in `x1` and `x2` excluding `row_id`.
- **Interpretation**: In the default random split, the shift in the last 30% of time was equally distributed to the train and test subsets, the KS remained at the 0.1146 level and did not exceed the 0.25 threshold. In the temporal split, since train=first 80% and test=last 20%, the `x2 += 2.0` shift was directly caught and the `drift.feature_ks`, `drift.target_ks`, `ood.feature_range` checks returned fail. This shows that the split mode directly affects the detection capacity (I-051, D-095).

### D7 — Overly Narrow Intervals
- **Relevant Question**: Q8 ("Uncertainty intervals?")
- **Executed Command**: `modeltrust evaluate --input examples/case_study/case_study.csv --target-col y --lower-col lo --upper-col hi --nominal-coverage 0.9`
- **Status**: `performed` (check: `fail`, detected)
- **Raw Evidence Excerpt**:
  ```json
  "uncertainty": {
    "coverage": 0.191667,
    "coverage_gap": -0.708333,
    "nominal_coverage": 0.9,
    "status": "performed",
    "warnings": ["non_nominal_coverage"]
  }
  ```
  And check result: `"name": "interval.nominal_gap", "result": "fail", "detail": "gap=-0.708333"`.
- **Interpretation**: The realized coverage was measured as 19.17% against 90% nominal coverage, and since the gap tolerance (0.05) was exceeded, the interval reliability was directly reported as a fail.

### D8 — Regional Error Concentration
- **Relevant Question**: Q5 ("Subpopulation or fairness disparities?")
- **Executed Commands**:
  - First run: `modeltrust report ... --group-col site --evaluate` (site level)
  - Targeted run: `modeltrust report --input ... --target-col y --pred-col pred --group-col region --evaluate --out-dir $t/t19r1_region`
- **Status**:
  - `--group-col site`: `answered` (`worst_by_mae: ["S5", "S8", "S4"]` at site level)
  - `--group-col region`: `answered` (regional disparity detected)
- **Raw Evidence Excerpt (region run)**:
  ```json
  "group_errors": {
    "groups": [
      {"group": "A", "mae": 0.46471, "mean_residual": -0.007916, "n": 200, "rmse": 0.568517},
      {"group": "B", "mae": 1.351882, "mean_residual": 0.194973, "n": 200, "rmse": 1.69947},
      {"group": "C", "mae": 0.497436, "mean_residual": -0.007101, "n": 200, "rmse": 0.6057}
    ],
    "worst_by_mae": ["B", "C", "A"]
  }
  ```
  Overall model: `supplied_predictions MAE: 0.771342, RMSE: 1.092136, n=600`.
- **Interpretation**: The MAE (1.352) in region B is approximately 3 times that of regions A (0.465) and C (0.497); the RMSE ratio is also similar (1.699 vs 0.569/0.606). When `--group-col region` was provided, the tool directly reported the regional error concentration. Since `--group-col site` was used in the first run, the disparity at the region level was not observed; whatever input parameter is provided, the tool only audits that (I-051, D-095).

### D9 — Label Noise
- **Relevant Question**: —
- **Executed Command**: All commands
- **Status**: **Not detected / Check not available**
- **Interpretation**: Within the ModelTrust Lab v1 diagnostic scope, there is no independent diagnostic module that directly detects ground-truth label corruption in raw tables. This is deliberately out of scope by design and is noted as a finding.

## 4.1. Impact of Mode and Group Column Selection

The table below shows how different split mode and group column selections change the detection results on the same dataset.

| Command | Measurement | Result |
|---|---|---|
| `shift --split-mode random` (default) | `drift.feature_ks` max KS=0.114583, threshold 0.25 | `pass` |
| `shift --split-mode random` (default) | `ood.feature_range` max outside=0.008333, threshold 0.10 | `pass` |
| `report --split-mode temporal --shift` | `drift.feature_ks` max KS=1.000000, threshold 0.25 | `fail` |
| `report --split-mode temporal --shift` | `drift.target_ks` KS=0.331250, threshold 0.25 | `fail` |
| `report --split-mode temporal --shift` | `ood.feature_range` max outside=1.000000, threshold 0.10 | `fail` |
| `report --group-col site --evaluate` | `worst_by_mae` | `["S5", "S8", "S4"]` |
| `report --group-col region --evaluate` | region B MAE=1.352, A=0.465, C=0.497 | `worst_by_mae: ["B", "C", "A"]` |

This table shows that the split mode and group column selection directly affect the detection capacity: the time-local shift targeted by the D6 flaw is only caught in temporal mode; the regional error concentration of D8 is only seen with `--group-col region`.

## 5. What is Not Detected and Not Assessable

1. **D9 (Label Noise)**: As explained above, the tool does not have a module to perform this check (`check not available`).
2. **D4 (High Cardinality ID)**: `row_id` is an integer, but since strict monotonicity is broken due to the duplicates introduced by D1, `index_like_feature` was not triggered. Code reference: [`leakage.py:170`](file:///c:/Users/agah/Documents/modeltrust-lab/src/modeltrust/audit/leakage.py#L170) — `if is_int and unique_ratio >= INDEX_LIKE_UNIQUE_RATIO_MIN and is_monotonic:`.
3. **D6 (Distribution Shift, default mode)**: Since default random split is used when `--split-mode temporal` is not provided in the `shift` call, the KS threshold was not exceeded. In temporal mode, three checks returned fail (see §4, D6 and §4.1).
4. **Not Assessable Checks (`not_assessable`)**:
   - `leakage.preprocess.fit_scope` (`requires_pipeline_code`): It cannot be understood from a CSV table whether data preprocessing steps (scaler, encoder) are fitted only on the training set. Pipeline code is strictly required.
   - `leakage.subset_row_overlap`, `subset_group_overlap`, `subset_time_ranges` (`not_provided`): A distinct `subset` column (e.g., `train`/`test`) was not provided in the input table.
   - `shift.drift.feature_ks` (`not_provided`) in `card` single run (C1): Time series drift cannot be evaluated when the `--time-col` parameter is not entered in the `card` command.

## 6. Coverage Inventory

The raw audit summary (`checks_summary`) taken from inside `card.json` in the run output:

```json
[
  {"module": "leakage", "total": 12, "performed": 8, "fail": 2, "not_assessable": 4},
  {"module": "split", "total": 3, "performed": 3, "fail": 0, "not_assessable": 0},
  {"module": "shift", "total": 4, "performed": 4, "fail": 0, "not_assessable": 0}
]
```

This inventory clearly demonstrates what the tool actually evaluated, what it flagged as fail, and what it could not evaluate due to missing parameters or pipeline code requirements.

Full JSON output of the checks returning fail in the leakage module:

```json
{
  "name": "target_copy_near",
  "status": "performed",
  "result": "fail",
  "detail": "Target near copy found",
  "evidence": [{"abs_correlation": 1.0, "column": "y_proxy", "equality_ratio": 0.0}]
}
```

```json
{
  "name": "preprocess.feature_target_near_deterministic",
  "status": "performed",
  "result": "fail",
  "detail": "Near-deterministic relationship between feature and target; this is a diagnostic indicator, not proof.",
  "evidence": [{"abs_correlation": 1.0, "column": "y_proxy", "n": 600}]
}
```

## 7. Limitations

- **Lack of generalizability**: The detections and failures obtained in this case study apply only to the deliberately designed synthetic `case_study.csv` data; they cannot be generalized to different datasets, different noise regimes, or complex non-linear relationships.
- **Measurement version**: The results were obtained with the `0.0.1.dev0` development version installed at that time; `0.1.0` is the versioned state of the exact same codebase.
- **Diagnostic indicator only**: The flagged findings are diagnostic indicators, not absolute proof; similarly, the absence of a generated flag cannot be considered proof that there is no leakage or flaw.
