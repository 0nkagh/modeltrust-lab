# Yöntemler ve Eşik Gerekçeleri

## Eşikler (koddan birebir)
| Sabit Adı | Değer |
| --- | --- |
| `MIN_ROWS_FOR_COPY_CHECK` | 5 |
| `MIN_PAIRS_FOR_CORRELATION` | 20 |
| `EXACT_COPY_EQUALITY_RATIO` | 1.0 |
| `NEAR_COPY_CORR_ABS_MIN` | 0.999 |
| `INDEX_LIKE_UNIQUE_RATIO_MIN` | 0.99 |
| `ATOL_NUMERIC_EQUALITY` | 1e-12 |
| `EXAMPLE_LIMIT` | 5 |
| `PREPROCESS_MIN_ROWS` | 10 |
| `PREPROCESS_NUMERIC_TOL` | 1e-9 |
| `FEATURE_TARGET_DET_MIN` | 0.999 |
| `REDUNDANT_PAIR_MIN` | 0.999 |

## Kapsam Dışı Bırakılanlar
Aşağıdaki sızıntı türleri statik denetim (yalnızca CSV) aracılığıyla güvenilir bir şekilde tespit edilemeyeceği için kasıtlı olarak kapsam dışı bırakılmıştır:
- Preprocessing ve Feature Engineering sırasında yaşanan sızıntılar
- Örnekleme bias'ı (Sampling bias)
- Etiket gürültüsü (Label noise)
- Veritabanı "join" işlemlerinden kaynaklı sızıntılar
- Temporal nedensellik ihlalleri (gelecekten geçmişe sızıntı)

## 1. Hedef Kolon Kopyası Şüphesi (Target Copy Suspicion)
- **Ne Ölçer:** Herhangi bir özelliğin (feature) hedef değişken (target) ile tam olarak aynı olup olmadığını.
- **Nasıl Ölçer:** Hedef kolon ile feature arasındaki sayısal farkların mutlak değerinin `ATOL_NUMERIC_EQUALITY` eşiğinden (1e-12) küçük veya eşit olup olmadığına (NaN ve NaN eşit kabul edilir), veya string/kategorik değerlerin birebir eşit olup olmadığına bakar.
- **Eşik Gerekçesi:** Oran eşiği `EXACT_COPY_EQUALITY_RATIO (=1.0)`'dır, yani kolonların tamamen aynı olması aranır.

### Hedef Kolon Yakın Kopyası Şüphesi (Target Copy Near Suspicion)
- **Ne Ölçer:** Herhangi bir özelliğin hedef değişkene çok yüksek bir doğrusal korelasyonla benzer olup olmadığını.
- **Nasıl Ölçer:** Hedef değişken ile feature arasındaki Pearson korelasyon katsayısının mutlak değerine bakar.
- **Eşik Gerekçesi:** Korelasyon katsayısının mutlak değeri `NEAR_COPY_CORR_ABS_MIN (=0.999)` ve üzerindeyse şüpheli kabul edilir (küçük yuvarlama hataları veya az sayıda aykırı değer esnemeleri için).

## 2. İndeks Benzeri Kolon (Index-Like Column)
- **Ne Ölçer:** Modelin öğrenebileceği bir sinyalden ziyade, her satır için neredeyse tekil (unique) olan bir kimlik (ID) veya indeks kolonu olup olmadığını.
- **Nasıl Ölçer:** Kolondaki eşsiz eleman sayısının toplam satır sayısına oranını hesaplar. Ayrıca kolonun kesinlikle tamsayı (integer) tipinde olması ve kesin artan (strictly monotonically increasing) olması şartı aranır.
- **Eşik Gerekçesi:** Eşik 0.99. %99'dan fazla tekil değer içeren, tamsayı tipli ve monoton artan kolonlar modelin ezber yapmasına sebep olacağı için şüpheli kabul edilir (yanlış pozitifleri azaltmak için strict kurallar eklenmiştir).

## 3. Alt Küme (Subset) Satır Çakışması (Subset Row Overlap)
- **Ne Ölçer:** Train, validation veya test gibi alt kümeler (subset) arasında birebir aynı satırların olup olmadığını.
- **Nasıl Ölçer:** Tüm kolonların (subset kolonu hariç) string temsillerinin birleşimi üzerinden SHA-256 parmak izi çıkarılır. Aynı parmak izinin birden fazla alt kümede yer alıp almadığı çiftler (pairs) halinde sayılır. Çıktıda her çift için overlap_count ve o çiftteki daha küçük kümenin boyutuna oranı (overlap_ratio_of_smaller) raporlanır.
- **Eşik Gerekçesi:** 0; farklı alt kümelerde tam çakışan satır sayısı 0 olmalıdır. En az 1 çakışma raporlanır.

## 4. Alt Küme (Subset) Grup Çakışması (Subset Group Overlap)
- **Ne Ölçer:** Grup kolonu (örn. patient_id) kullanıldığında, aynı gruba ait satırların birden fazla alt kümeye dağılıp dağılmadığını.
- **Nasıl Ölçer:** Grup kimliklerinin subset değerlerine göre dağılımına bakılır. Bir grup ID, hem train hem test kümesinde varsa çakışma sayılır.
- **Eşik Gerekçesi:** 0; gruplar alt kümeler arasında ayrık olmalıdır (strict split).

## 5. Alt Küme Zaman Sızıntısı Şüphesi (Temporal Subset Leakage Suspicion)
- **Ne Ölçer:** Zaman bazlı (temporal) bir ayrım yapılması beklendiğinde, eğitim (train) kümesindeki bazı örneklerin, test kümesinden daha güncel (ileriki tarihli) olup olmadığını.
- **Nasıl Ölçer:** `subset_col` train/test gibi zaman sırası varsayımı içeriyorsa (bunu doğrudan doğrulayamaz, ancak uyarı verebilir), alt kümelerin max/min zaman damgaları arasında açık bir çakışma (overlap) veya tersine dönme olup olmadığını kontrol eder.
- **Eşik Gerekçesi:** Test kümesinin en eski (min) tarihi, Train kümesinin en yeni (max) tarihinden eski ise bir uyarı tetiklenir (overlap > 0).
 
## Preprocessing İmza Kontrolleri (Preprocessing Signature Checks)

| Kontrol Adı | Kapsam / Açıklama | Eşik / Kural | Sonuç / Davranış |
| --- | --- | --- | --- |
| `preprocess.fit_scope` | Pipeline fit kapsamı (train-only fit yapılıp yapılmadığı) | CSV'den tespit edilemez | Her zaman `not_assessable`, `reason_code="requires_pipeline_code"` |
| `preprocess.global_standardization_signature` | Tüm veri üzerinde standartlaştırma (z-score) imzası | `abs(mean) <= PREPROCESS_NUMERIC_TOL (1e-9)` ve (`abs(std_ddof0 - 1) <= PREPROCESS_NUMERIC_TOL` veya `abs(std_ddof1 - 1) <= PREPROCESS_NUMERIC_TOL`) (`n >= PREPROCESS_MIN_ROWS (10)`) | `fail` (teşhis göstergesi) |
| `preprocess.global_minmax_signature` | Tüm veri üzerinde min-max ölçekleme imzası | `min ≈ 0` ve `max ≈ 1` (`atol=PREPROCESS_NUMERIC_TOL (1e-9)`, `n >= PREPROCESS_MIN_ROWS (10)`) | `fail` (teşhis göstergesi) |
| `preprocess.feature_target_near_deterministic` | Özellik ile hedef arasında deterministiğe yakın doğrusal ilişki | `abs(corr) >= FEATURE_TARGET_DET_MIN (0.999)` (`n >= MIN_PAIRS_FOR_CORRELATION (20)`) | `fail` (teşhis göstergesi) |
| `preprocess.redundant_feature_pair` | İki sayısal özellik arasında aşırı yüksek korelasyon | `abs(corr) >= REDUNDANT_PAIR_MIN (0.999)` (`n >= MIN_PAIRS_FOR_CORRELATION (20)`) | `pass` (bilgi amaçlı), uyarı: `redundant_features` |
| `preprocess.suspicious_feature_name` | Şüpheli özellik isim kalıpları (`target`, `_mean`, `zscore` vb.) | Kalıp eşleşmesi (case-insensitive) | `pass` (asla fail değil), uyarı: `suspicious_feature_names` |

Bu kontroller imza temellidir; pipeline kodunun train-only fit yaptığını kanıtlamaz. Tespit edilemeyenler: hedefle türetilmiş özellikler, test istatistikleriyle doldurma (imputation), tüm veriyle yapılan özellik seçimi. → bunlar raporda `not_assessable` olarak görünür.

## Yorumlama
Tüm bu denetim çıktıları **teşhis göstergesidir (Diagnostic indicators only)**. Bir kuralın işaretlenmesi veride kesin bir hata olduğu anlamına gelmez (meşru bir durum olabilir). Aynı şekilde, bir bayrak olmaması da sızıntı (leakage) veya hata olmadığı garantisini vermez.

## 6. Split Audit (Bölme Denetimi)
- **Ne Ölçer:** Aynı veri üzerinde random, group ve temporal stratejilerle (deterministik) oluşturulan bölmelerin sızıntı (leakage) ve kararsızlık özelliklerini karşılaştırmalı olarak teşhis eder.
- **Neyi Ölçmez:** Model bazlı karşılaştırmalar (hata payı - MAE/RMSE/R²), CV (Cross-Validation) döngüsü veya istatistiksel anlamlılık testleri bu aşamanın kapsamı dışındadır (PHASE 3 konularıdır). Yalnızca bölme (split) özellikleri incelenir.
- **Algoritmalar ve Yöntemler:**
  - **Yuvarlama Kuralı:** Test kümesi boyutu `n_test = int(round(test_size * n))` ile belirlenir ve en az 1, en fazla `n-1` olacak şekilde sınırlandırılır (clamp).
  - **Random Split:** Yöntem olarak `numpy.random.default_rng(seed).permutation` kullanılır. **Tekrarlanabilirlik kapsamı:** Sadece aynı ortam ve aynı numpy sürümü (D-010); numpy sürümleri arası kararlılık garanti edilmez.
  - **Group Split (Greedy):** Gruplar satır sayısı azalan, grup adı ise artan sırada sıralanır. En kalabalık gruptan başlanarak, test kümesindeki toplam satır sayısı `n_test` hedefine ulaşana kadar gruplar sırayla test kümesine atanır. (Eğer son eklenen grup ile `n_test` sınırı aşılırsa, o grup da teste dahil edilir; dolayısıyla gerçek `test_fraction` her zaman `test_size` ile birebir aynı olmayabilir). Kalan tüm gruplar train kümesine atanır. Deterministik bir yaklaşımdır.
  - **Temporal Split:** Veri, zaman kolonu ve ardından orijinal satır indeksine göre sıralanarak ayrılır.

## 7. Rapor Üretimi (Report Generation)
- **Kapsam ve İçerik:** `tool`, `run_metadata`, `environment`, `input`, `column_spec`, `schema`, `profile`, `leakage` ve isteğe bağlı `split` bloklarını içeren kanonik bir JSON üretir. `--evaluate` argümanı verildiğinde (varsayılan olarak kapalıdır), üst düzey `evaluation` bloğu ve Markdown raporuna `## 9. Model evaluation` bölümü eklenir (davranış `evaluate` komutuyla birebir aynıdır). `--shift` argümanı verildiğinde (varsayılan olarak kapalıdır), üst düzey `shift` bloğu JSON'a eklenir; Markdown'da `## 6. Split comparison` başlığı `## 6. Split comparison and distribution shift` olarak genişler ve `### Distribution shift & OOD` tablosu (`| Check | Result | Detail |`) eklenir. Bu iki bayrak bağımsız ve birlikte kullanılabilir.
- **Markdown İzdüşümü:** JSON ile birlikte oluşturulan `report.md` dosyası, JSON çıktısının doğrudan izdüşümüdür. JSON yapısında bulunmayan hiçbir ek bilgi Markdown'a eklenmez.
- **Determinizm:** Markdown raporundaki listeler ve tablolar deterministik bir sırada tutulur, ondalık sayılar formatlanarak verilir ve `not_assessable` olan kontroller atlanmaz, özel bir bölümde (`What could NOT be assessed`) raporlanır.
- **Yorumlama Dili:** Rapor, modelin güvende olduğuna veya sızıntı olmadığına dair kesin sonuç cümleleri ("leakage-proof", "safe", "fully reliable" vb.) içermez. Sadece teşhis göstergesi olduğunu belirten uyarılar içerir.

## 8. Evaluation (Değerlendirme)
- **Modeller (Baseline):**
  - **mean_baseline:** Eğitim kümesindeki hedef değişkenin (target) aritmetik ortalamasını tüm test örnekleri için tahmin olarak döndürür.
  - **ols_baseline:** Tüm sayısal özellikler üzerinden (sabit terim eklenerek) Sıradan En Küçük Kareler (Ordinary Least Squares - OLS) ile çoklu doğrusal regresyon uygular.
  - **supplied_predictions:** Kullanıcı dışarıdan hazır bir tahmin kolonu (`--pred-col`) sağlarsa model eğitimi atlanır ve bu kolon test/değerlendirme için doğrudan kullanılır.
- **Metrikler ve Yöntemler:**
  - **MAE (Mean Absolute Error):** Hataların mutlak değerlerinin ortalaması. `mean(|y - y_pred|)`
  - **RMSE (Root Mean Square Error):** Hataların karelerinin ortalamasının karekökü. `sqrt(mean((y - y_pred)^2))`
  - **R² (R-squared):** Modelin açıkladığı varyans oranı. `1 - (SS_res / SS_tot)` formülü ile hesaplanır. SS_tot sıfır ise `not_assessable` durumu döner ve `zero_variance_target` uyarısı verilir.
- **Eksik Veri (NaN) Davranışı:**
  - Hedef değişkende veya sağlanan tahminde (`supplied_predictions` kullanılıyorsa) NaN olan test satırları skorlamaya (n_scored) dahil edilmez.
  - OLS eğitimi sırasında, hedefte veya herhangi bir özelliğinde (feature) NaN olan satırlar eğitim kümesinden düşülür.
- **Cross-Validation (CV):** K-katlı çapraz doğrulama (CV) modülleri (random, group, temporal) desteklenir. Modüle özgü bölme mantıkları (örneğin grup bütünlüğünü bozmayan greedy group allocation) uygulanır. Eğer test kümesindeki veri çok küçükse (`CV_MIN_FOLD_SIZE < 3`) kat değerlendirilmez (`not_assessable`).
- **Grup Hatası (Group Error):** Grup modunda (`--split-mode group`), test kümesinde yer alan her bir grup için test hataları (n, MAE, RMSE, mean residual) bağımsız hesaplanarak listelenir. MAE değerine göre gruplar sıralanır ve en kötü performans gösteren gruplar (`TOP_WORST_GROUPS = 3`) belirlenir. Yeterli örneğe sahip olmayan (`n < 5`) gruplar bu sıralamanın dışında bırakılır.
  - **`coverage_ratio` Tanımı:** `coverage_ratio = n_rows_evaluated / n_rows_scored` olarak hesaplanır. Skorlanan toplam satırlar içinde, asgari grup büyüklüğü eşiğini (`MIN_GROUP_ROWS_FOR_ERROR = 5`) sağlayan ve grup hata sıralamasına dahil edilen geçerli satırların oranını ifade eder. Değerlendirilemeyen (not_assessable) sayısal alanlar raporda 0.000000 olarak gösterilmez; N/A ve reason_code (örn. `N/A (not_provided)`) ile gösterilir.

### 8.x Eşikler
| Sabit Adı | Değer | Açıklama |
| --- | --- | --- |
| `MIN_ROWS_FOR_METRICS` | 10 | Metriklerin hesaplanabilmesi için gereken asgari satır sayısı |
| `MIN_GROUP_ROWS_FOR_ERROR` | 5 | Bir grubun hata sıralamasına (worst_by_mae) dahil edilmesi için gereken asgari satır sayısı |
| `TOP_WORST_GROUPS` | 3 | En yüksek MAE değerine sahip listelenecek maksimum grup adedi |
| `CV_MIN_FOLD_SIZE` | 3 | Bir CV katının değerlendirilebilmesi için gereken asgari test satırı sayısı |
| `MIN_ROWS_FOR_COPY_CHECK` | 5 | Hedef kolon kopyası denetimi için asgari satır sayısı |
| `MIN_ROWS_FOR_INDEX_CHECK` | 10 | ID benzeri özellik denetimi için asgari satır sayısı |
| `PREPROCESS_MIN_ROWS` | 10 | Ön işleme imza denetimleri için asgari satır sayısı |
| `MIN_PAIRS_FOR_CORRELATION` | 20 | Korelasyon ve deterministik özellik-hedef ilişkisi için asgari satır sayısı |
| `MIN_ROWS_FOR_INTERVAL` | 20 | Belirsizlik (uncertainty) hesaplaması için asgari satır sayısı |
| `WILSON_Z` | 1.96 | Wilson skor aralığı z-değeri (%95 güven) |
| `COVERAGE_GAP_TOL` | 0.05 | Nominal kapsama ile ampirik kapsama arasındaki kabul edilebilir açık |
| `GROUP_COVERAGE_RANGE_MAX` | 0.30 | Gruplar arası maksimum kapsama oranı farkı (uniformity tolerance) |
| `WIDTH_BINS` | 4 | Aralık genişliği histogram kırılımı (bin sayısı) |

### 8.y Belirsizlik (Uncertainty)
Eğer `evaluate` (veya `report --evaluate`) komutuna `--lower-col` ve `--upper-col` argümanları birlikte verilirse, modelin tahminsel belirsizlik (predictive uncertainty) performansı ölçülür ve evaluation bloğu içine `uncertainty` bölümü eklenir.

- **Kapsama Oranı (Coverage):** Test kümesindeki hedef değişkenin (target) alt ve üst sınırlar (`[lower, upper]`) içinde kalma oranıdır. Ampirik olarak (observed coverage) hesaplanır.
- **Wilson Skoru:** Kapsama oranının 95% güven aralığı, küçük örneklem kararlılığı için $z=1.96$ (Wilson Score Interval) ile tahmin edilir.
- **Grup Kapsaması:** Veri gruplara ayrılmışsa, her grubun kendi kapsama oranı ayrıca raporlanır. `MAX_GROUP_COVERAGE_GAP (0.10)` eşiği kullanılarak, gruplar arası maksimum kapsama farkının (max - min) çok yüksek olup olmadığı (`interval.group_coverage_uniformity`) denetlenir.
- **Nominal Kapsama Karşılaştırması:** Kullanıcı `--nominal-coverage` (ör. 0.95) sağlarsa, ampirik kapsamın alt sınırının bu değere ulaşıp ulaşmadığı (`interval.coverage_gap`) kontrol edilir. Ulaşmıyorsa `non_nominal_coverage` uyarısı verilir.

**Yorumlama (Neyi Ölçmez):** 
Belirsizlik göstergeleri "single split, no distribution-free guarantee" kapsamında çalışır. Hesaplanan oranlar sadece elde edilen test kümesine (single split) aittir, distribution-free bir istatistiksel geçerlilik taşımaz (ör. Conformal Prediction garantisi verilmez). Kapsama oranının nominal değere yakın olması, model aralıklarının "tamamen kalibre (fully reliable)" veya "production-ready" olduğu anlamına gelmez, yalnızca bir diagnostic indicator'dır.

*Yarıçap/hata ölçeği notu: `intervals_*` sentetik verilerinde (fixture) hedef değişkenin gürültü standart sapması ($\sigma=1.0$) baz alınmış olup, güven aralığı hesaplamalarında yarıçap genişliği bu gürültü ölçeğiyle doğrudan ilişkilidir (örn. `%90` kapsama için ideal yarıçap yaklaşık `1.645 * 1.0`). Fixture'lar doğrudan bu prensiple üretilmiştir ve testler ölçülen ampirik kapsama oranlarına tolerans payıyla bağlanmıştır.*

### 8.z Neyi ölçmez
Bu blok kullanıcının modelinin genel performansını ölçmez. `--pred-col` verildiğinde **tüm satırlar** skorlanır, holdout yoktur. Hiperparametre arama, sınıflandırma metrikleri, model kalibrasyon güvencesi kapsam dışıdır. OLS ve ortalama baseline yalnız araç içi referanstır.

## 9. Dağılım Kayması ve OOD (Gösterge)

ModelTrust Lab `shift` modülü (`src/modeltrust/audit/shift.py`), eğitim ve test bölmeleri arasındaki veri dağılımı farklılıklarını ve alan dışı (Out-of-Distribution - OOD) örnekleri istatistiksel ve geometrik göstergelerle teşhis eder:

- **Kontroller:**
  - **`ood.feature_range`:** Sayısal özelliklerin eğitim kümesindeki asgari ve azami (`[train_min, train_max]`) değer sınırlarını hesaplar. Test kümesinde bu sınırların dışına çıkan değerlerin oranını (`outside_ratio`) ve en az bir özelliği sınır dışına çıkan test satırlarının oranını (`row_outside_ratio`) ölçer. `max_feature_outside_ratio >= OOD_FEATURE_OUTSIDE_RATIO_MIN (0.10)` ise başarısız (`fail`) sayılır.
  - **`ood.mahalanobis`:** Eğitim kümesi üzerinden ortalama vektör $\mu$ ve kovaryans matrisi $\Sigma$ (`ddof=1`, tekil matrisler için Moore-Penrose sözde tersi $\Sigma^+$) hesaplar. Test ve eğitim satırlarının Mahalanobis mesafesi $d(x) = \sqrt{(x-\mu)^T \Sigma^+ (x-\mu)}$ medyan oranını (`ratio = median_test / median_train`) belirler. `ratio >= OOD_MAHALANOBIS_RATIO_MIN (2.0)` ise başarısız (`fail`) sayılır.
  - **`drift.feature_ks`:** Train ve test kümesi sayısal özellikleri arasındaki iki örneklemli Kolmogorov-Smirnov ($D$) istatistiğini $D = \max |F_{\text{train}}(x) - F_{\text{test}}(x)|$ formülüyle hesaplar. En yüksek özellik KS değeri `max_ks_stat >= DRIFT_KS_STAT_MIN (0.25)` ise başarısız (`fail`) sayılır.
  - **`drift.target_ks`:** Train ve test kümesi hedef değişkenleri arasındaki Kolmogorov-Smirnov ($D$) istatistiğini hesaplar. `ks_stat >= DRIFT_KS_STAT_MIN (0.25)` ise başarısız (`fail`) sayılır.
- **Sabit Kolon Politikası:** Eğitim kümesinde varyansı sıfır (`std == 0`) olan sabit kolonlar shift analizinden hariç tutulur ve `constant_features_excluded` uyarısıyla listelenir.
- **Zaman Kolonu Koşulu:** Drift kontrolleri (`drift.feature_ks`, `drift.target_ks`) zaman serisi ekseninde anlamlı olduğundan, `--time-col` verilmediğinde drift kontrolleri `not_assessable` (`not_provided`) olarak işaretlenir; OOD kontrolleri ise random veya group bölmelerinde de çalıştırılabilir.

### 9.x Eşikler
| Sabit Adı | Değer | Açıklama |
| --- | --- | --- |
| `SHIFT_MIN_ROWS` | 20 | Shift analizi için eğitim kümesinde gereken asgari satır sayısı |
| `CV_MIN_FOLD_SIZE` | 3 | Shift analizi için test kümesinde gereken asgari satır sayısı |
| `OOD_FEATURE_OUTSIDE_RATIO_MIN` | 0.10 | Bir özelliğin OOD aralık aşımı fail eşiği |
| `OOD_MAHALANOBIS_RATIO_MIN` | 2.0 | Mahalanobis medyan mesafe oranı fail eşiği |
| `DRIFT_KS_STAT_MIN` | 0.25 | Kolmogorov-Smirnov kayma istatistiği fail eşiği |

### 9.y Neyi Ölçmez (Dürüstlük ve Sınırlar)
- **p-değeri ve İstatistiksel Anlamlılık Yoktur:** Modül parametrik testler veya p-değeri hesaplamaz (scipy bağımlılığı yoktur). Raporlanan değerler kesin hipotez testi sonuçları değil, ampirik mesafelerdir.
- **Heuristik Eşikler:** Belirlenen eşikler (0.10, 2.0, 0.25) kural tabanlı tanı göstergeleridir ("diagnostic indicators"); mutlak bir kabul/ret sınırını temsil etmez.
- **Nedensellik ve Başarısızlık Garantisi Yoktur:** OOD veya kayma bayrağının verilmesi bir verinin meşru bir rejim değişiminden kaynaklanabileceğini dışlamaz; aynı şekilde bir bayrağın bulunmaması dağılım kaymasının kesinlikle olmadığı anlamına gelmez ("Absence of a flag does not establish absence of shift").
- **Model Çökme İddiası Yoktur:** Alan dışı örnek bulunması veya KS istatistiğinin yüksek olması, kullanıcının modelinin bu örnekler üzerinde kesinlikle hatalı tahmin üreteceğini garanti etmez.

### 9.z `shift` Komutu Sözleşmesi (CLI Kuralları)
- **`--target-col` zorunludur** (`shift` komutu ve `report --shift` için). Eksikse `exit 2` döner (`Error: --target-col is required`). Gerekçe: `drift.target_ks` kontrolü hedef kolon üzerinden hesaplanır; kolon yoksa kontrol anlamsızlaşır.
- **`--split-mode group`** için **`--group-col` zorunludur**; eksikse `exit 4` döner (`Error: --split-mode group requires --group-col`).
- **`--split-mode temporal`** için **`--time-col` zorunludur**; eksikse `exit 4` döner (`Error: --split-mode temporal requires --time-col`).
- **`--time-col` yoksa** drift kontrolleri (`drift.feature_ks`, `drift.target_ks`) `not_assessable (not_provided)` olarak işaretlenir; OOD kontrolleri (`ood.feature_range`, `ood.mahalanobis`) çalışmaya devam eder.
- **`report --shift` ile `--split-mode`/`--test-size`** birlikte kullanılabilir; bu bayraklar artık yalnız `--evaluate` değil, `--evaluate` veya `--shift` varlığını gerektirir. İkisi de yoksa `exit 2` döner (`Error: {flag} requires --evaluate or --shift`).



## 11. Model Card (Özet Rapor)

`modeltrust card` komutu, veri kaynağı, test edilen senaryolar, ölçülen metrikler ve gerçekleştirilemeyen denetimlerin teşhis özetini içeren bir kart üretir. 

### 11.1 Kart Bölümleri
1. **Scope & disclaimer:** Kartın bir sertifika olmadığı, performans garantisi sunmadığı belirtilir.
2. **Data provenance:** Girdi veri yolunu, satır/kolon sayısını, veri hash'ini, kullanılan sürüm ve seed bilgilerini içerir.
3. **Questions answered:** Modüllerin çalışabilirlik durumuna göre 10 kritik soruya verilen yanıtlar (durum ve kanıt) tablosu. Split modülü yalnız `--group-col` veya `--time-col` verildiğinde çalışır; aksi hâlde kontroller atlanır ve reason_code ile kaydedilir.
4. **Checks summary:** Modül bazında (örn. `leakage`) gerçekleştirilen, başarısız olan ve yapılamayan denetimlerin sayımı. Bir modül atlandığında (örn. split çalıştırılmadığında), modül özette toplam kontrol sayısı, performed=0, fail=0 ve not_assessable olarak kayda geçer.
5. **Not assessable:** Gerçekleştirilemeyen denetimlerin listesi ve nedenleri (reason_code). Atlanan modüllerin kontrolleri ilgili reason_code (örn. `not_provided`) ile burada listelenir.
6. **Metrics:** Modelin ölçülen hata metrikleri, çapraz doğrulama (CV) sonuçları ve varsa belirsizlik aralığı (uncertainty interval) kapsamı.
7. **Thresholds:** Kullanılan konfigürasyon ve eşik değerleri (örn. `OOD_MAHALANOBIS_RATIO_MIN`).
8. **Limitations:** Aracın kısıtlamaları (sadece tabular regression, p-değeri yok, vb.) ve uyarılar.
9. **Reproduce:** Raporu birebir aynı seed ve ayarlarla tekrar üretmek için gereken CLI komutu.

### 11.2 "Questions Answered" Durum Kuralları
Kart, değerlendirme durumunu belirlemek için aşağıdaki katı kuralları (deterministik) kullanır:

| # | Soru | `answered` koşulu | Aksi hâlde |
|---|---|---|---|
| 1 | Eksik/duplicate kayıt? | profile çalıştı | — |
| 2 | Target leakage şüphesi? | `leakage.target_copy_exact` **veya** `target_copy_near` performed | `not_assessable` |
| 3 | Train/test veya grup sızıntısı? | `split.modes.random` performed | `not_assessable` |
| 4 | Split stratejisi farkı? | random/group/temporal'dan ≥2 performed | `partial` |
| 5 | Hangi gruplarda hata? | `evaluation.group_errors.status == "performed"` | `not_assessable` |
| 6 | Drift? | `shift.drift.feature_ks.status == "performed"` | `not_assessable` |
| 7 | OOD? | `shift.ood.feature_range.status == "performed"` | `not_assessable` |
| 8 | Belirsizlik kalibre mi? | `uncertainty.status == "performed"` | `not_assessable` |
| 9 | Hangi kontroller yapılamadı? | her zaman `answered` | — |
| 10 | Rapora ne kadar güvenilebilir? | her zaman `partial` | — |

### 11.3 Neyi İddia Etmez (Sınırlar)
Model card bir **sertifika değildir**. Herhangi bir modelin "production-ready" olduğunu, "compliant" (mevzuata uygun) olduğunu veya performans/güvenilirlik garantisi taşıdığını iddia etmez. Yalnızca belirtilen veri kümesi ve çalıştırılan argümanlarla üretilen bir teşhis (diagnostic) özetidir.

### 11.4 `n_scored` Kapsamı — Supplied Predictions Modu

`--pred-col` verildiğinde CLI, tahminlerin kullanıcı tarafından dışarıda hesaplanmış olduğunu varsayar. Bu modda:

- **Split uygulanmaz.** Tüm sağlanan satırlar (NaN olmayan) metriğe dahil edilir.
- Metrik tablosundaki `n_scored (all rows provided)` kolonu bu gerçeği yansıtır: değer, sağlanan veri setindeki NaN-olmayan satır sayısıdır; bir test split'inin büyüklüğü değildir.
- `--split-mode` ve `--test-size` argümanları bu modda train/test split metrikleri üretmez. Split modülü yalnız `--group-col` veya `--time-col` sağlandığında çalışır; aksi hâlde split atlanır ve checks summary ile not_assessable listesine reason_code=not_provided olarak kaydedilir.

### 11.5 `n_scored` Dinamik Kapsam Kuralı

Metrik tablosundaki `n_scored` sütun başlığı model satırlarına göre dinamik olarak belirlenir (`scored_scope_label` yardımcı fonksiyonu — tek kaynak, `report.py` içinde tanımlı, card ve report tarafından paylaşılır):

| n_train durumu | Başlık |
|---|---|
| Tüm satırlarda `n_train == 0` | `n_scored (all rows provided)` |
| Tüm satırlarda `n_train > 0` | `n_scored (split)` |
| Karmaşık küme (hem 0 hem >0) | `n_scored (scope varies)` + warnings notu |

`n_train == 0`: supplied_predictions modu; split uygulanmaz, skor tüm satırlarda. `n_train > 0`: dahili model eğitimi; skor yalnızca test split'inde.

## 12. Reproducibility Manifest

`--manifest` bayrağı verildiğinde `card` komutu, kart çıktılarıyla birlikte reproducibility manifest dosyası (`manifest.json`) üretir (`manifest_schema_version = 1`).

### 12.1 Manifest Alanları
- **`manifest_schema_version`:** Şema sürümü (tamsayı, 1).
- **`tool`:** Aracın adı (`name`) ve sürümü (`version`).
- **`command`:** Kartın §9 Reproduce bölümünde listelenen yeniden üretme CLI komutu (tek kaynaktan).
- **`input`:** Kullanıcının verdiği girdi dosya yolu (`path`), girdi dosyasının SHA-256 bayt özeti (`sha256`), toplam satır sayısı (`rows`) ve kolon sayısı (`columns`).
- **`environment`:** Çalışma ortamı bilgileri (`python` sürümü, `pandas` sürümü, `numpy` sürümü, `platform`).
- **`seed`:** Rastgele sayı üretici tohumu (`seed`).
- **`git`:** Yerel git bilgileri (`commit`: 40-karakter hex commit hash'i, `dirty`: çalışma ağacında commit edilmemiş değişiklik olup olmadığı boolean değeri).
- **`config`:** Kullanılan eşik değerleri (`thresholds`).
- **`outputs`:** Üretilen kart dosyalarının SHA-256 bayt özetleri (`card_json_sha256`, `card_md_sha256`).
- **`warnings`:** Uyarı listesi.

### 12.2 Determinizm ve Zaman Damgası Kuralı
- Manifest hiçbir koşulda tarih veya saat damgası (timestamp) içermez.
- Aynı girdi, seed ve ortamda ardışık çalıştırmalarda üretilen `manifest.json` bayt bayt özdeştir (hash-identical determinism).

### 12.3 Git Erişilemezse Davranış
- Git yüklü olmadığında, `.git` dizini bulunmadığında veya `git` komutları başarısız olduğunda çalıştırma kesintiye uğramaz.
- `git` alanı şu şekilde doldurulur: `{"commit": null, "dirty": null, "reason_code": "not_available"}`.

### 12.4 Kapsam Dışı Maddeler
- `manifest.json` yalnız `modeltrust card` komutu kapsamındadır; `report`, `evaluate` ve `shift` komutları için manifest üretimi kapsam dışıdır.
- Dizin taraması, çoklu fixture toplu hash'i ve kriptografik imzalama bu sürümün kapsamı dışındadır.
