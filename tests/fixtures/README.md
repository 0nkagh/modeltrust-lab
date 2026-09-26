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

