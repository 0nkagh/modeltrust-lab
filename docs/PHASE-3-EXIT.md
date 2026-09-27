# PHASE 3 EXIT GATE — Kapanış ve Denetim Raporu

> **Kanıt Tazeliği Beyanı:** Bu belgedeki her sayı ve metrik T10 oturumunda (2026-09-27) doğrudan çalıştırılan komutların ham çıktılarından üretilmiştir; geçmiş oturumlardan kopyalanmış hiçbir veri içermez.

---

## 1. Kapsam ve Eklenen Yetenekler

PHASE 3 kapsamında ModelTrust Lab teşhis araç setine aşağıdaki yetenekler kazandırılmıştır:
- **`evaluate` alt komutu ve modülü (`src/modeltrust/evaluate.py`):**
  - **Baseline modelleri:** `mean_baseline` (hedefin eğitim ortalaması) ve `ols_baseline` (tüm sayısal özelliklerle çoklu doğrusal regresyon).
  - **Harici tahmin değerlendirme:** `--pred-col` sağlandığında model eğitimi atlanarak kullanıcının hazır tahminleri doğrudan skorlanır.
  - **Metrik hesaplama:** Regresyon metrikleri (MAE, RMSE, R²) ve R² tanımsızlık (`zero_variance_target`) kontrolleri.
  - **Çapraz doğrulama (CV):** K-katlı çapraz doğrulama şemaları (`random`, `group`, `temporal`), kat bazında ve birleşik (`aggregate`) hata istatistikleri.
  - **Grup hata analizi (`group_errors`):** Grup bazlı MAE, RMSE ve ortalama kalıntı (`mean_residual`) dökümü; asgari grup satır eşiği (`MIN_GROUP_ROWS_FOR_ERROR = 5`) ile filtrelenmiş `worst_by_mae` sıralaması ve `coverage_ratio` hesabı.
- **Preprocessing İmza Denetimleri (`src/modeltrust/audit/leakage.py`):**
  - `preprocess.fit_scope`: Tablo girdisinde her zaman `not_assessable` (`requires_pipeline_code`).
  - `preprocess.global_standardization_signature`: Z-score standartlaştırma tespiti (`PREPROCESS_NUMERIC_TOL = 1e-9`).
  - `preprocess.global_minmax_signature`: [0, 1] aralığına ölçekleme tespiti.
  - `preprocess.feature_target_near_deterministic`: Özellik ile hedef arasında deterministiğe yakın ilişki tespiti (`FEATURE_TARGET_DET_MIN = 0.999`).
  - `preprocess.redundant_feature_pair`: Sayısal özellik çiftleri arası aşırı korelasyon tespiti (`REDUNDANT_PAIR_MIN = 0.999`).
  - `preprocess.suspicious_feature_name`: Şüpheli kolon adı desenleri.
- **Rapor Entegrasyonu (`src/modeltrust/report.py`):**
  - `--evaluate` bayrağı ile `report.json` içine üst düzey `evaluation` bloğunun eklenmesi.
  - `report.md` içine son numaralı bölüm olarak `## 9. Model evaluation` bölümünün eklenmesi (Model tablosu, CV tablosu, en kötü gruplar tablosu, eşikler ve `not_assessable` dökümü).
  - Değerlendirme modülü hata kontrollerinin §2 özet tablosuna ve §5 Flagged patterns tablosuna entegrasyonu.

### İlgili Dosyalar
- Kaynak kodlar: `src/modeltrust/evaluate.py`, `src/modeltrust/report.py`, `src/modeltrust/cli.py`, `src/modeltrust/audit/leakage.py`, `src/modeltrust/audit/split.py`
- Test paketleri: `tests/unit/test_evaluate.py`, `tests/unit/test_report.py`, `tests/unit/test_split.py`, `tests/integration/test_report_cli.py`, `tests/integration/test_evaluate_cli.py`
- Golden dosyaları: `tests/golden/evaluate_exact_linear.normalized.json`, `tests/golden/report_evaluate.normalized.json`, `tests/golden/leakage_preprocess.normalized.json`
- Dokümanlar: `docs/METHODS.md`, `docs/DECISIONS.md`, `docs/INCIDENTS.md`, `docs/ENVIRONMENT.md`, `README.md`

---

## 2. Test Envanteri

T10 oturumunda `.\.venv\Scripts\python.exe -m pytest --collect-only -q` çıktısıyla toplanan **16 dosya ve 109 test**:

| Test Dosyası | Test Sayısı | Tür |
|---|---|---|
| `tests/integration/test_cli_inspect.py` | 5 | Integration |
| `tests/integration/test_evaluate_cli.py` | 3 | Integration |
| `tests/integration/test_leakage_cli.py` | 6 | Integration |
| `tests/integration/test_profile_golden.py` | 1 | Integration |
| `tests/integration/test_report_cli.py` | 10 | Integration |
| `tests/integration/test_split_cli.py` | 5 | Integration |
| `tests/unit/test_cli_smoke.py` | 4 | Unit |
| `tests/unit/test_dataio.py` | 10 | Unit |
| `tests/unit/test_evaluate.py` | 11 | Unit |
| `tests/unit/test_fixture_hygiene.py` | 1 | Unit |
| `tests/unit/test_high_cardinality.py` | 1 | Unit |
| `tests/unit/test_leakage.py` | 23 | Unit |
| `tests/unit/test_profile.py` | 6 | Unit |
| `tests/unit/test_report.py` | 7 | Unit |
| `tests/unit/test_schema.py` | 3 | Unit |
| `tests/unit/test_split.py` | 13 | Unit |
| **Toplam** | **109** | **109 passed (38.41s)** |

---

## 3. Doğrulanmış Davranışlar ve Sayılar Tablosu

T10 oturumunda çalıştırılan doğrulamalar:

| Ölçüm | Komut | Değer | Beklenen | Uyuşuyor mu? |
|---|---|---|---|---|
| Doğrusal model metrikleri | `evaluate --input tests/fixtures/eval_exact_linear.csv --target-col y --model ols` | `MAE: 0.0`, `RMSE: 0.0`, `R²: 1.0` | `MAE: 0.0`, `RMSE: 0.0`, `R²: 1.0` | Evet |
| Harici tahmin ve grup hataları | `evaluate --input tests/fixtures/eval_preds.csv --target-col y --pred-col pred --group-col grp` | Global `MAE: 1.0`, `RMSE: 1.732051`; Gruplar: `G1: 0.0`, `G2: 0.0`, `G3: 3.0` | Global `MAE: 1.0`, `RMSE: √3`; `G1/G2: 0.0`, `G3: 3.0` | Evet |
| Grup bazlı CV kat ortalaması | `evaluate --input tests/fixtures/split_groups.csv --target-col y --group-col grp --cv group` | `cv.aggregate.mae_mean = 0.867302` | `0.867302` | Evet |
| Preprocessing sızıntı bayrak sayısı | `report --input tests/fixtures/leak_std_full.csv --target-col y --evaluate` | §5 Flagged patterns tablosunda 4 satır (`leakage: 4`, `evaluation: 0`) | `target_copy_near`, `index_like_feature`, `global_standardization_signature`, `feature_target_near_deterministic` | Evet |
| Deterministik rapor hash çifti | İki ardışık `report --evaluate` çalıştırması | `report.json`: `dbeb5a78...` == `dbeb5a78...`<br>`report.md`: `e1ac39ce...` == `e1ac39ce...` | Byte-identik SHA-256 çiftleri | Evet |

---

## 4. `not_assessable` Envanteri

Girdi verisinde veya parametrelerde ön koşul sağlanmadığında atlanan kontrollerin gerekçe kodları (`reason_code`):

| Modül | Kontrol Adı | Durum | Gerekçe Kodu (`reason_code`) | Açıklama |
|---|---|---|---|---|
| `leakage` | `preprocess.fit_scope` | `not_assessable` | `requires_pipeline_code` | Tablo girdisinde (CSV/Parquet) pipeline kodu bulunmadığından fit kapsamı doğrudan denetlenemez. |
| `evaluation` | `cv_folds_size_sane` | `not_assessable` | `not_provided` / `insufficient_rows` | `--cv none` verildiğinde veya satır sayısı CV için yetersiz (`n < 10`) olduğunda. |
| `evaluation` | `group_error_coverage` | `not_assessable` | `not_provided` | `--group-col` verilmediğinde grup hatası hesaplanamaz. |
| `evaluation` | `supplied_predictions_present` | `not_assessable` | `not_provided` | `--pred-col` verilmediğinde harici tahmin doğrulaması atlanır. |
| `leakage` | `target_copy_exact` | `not_assessable` | `insufficient_rows` | Satır sayısı `MIN_ROWS_FOR_COPY_CHECK (5)` altındaysa. |
| `leakage` | `target_copy_near` | `not_assessable` | `insufficient_rows` | Satır sayısı `MIN_PAIRS_FOR_CORRELATION (20)` altındaysa. |
| `leakage` | `index_like_feature` | `not_assessable` | `insufficient_rows` | Satır sayısı `MIN_ROWS_FOR_INDEX_CHECK (10)` altındaysa. |
| `leakage` | `subset_*` kontrolleri | `not_assessable` | `not_provided` | `--subset-col` sağlanmadığında alt küme çakışma kontrolleri atlanır. |
| `split` | `temporal_*` kontrolleri | `not_assessable` | `not_provided` | `--time-col` sağlanmadığında zaman serisi bölme kontrolleri atlanır. |

---

## 5. Kanıtlanmamış / Kapsam Dışı Beyanı (Dürüstlük Bölümü)

Aşağıdaki başlıklar ModelTrust Lab kapsamında **kanıtlanmamıştır**, desteklenmemektedir veya kapsam dışındadır. Bu konularda herhangi bir güvenlik, doğruluk veya yeterlilik iddiası üretilmez:
1. **Preprocessing fit kapsamı:** Tablo üzerinden fit kapsamının train-only yapıldığı garanti edilemez; araç yalnızca veri üzerinde istatistiksel imza arar.
2. **Out-of-Distribution (OOD):** Test verisinin eğitim verisi dağılımı dışına çıkıp çıkmadığına dair OOD tespiti yapılmaz.
3. **Drift Analizi:** Özellik veya hedef kayması için zaman serisi drift testleri bulunmamaktadır.
4. **Belirsizlik ve Kalibrasyon:** Model tahminlerinin güven aralıkları, belirsizliği veya olasılık kalibrasyonu ölçülmez.
5. **Model Card:** Otomatik model kartı veya uyumluluk sertifikası üretimi kapsam dışıdır.
6. **Sınıflandırma Metrikleri:** Araç şu an için yalnız tabüler regresyon modellerini destekler; sınıflandırma metrikleri (AUC, F1, LogLoss vb.) bulunmaz.
7. **Hiperparametre Arama:** ModelTrust hiperparametre optimizasyonu yapmaz; `mean_baseline` ve `ols_baseline` araç içi referans baselines'dır.
8. **`--pred-col` Yolunda Holdout Yoktur:** Dışarıdan hazır tahmin sağlandığında tüm satırlar skorlanır; holdout veri ayrımı iddiası bulunmaz.
9. **Kullanıcı Kodu Çalıştırma:** Kullanıcının Python/scikit-learn modelleri import edilmez veya çalıştırılmaz.

---

## 6. PHASE 4 Adayları

Gelecek aşama (PHASE 4) için planlanan geliştirme alanları:
- Out-of-Distribution (OOD) ve Mahalanobis mesafe temelli anomali göstergeleri.
- Zaman serisi ve grup kayması (covariate shift / target drift) testleri.
- Model belirsizlik ve kalibrasyon teşhisleri.
- Otomatik Model Kartı (Model Card) JSON/Markdown ihracı.
- Tekrarlanabilirlik paketi (container/environment kilitleme desteği).
