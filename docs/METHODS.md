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
