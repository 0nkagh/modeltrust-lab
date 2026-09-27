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
- **Kapsam ve İçerik:** `tool`, `run_metadata`, `environment`, `input`, `column_spec`, `schema`, `profile`, `leakage` ve isteğe bağlı `split` bloklarını içeren kanonik bir JSON üretir. `--evaluate` argümanı verildiğinde (varsayılan olarak kapalıdır), üst düzey `evaluation` bloğu ve Markdown raporuna `## 9. Model evaluation` bölümü eklenir (davranış `evaluate` komutuyla birebir aynıdır).
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
  - **`coverage_ratio` Tanımı:** `coverage_ratio = n_rows_evaluated / n_rows_scored` olarak hesaplanır. Skorlanan toplam satırlar içinde, asgari grup büyüklüğü eşiğini (`MIN_GROUP_ROWS_FOR_ERROR = 5`) sağlayan ve grup hata sıralamasına dahil edilen geçerli satırların oranını ifade eder.

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

### 8.y Neyi ölçmez
Bu blok kullanıcının modelinin genel performansını ölçmez. `--pred-col` verildiğinde **tüm satırlar** skorlanır, holdout yoktur. Hiperparametre arama, sınıflandırma metrikleri, kalibrasyon ve belirsizlik kapsam dışıdır. OLS ve ortalama baseline yalnız araç içi referanstır.

