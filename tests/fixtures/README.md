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
| leak_nearcopy.csv | Near target copy | Target copy near fail | `python -c "import pandas as pd, numpy as np; y = 10 + 5*np.arange(25); pd.DataFrame({'y':y, 'x1':y*1.0001, 'x2':np.random.rand(25)}).to_csv('tests/fixtures/leak_nearcopy.csv', index=False)"` |
| leak_index.csv | Index like feature | Index like feature fail |
| leak_overlap.csv | Subset row overlap | Subset row overlap fail |
| leak_group_overlap.csv | Subset group overlap | Subset group overlap fail |
| leak_time_overlap.csv | Subset time ranges | Subset time ranges fail |
| leak_clean.csv | No leakage | Suspicion count 0 | `python -c "import pandas as pd, numpy as np; np.random.seed(42); x1=np.random.rand(30); x2=np.random.rand(30); i=np.arange(30)%3; y=0.8*x1+0.4*x2+0.2*i+np.random.randn(30)*0.5; pd.DataFrame({'y':y, 'x1':x1, 'x2':x2, 'grp':[f'G{j//4}' for j in range(20)]+[f'G{5+j//4}' for j in range(10)], 'subset':['train']*20+['test']*10}).to_csv('tests/fixtures/leak_clean.csv', index=False)"` |
