# Environment and Installation Evidence (ENVIRONMENT)

- **Date:** 2026-09-26
- **Operating System:** Windows 11
- **Python (Global):**
```text
Python 3.12.8
```
- **.venv Path (sys.executable):** `C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe`
- **Installation Commands Used:**
```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```
- **Internet Access:** Accessed (packages successfully downloaded).
- **.venv pip list (Raw Output):**
```text
Package         Version     Editable project location
--------------- ----------- --------------------------------------
colorama        0.4.6
iniconfig       2.3.0
modeltrust      0.0.1.dev0  C:\Users\agah\Documents\modeltrust-lab
numpy           2.5.3
packaging       26.3
pandas          3.0.6
pip             24.3.1
pluggy          1.6.0
Pygments        2.21.0
pytest          9.1.1
python-dateutil 2.9.0.post0
six             1.17.0
tzdata          2026.4
```
- **Pandas and Numpy Versions (Raw Output):**
```text
3.0.6 2.5.3
```
- **.venv Python Version:** Python 3.12.8
- **Note:** Since `pandas 3.x` is used, string dtypes are checked for object/string behavior; a fixed object assumption is not made.
- **Known Limitations:**
  - The `tmp_path` fixture occasionally raised a `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\agah\\AppData\\Local\\Temp\\pytest-of-agah'` error in the test runner (single observation, permission issue bypassed).
  - Temporary file read-write test on `tempfile.mkdtemp()` is successful (Output: `temp_write: ok`).
- **Deviations / Notes:** None.
- **Environment Variable Management (OPENBLAS_NUM_THREADS):**
  - **Variable Name:** `OPENBLAS_NUM_THREADS`
  - **Value:** `1`
  - **Scope:** User (User-level persistent environment variable)
  - **Rationale:** To prevent OpenBLAS default thread pool memory allocation from failing (`OpenBLAS error: Memory allocation still failed after 10 retries, giving up`) and subprocesses from crashing under test conditions where numerous CLI subprocesses are launched sequentially on Windows 11; to ensure single-threaded deterministic mathematical operations.
  - **Removal / Revert Command:**
    ```powershell
    [System.Environment]::SetEnvironmentVariable("OPENBLAS_NUM_THREADS", $null, "User")
    ```
  - **Status:** The persistent user environment variable was removed on 2026-09-27 (D-041 / I-018); all tests and CLI run flawlessly without the persistent environment variable.


- **Line Ending Normalization:** Golden files are stored in the repository with LF line endings; the Windows working copy is committed with CRLF git normalization.
