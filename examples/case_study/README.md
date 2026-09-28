# Case Study Dataset (Deliberately Corrupted Synthetic Data)

This directory contains a synthetic dataset with deliberately injected defects for auditing and diagnostic evaluation.

- **Purpose**: Demonstration of model diagnostic workflows on known defects. Not a benchmark.
- **Specification and Findings**: See [docs/CASE_STUDY.md](../../docs/CASE_STUDY.md).
- **RNG Seed**: `20260928`
- **Rows**: 600 data rows (601 lines including header)
- **Columns**: `row_id, ts, site, region, x1, x2, x3, y, pred, lo, hi, y_proxy`
- **CSV SHA-256**: `9587b66886a942ee9e9589fe65f000406f6f9f40f41ba7e7bf0b5e0cf9e942da`

## Reproduction

Run the deterministic generator script:

```bash
python examples/case_study/generate_case_study.py --out-dir examples/case_study
```
