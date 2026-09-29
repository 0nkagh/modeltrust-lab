# Changelog

All notable changes to this project are documented in this file.
This project uses `0.x` versioning: before 1.0, the CLI contract and output schemas may change.

## Unreleased

### Added

- GitHub Actions CI (`.github/workflows/ci.yml`): the full test suite on Python 3.11, 3.12 and 3.13 (Ubuntu) and Python 3.12 (Windows), a sha256 integrity check of the committed case-study data, a wheel build + clean-venv smoke test, and a byte-level determinism check of the canonical case-study run.
- CI status badge in the README.

### Changed

- `requires-python` raised to `>=3.11` to match the CI-tested range; the previous `>=3.10` floor was never exercised (see `I-059`).
- Narrative documentation translated to English: `docs/METHODS.md`, `docs/ASSESSABILITY.md`, `docs/CASE_STUDY.md`, `docs/COMPARISON.md`, `docs/ENVIRONMENT.md`. Historical records in `docs/` remain Turkish (see `D-110`).
- Four Turkish code comments in `tests/` translated to English (comments only; no behaviour change).

## [0.1.0] - 2026-09-29

First release. A model-agnostic diagnostic toolkit that answers ten trustworthiness
questions about a tabular regression setup from a single CSV file.

### Added
- CLI commands: `inspect`, `profile`, `leakage`, `split`, `report`, `evaluate`, `shift`, `card`.
- Schema validation and canonical JSON provenance for every run.
- Dataset profiling: dtypes, missing values, duplicate rows, high-cardinality indicators.
- Leakage diagnostics: target copy and near-copy, index-like features, subset overlap,
  preprocessing-scope check (recorded as `not_assessable` without pipeline code).
- Split audits: random / group / temporal splits with row, group and time overlap checks.
- Model error evaluation: mean and OLS baselines, supplied predictions, cross-validation,
  per-group error breakdown.
- Uncertainty interval coverage evaluation with a Wilson interval.
- Distribution shift and OOD diagnostics: hand-written two-sample KS, feature-range
  outside ratio, Mahalanobis distance ratio.
- Deterministic JSON and Markdown outputs written into a single output directory;
  two runs with the same input and output directory are byte-identical.
- Reproducibility manifest (schema v1): input sha256, configuration, environment, tool version.
- Answerability semantics: every check returns `answered` / `partial` / `not_assessable`
  with a `reason_code` and an evidence pointer; controls that cannot run are never silently skipped.
- Diagnostic card (`card`) and full report (`report`) including a per-dataset `checks_summary`.
- Case study on deliberately corrupted synthetic data: generator, dataset and findings
  (`examples/case_study/`, `docs/CASE_STUDY.md`), locked by a determinism test.
- Measured side-by-side comparison against Evidently 0.7.23 on the case-study splits
  (`docs/COMPARISON.md`).
- Test suite: 197 tests (unit + integration), including CLI contract and `--help` locks.

### Notes
- Scope is intentionally narrow: tabular regression, one input file (CSV; optional Parquet
  requires pyarrow, which is not bundled), no model loading, no user code execution,
  no network access, no telemetry.
- Runtime dependencies: `numpy` and `pandas` only. The two-sample KS test and the Wilson
  interval are implemented in this repository.
- Evidence status: research prototype. Diagnostic indicators only. No production-readiness,
  compliance or safety claim is made, and the absence of a flag is not evidence of absence.
