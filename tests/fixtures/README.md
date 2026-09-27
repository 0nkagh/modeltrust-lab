| File | What it tests | What it intentionally breaks |
|---|---|---|
| simple_ok.csv | Basic successful parsing | Nothing |
| turkish_bom_semicolon.csv | BOM stripping and semicolon delimiter | Delimiter detection |
| decimal_comma.csv | Decimal comma detection and parsing | Numeric parsing without --decimal |
| dup_headers.csv | Duplicate column header detection | Duplicate columns |
| missing_target.csv | Schema validation for missing target | Missing target column |
| non_numeric_target.csv | Schema validation for numeric target | Non-numeric target values |
| quoted_commas.csv | Correct delimiter detection with quoted text | Text contains commas |
| profile_dirty.csv | Full profiling scenarios | Contains missing values, Inf, duplicates, and constants |
| empty_rows.csv | 0 row dataframe behavior | 0 rows with header |
| high_card_id.csv | High cardinality column detection | Column with >95% unique string values |
| leakage_base.csv | Leakage detection base cases (combined scenario) | Target copy, index like, row overlap, group overlap |
| leakage_time.csv | Leakage detection temporal overlap (combined scenario) | Train and test overlapping time ranges |
| leak_copy.csv | Exact target copy | Target copy exact fail |
| leak_nearcopy.csv | Near target copy | Target copy near fail | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| leak_index.csv | Index like feature | Index like feature fail |
| leak_overlap.csv | Subset row overlap | Subset row overlap fail |
| leak_group_overlap.csv | Subset group overlap | Subset group overlap fail |
| leak_time_overlap.csv | Subset time ranges | Subset time ranges fail |
| leak_clean.csv | No leakage | Suspicion count 0 | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| leak_copy_nan.csv | NaN handling in exact target copy | Creates exact NaN patterns between feature and target |

| split_groups.csv | Group split overlap | Random mode fails, group mode passes | .\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py |
| split_time.csv | Temporal split group leakage | Time ranges ordered, group leak fails | .\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py |
| split_dupes.csv | Random split row overlap | Duplicate rows cross split | Manually generated |
| eval_exact_linear.csv | Evaluation baseline metrics | ols_baseline mae=0.0, rmse=0.0, r2=1.0 | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| eval_preds.csv | Supplied predictions calculation | MAE is exactly 1.0 | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| eval_nan.csv | NaN row dropping in evaluation | drops 4 in feature, 3 in target | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| eval_const_target.csv | Zero variance target handling | r2_status = not_assessable | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| leak_std_full.csv | Full dataset standardization check | preprocess.global_standardization_signature fail | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| leak_minmax_full.csv | Full dataset minmax scaling check | preprocess.global_minmax_signature fail | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| leak_det_feature.csv | Near deterministic feature correlation | preprocess.feature_target_near_deterministic fail | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| leak_name_hints.csv | Suspicious feature naming hints | preprocess.suspicious_feature_name warning | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| shift_ood.csv | OOD feature range detection | x_out outside_ratio=1.0, ood.feature_range fail | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| shift_drift.csv | Distribution shift detection via KS | x feature KS >= 0.5, drift.feature_ks fail | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| shift_clean.csv | No shift / clean baseline | all shift checks pass | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| intervals_calibrated.csv | Uncertainty coverage check | measured coverage: 0.910 (nominal 0.90) | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| intervals_overconfident.csv | Uncertainty coverage gap check | measured coverage: 0.325 (nominal 0.90) | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| intervals_grouped.csv | Uncertainty group uniformity check | measured coverage: A=0.925, B=0.200 | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
| intervals_invalid.csv | Uncertainty bounds check | invalid bounds (lo > hi) in 3 rows | `.\.venv\Scripts\python.exe tests\fixtures\generate_fixtures.py` |
