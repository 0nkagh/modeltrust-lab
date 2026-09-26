# Yöntemler ve Eşik Gerekçeleri

## Kapsam Dışı Bırakılanlar
Aşağıdaki sızıntı türleri statik denetim (yalnızca CSV) aracılığıyla güvenilir bir şekilde tespit edilemeyeceği için kasıtlı olarak kapsam dışı bırakılmıştır:
- Preprocessing ve Feature Engineering sırasında yaşanan sızıntılar
- Örnekleme bias'ı (Sampling bias)
- Etiket gürültüsü (Label noise)
- Veritabanı "join" işlemlerinden kaynaklı sızıntılar
- Temporal nedensellik ihlalleri (gelecekten geçmişe sızıntı)

## 1. Hedef Kolon Kopyası Şüphesi (Target Copy Suspicion)
- **Ne Ölçer:** Herhangi bir özelliğin (feature) hedef değişken (target) ile tam olarak aynı olup olmadığını.
- **Nasıl Ölçer:** Hedef kolon ile feature arasındaki farkların (nümerik için) `eps=1e-5`'ten küçük olup olmamasına veya string/kategorik için birebir eşleşme oranının > 0.999 olmasına bakar.
- **Eşik Gerekçesi:** 0.999; küçük yuvarlama hataları veya tesadüfi 1-2 farklılık (kirlilik) haricinde tamamen aynı olan kolonları yakalamak için.

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
  - **Yuvarlama Kuralı:** Test kümesi boyutu 
_test = int(round(test_size * n)) ile belirlenir ve en az 1, en fazla 
-1 olacak şekilde sınırlandırılır (clamp).
  - **Random Split:** Yöntem olarak 
umpy.random.default_rng(seed).permutation kullanılır. **Tekrarlanabilirlik kapsamı:** Sadece aynı ortam ve aynı numpy sürümü (D-010); numpy sürümleri arası kararlılık garanti edilmez.
  - **Group Split (Greedy):** Gruplar; satır sayısı azalan, grup adı ise artan sırada sıralanır. Test kümesi 
_test hedefine ulaşana kadar gruplar sırayla eklenir. Deterministik bir yaklaşımdır.
  - **Temporal Split:** Veri, zaman kolonu ve ardından orijinal satır indeksine göre sıralanarak ayrılır.
