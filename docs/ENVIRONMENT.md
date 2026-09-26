# Ortam ve Kurulum Kanıtları (ENVIRONMENT)

- **Tarih:** 2026-09-26
- **İşletim Sistemi:** Windows 11
- **Python (Global):**
```text
Python 3.12.8
```
- **.venv Yolu (sys.executable):** `C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe`
- **Kullanılan Kurulum Komutları:**
```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```
- **İnternet Erişimi:** Erişildi (paketler başarıyla indirildi).
- **.venv pip list (Ham Çıktı):**
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
- **Pandas ve Numpy Sürümleri (Ham Çıktı):**
```text
3.0.6 2.5.3
```
- **.venv Python Sürümü:** Python 3.12.8
- **Not:** `pandas 3.x` kullanıldığından string dtype'ları object/string davranışı açısından kontrol edilir; sabit object varsayımı yapılmamaktadır.
- **Bilinen Kısıtlamalar:**
  - `tmp_path` fixture'ı test çalıştırıcısında ara sıra `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\agah\\AppData\\Local\\Temp\\pytest-of-agah'` hatası vermiştir (tek seferlik gözlem, yetki sorunu atlatılmıştır).
  - `tempfile.mkdtemp()` üzerinde geçici dosya okuma-yazma testi başarılıdır (Çıktı: `temp_write: ok`).
- **Sapmalar / Notlar:** Bulunmamaktadır.
