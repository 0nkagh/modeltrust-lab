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
