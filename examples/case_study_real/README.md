# Real-data case study dataset: UCI "Student Performance" (Portuguese)

This directory contains one real dataset used by the real-data case study
(`docs/CASE_STUDY_REAL.md`). The file is committed **byte-identical** to the
source distribution and is **not** modified, cleaned or transformed in any way.

## Provenance

- Dataset: Student Performance (ID 320), UCI Machine Learning Repository
- File: `student-por.csv` (Portuguese language course), 649 rows x 33 columns, delimiter `;`
- Creator: Paulo Cortez (University of Minho) and A. G. Silva
- Introductory paper: P. Cortez and A. G. Silva, "Using data mining to predict secondary school student performance", 2008
- DOI: 10.24432/C5TG7T
- License: Creative Commons Attribution 4.0 International (CC BY 4.0) — https://creativecommons.org/licenses/by/4.0/
- Source URL: https://archive.ics.uci.edu/static/public/320/student+performance.zip
- No changes were made to the data.

## Integrity chain (sha256)

| Artefact | Bytes | sha256 |
|---|---|---|
| Downloaded archive `student.zip` | 40735 | `82AE9D66437B9808DF42E8C89D2BB179C46E9CFBCF06F38ABC1D20B3B747E177` |
| Nested archive `student.zip` (inside the download) | 20478 | `4F671AE4598C20BB4E64DE0F65931C98A609A52E383604E2601BD8F7E3822427` |
| `student-por.csv` (committed file) | 93220 | `A7594A11D7771C0EFE1A740824E0E833DA9C4CAD07C39A9766A874575563FB3F` |

## Notes

- The tool **never downloads data**: this file is read from the repository.
- Target column is `G3` (final grade); group column used in the audit is `school`.
- `G1` and `G2` (first and second period grades) are present as features, as in the original distribution. The dataset documentation itself warns that `G3` correlates strongly with `G1` and `G2`.
- This dataset is a **case study**, not a benchmark. See `docs/CASE_STUDY_REAL.md` §1 and §7.

## Reproduce the audit

```bash
python -m modeltrust report --input examples/case_study_real/student-por.csv --target-col G3 --group-col school --model both --evaluate --shift --card --out-dir <DIR>
```
