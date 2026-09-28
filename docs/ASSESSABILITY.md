# ModelTrust Soru Erişilebilirliği (Question Assessability)

## 1. Amaç ve Kural
ModelTrust model card (`card.json`) çıktısında yer alan 10 tanı sorusunun her biri, dokümante edilmiş en az bir girdi kombinasyonunda `answered` durumuna ulaşır.
- **Kural:** 10 sorunun her biri için geçerli ve desteklenen bir veri/parametre kombinasyonu mevcuttur.
- **Q10 Sözleşmesi:** Soru 10 ("How much can this report be trusted?") kural gereği ve sistem tasarımı uyarınca her zaman `partial` döner. Model kartı bir uygunluk belgesi değildir; kesinlik veya kusursuzluk iddiası taşımaz (D-074, D-076, D-077).
- **Ölçülemeyen Durumlar:** Bir girdi veya parametre sağlanmadığında ya da satır sayısı yetersiz olduğunda ilgili soru `not_assessable` durumuna geçer ve yapılandırılmış bir `reason_code` ile gerekçelendirilir.

## 2. Soru Erişilebilirlik Matrisi

| # | card.json soru metni (BİREBİR) | minimum komut | durum | kanıt alanı | not |
|---|---|---|---|---|---|
| 1 | Missing or duplicate records? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | answered | profile: duplicate_rows=0, missing cells reported | Profil modülü her çalıştırmada yürütülür. |
| 2 | Target leakage suspicion? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | answered | leakage.target_copy_exact=None, target_copy_near=None | Sızıntı modülü hedef sütun verildiğinde yürütülür. |
| 3 | Train/test or group leakage? | `modeltrust card --input tests/fixtures/leak_clean.csv --target-col y --group-col grp --out-dir <DIR>` | answered | split.modes.random=performed | Split modülü `--group-col` veya `--time-col` sağlandığında çalışır (D-081). |
| 4 | Split strategy difference? | `modeltrust card --input tests/fixtures/leak_clean.csv --target-col y --group-col grp --out-dir <DIR>` | answered | multiple split modes performed (2) | En az iki bölme modu (random + group/temporal) yürütüldüğünde karşılaştırma tamamlanır. |
| 5 | Which groups have higher error? | `modeltrust card --input tests/fixtures/eval_preds.csv --target-col y --pred-col pred --group-col grp --out-dir <DIR>` | answered | evaluation.group_errors performed | Tahmin sütunu (`--pred-col`) ve grup sütunu (`--group-col`) sağlandığında grup hataları analiz edilir. |
| 6 | Distribution drift? | `modeltrust card --input tests/fixtures/shift_drift.csv --target-col y --time-col ts --out-dir <DIR>` | answered | shift.drift.feature_ks performed | Zaman sütunu (`--time-col`) ve sayısal özellik sütunları sağlandığında drift analizi yürütülür. |
| 7 | Out-of-distribution (OOD) data? | `modeltrust card --input tests/fixtures/leak_clean.csv --target-col y --group-col grp --out-dir <DIR>` | answered | shift.ood.feature_range performed | Bölme verisi ve sayısal özellikler mevcut olduğunda OOD kontrolü yapılır. |
| 8 | Are uncertainty intervals calibrated? | `modeltrust card --input tests/fixtures/intervals_calibrated.csv --target-col y --lower-col lo --upper-col hi --nominal-coverage 0.9 --out-dir <DIR>` | answered | uncertainty.coverage=0.910 (Wilson [0.862, 0.942]), nominal=0.9, mean_width=3.290 | Alt/üst aralık sınırları ve nominal kapsam seviyesi sağlandığında kapsama analizi yürütülür. |
| 9 | Which checks could not be performed? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | answered | see not_assessable | Her zaman `answered` döner; yürütülemeyen tüm kontroller `not_assessable` bloğuna aktarılır. |
| 10 | How much can this report be trusted? | `modeltrust card --input tests/fixtures/simple_ok.csv --target-col y --out-dir <DIR>` | partial | see limitations and not_assessable | Her zaman `partial` döner; rapor sınırları ve yürütülemeyen kontroller kapsamında değerlendirilir. |

## 3. reason_code Sözlüğü

`card.json` içinde `reason_code` **soru nesnesinde değil**, `not_assessable` bloğunda ve soru `evidence` metni içinde yer alır.

### Gözlenen (modül, kontrol, reason_code) Üçlüleri
- `('leakage', 'index_like_feature', 'insufficient_rows')`
- `('leakage', 'preprocess.feature_target_near_deterministic', 'insufficient_rows')`
- `('leakage', 'preprocess.fit_scope', 'requires_pipeline_code')`
- `('leakage', 'preprocess.global_minmax_signature', 'insufficient_rows')`
- `('leakage', 'preprocess.global_standardization_signature', 'insufficient_rows')`
- `('leakage', 'preprocess.redundant_feature_pair', 'insufficient_rows')`
- `('leakage', 'subset_group_overlap', 'not_provided')`
- `('leakage', 'subset_row_overlap', 'not_provided')`
- `('leakage', 'subset_time_ranges', 'not_provided')`
- `('leakage', 'target_copy_exact', 'insufficient_rows')`
- `('leakage', 'target_copy_near', 'insufficient_rows')`
- `('shift', 'drift.feature_ks', 'not_provided')`
- `('shift', 'drift.target_ks', 'not_provided')`
- `('shift', 'ood.feature_range', 'insufficient_rows')`
- `('shift', 'ood.mahalanobis', 'insufficient_rows')`
- `('split', 'modes.group', 'not_provided')`
- `('split', 'modes.random', 'not_provided')`
- `('split', 'modes.temporal', 'not_provided')`

### Gözlenen Kodlar ve Anlamları
- **`not_provided`**:
  - **Anlamı:** İlgili denetim veya modül için zorunlu olan girdi bayrağı / veri sütunu kullanıcı tarafından komut satırında sağlanmadı.
  - **Gözlendiği Durumlar:**
    - `split.modes.random`, `split.modes.group`, `split.modes.temporal`: `--group-col` ve `--time-col` belirtilmediğinde (D-081 uyarınca split modülü atlanır) veya ilgili mod için gerekli zaman/grup sütunu verilmediğinde.
    - `leakage.subset_row_overlap`, `leakage.subset_group_overlap`, `leakage.subset_time_ranges`: `--subset-col` sağlanmadığında alt küme çakışma denetimleri atlanır.
    - `shift.drift.feature_ks`, `shift.drift.target_ks`: `--time-col` veya ilgili bölme sütunları belirtilmediğinde dağılım kayması denetimi atlanır.
- **`insufficient_rows`**:
  - **Anlamı:** Veri kümesindeki satır sayısı, ilgili istatistiksel testin veya kontrolün çalışması için gereken minimum eşiğin (`thresholds`) altındadır.
  - **Gözlendiği Durumlar:**
    - `leakage.target_copy_exact`, `leakage.target_copy_near`, `leakage.index_like_feature`, `leakage.preprocess.global_standardization_signature`, `leakage.preprocess.global_minmax_signature`, `leakage.preprocess.feature_target_near_deterministic`, `leakage.preprocess.redundant_feature_pair`: Veri setindeki satır sayısı minimum kontrol eşiğinin (`MIN_ROWS_FOR_COPY_CHECK` vb.) altındadır.
    - `shift.ood.feature_range`, `shift.ood.mahalanobis`: OOD denetimleri için bölme satır sayısı yetersiz olduğunda.
- **`requires_pipeline_code`**:
  - **Anlamı:** Kontrol yalnızca veri tablosuna bakarak gerçekleştirilemez; veri ön işleme veya model eğitim kodunun incelenmesini gerektirir.
  - **Gözlendiği Durumlar:** `leakage.preprocess.fit_scope` denetimi veri seti tablosu üzerinden değil eğitim boru hattı analizi gerektirir.

## 4. Ölçülemediğimiz Durumlar (Girdi Eksiklikleri ve Dayanaklar)

Belirli girdi eksikliklerinin hangi soruları `not_assessable` durumuna getirdiği kod satırları ve kararlı kontrol anahtarları ile sabittir:

- **Soru 3 (`Train/test or group leakage?`):**
  - `--group-col` veya `--time-col` sağlanmadığında split modülü atlanır ve soru `not_assessable` döner (`split.modes.random not performed (reason_code=not_provided)`). Dayanak: `src/modeltrust/card.py:78 (check: split.modes.random)`, `src/modeltrust/card.py:204 (check: split.modes)`, D-081.
- **Soru 5 (`Which groups have higher error?`):**
  - `--group-col` sağlanmadığında veya grup hata analizi yürütülmediğinde `not_assessable` döner (`group_errors not performed`). Dayanak: `src/modeltrust/card.py:100 (check: group_errors)`.
- **Soru 6 (`Distribution drift?`):**
  - `--time-col` sağlanmadığında veya drift analizi için uygun sayısal özellik sütunu bulunmadığında `not_assessable` döner (`shift.drift.feature_ks not performed`). Dayanak: `src/modeltrust/card.py:111 (check: shift.drift)`.
- **Soru 7 (`Out-of-distribution (OOD) data?`):**
  - Bölme verisi veya sayısal özellik aralıkları hesaplanamadığında `not_assessable` döner (`shift.ood.feature_range not performed`). Dayanak: `src/modeltrust/card.py:117 (check: shift.ood)`.
- **Soru 8 (`Are uncertainty intervals calibrated?`):**
  - `--lower-col` ve `--upper-col` sınır sütunları sağlanmadığında `not_assessable` döner (`uncertainty not performed`). Dayanak: `src/modeltrust/card.py:151 (check: uncertainty)`.
- **Soru 10 (`How much can this report be trusted?`):**
  - Model kartı bir sertifika/uygunluk belgesi olmadığı ve kesinlik iddiası taşımadığı için her zaman `partial` döner (`see limitations and not_assessable`). Dayanak: `src/modeltrust/card.py:159 (check: q10_by_rule)`, `docs/METHODS.md:201`, D-074, D-076, D-077.

## 5. Sınırlar
Bu matristeki erişilebilirlik sonuçları ve durumlar yalnızca belirtilen test fixture'ları ve CLI parametre kombinasyonları için doğrulanmıştır. Farklı şema, veri dağılımı veya eksik sütun yapısına sahip harici veri kümelerinde denetim sonuçları ve durumlar değişiklik gösterebilir. ModelTrust tanı araçları kesin güvence sağlamaz, veri ve model değerlendirme süreçlerine yönelik ampirik tanı sinyalleri sunar.
