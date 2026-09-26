# Golden Tests

This directory contains golden (expected) JSON outputs for integration testing.

The tests compare **normalized** JSON files. Normalization removes the `environment` block (which contains machine-specific paths, OS versions, and dependency versions that vary across setups) to ensure deterministic comparisons.

To regenerate golden files (e.g. after a deliberate format change), run:
```powershell
$env:MODELTRUST_REGEN_GOLDEN="1"
.\.venv\Scripts\python.exe -m pytest tests/integration/test_profile_golden.py -q
Remove-Item Env:MODELTRUST_REGEN_GOLDEN
```

**Warning:** Regeneration overwrites the canonical evidence files. The resulting `git diff` must be carefully inspected by the developer before committing to ensure no unintended changes were introduced.
