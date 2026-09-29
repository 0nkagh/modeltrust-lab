# ModelTrust Lab: Real-Data Case Study

## 1. Purpose and honesty framing

This is a case study, **not a benchmark**. The numbers in this document are diagnostic indicators specific to a single dataset, not absolute performance claims about the tool or the models. Furthermore, the absence of a flag is not a proof of absence of leakage or other issues.

## 2. Dataset provenance

- **Dataset**: Student Performance (ID 320), UCI Machine Learning Repository
- **Creator**: Paulo Cortez (University of Minho) and A. G. Silva
- **DOI**: 10.24432/C5TG7T
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0) - https://creativecommons.org/licenses/by/4.0/
- **Source URL**: https://archive.ics.uci.edu/static/public/320/student+performance.zip
- **Dimensions**: 649 rows, 33 columns
- **Integrity chain**:
  - Downloaded archive `student.zip` (40735 bytes): `82AE9D66437B9808DF42E8C89D2BB179C46E9CFBCF06F38ABC1D20B3B747E177`
  - Nested archive `student.zip` (20478 bytes): `4F671AE4598C20BB4E64DE0F65931C98A609A52E383604E2601BD8F7E3822427`
  - `student-por.csv` (93220 bytes): `A7594A11D7771C0EFE1A740824E0E833DA9C4CAD07C39A9766A874575563FB3F`
- **Note**: The tool never downloads data. The dataset is read locally from the repository.

## 3. Canonical run

```bash
python -m modeltrust report --input examples/case_study_real/student-por.csv --target-col G3 --group-col school --model both --evaluate --shift --card --out-dir <DIR>
```

The hashes of the resulting JSON and MD files depend on the absolute path passed to `--out-dir` (recorded in the reports). The output contents are fully deterministic.

## 4. Observed findings

From the diagnostic card (`card.md`):

| # | Question | Status | Evidence |
|---|---|---|---|
| 1 | Missing or duplicate records? | answered | profile: duplicate_rows=0, missing cells reported |
| 2 | Target leakage suspicion? | answered | leakage.target_copy_exact=pass, target_copy_near=pass |
| 3 | Train/test or group leakage? | answered | split.modes.random=performed |
| 4 | Split strategy difference? | answered | multiple split modes performed (2) |
| 5 | Which groups have higher error? | answered | evaluation.group_errors performed |
| 6 | Distribution drift? | not_assessable | shift.drift.feature_ks not performed |
| 7 | Out-of-distribution (OOD) data? | answered | shift.ood.feature_range performed |
| 8 | Are uncertainty intervals calibrated? | not_assessable | uncertainty not performed |
| 9 | Which checks could not be performed? | answered | see not_assessable |
| 10 | How much can this report be trusted? | partial | see limitations and not_assessable |

**Checks summary**:

| Module | Total | Performed | Fail | Not Assessable |
|---|---|---|---|---|
| leakage | 12 | 8 | 0 | 4 |
| split | 3 | 2 | 0 | 1 |
| shift | 4 | 2 | 0 | 2 |

**Not assessable (with reason codes)**:
- leakage `subset_row_overlap`: `not_provided`
- leakage `subset_group_overlap`: `not_provided`
- leakage `subset_time_ranges`: `not_provided`
- leakage `preprocess.fit_scope`: `requires_pipeline_code`
- split `modes.temporal`: `not_provided`
- shift `drift.feature_ks`: `not_provided`
- shift `drift.target_ks`: `not_provided`

## 5. Metrics and group errors

**Metrics (`ols_baseline`)**:
- MAE: 0.869507
- RMSE: 1.453175
- R²: 0.818422
- n_scored: 130

**Metrics (`mean_baseline`)**:
- MAE: 2.582748
- RMSE: 3.411169
- R²: -0.000537
- n_scored: 130

**Group errors (`ols_baseline`)**:
- `GP`: n=95, RMSE=1.440666, MAE=0.891708
- `MS`: n=35, RMSE=1.486597, MAE=0.809249
- Worst by MAE: `GP`, `MS`

*These are diagnostic indicators on a single dataset, not performance claims.*

## 6. What the tool did not flag — and why that matters

The columns `G1` and `G2` (first and second period grades) are present as features in this dataset, and the original dataset documentation explicitly states that they are highly correlated with the target `G3`. The tool did not flag these features under `target_copy_exact` or `target_copy_near`, because they are not identical or near-identical deterministic copies of the target. This highlights a limitation: the tool's heuristic thresholding does not equate to a rigorous statistical correlation filter. As stated in the honesty framing, the absence of a flag is not a proof of absence of leakage.

## 7. Limitations

- No time column was provided, so temporal drift (`drift.feature_ks` and `drift.target_ks`) is `not_assessable` (`not_provided`).
- No uncertainty intervals were provided, so calibration is `not_assessable`.
- No cross-validation (CV) was requested, making subset leakages `not_assessable`.
- The tool currently lacks a column exclusion flag (running a second audit without `G1` and `G2` is outside the scope of this baseline case study).
- This is a single dataset evaluation.
- The tool relies on heuristic thresholds, without formal significance testing.
- The `--shift` flag currently only runs Out-of-Distribution (OOD) checks, but does not execute full drift analysis on its own without explicit temporal data.
