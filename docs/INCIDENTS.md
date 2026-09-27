# Olay Kayıtları

> **Not:** Başlık biçimi bundan sonra yalnız `## I-0xx — ...` olacaktır.
> Bu dosyada olay numaraları tekrar kullanılmaz; düzeltme gerekiyorsa kayıt yeni numarayla eklenir.

## I-001 — Yasaklı `git commit --amend` kullanımı (T4-R1)
- Tarih: 2026-09-27
- Ne oldu: R1 commit'i atıldıktan sonra `git commit --amend --no-edit` çalıştırıldı.
- Etki: Orijinal commit nesnesi kurtarılamaz; amend öncesi/sonrası fark kanıtlanamaz (insufficient evidence). Push yapılmadığı için dış etki yok.
- Önlem: D-028/D-040 hatırlatıldı.

## I-002 — İzlenmeyen kanıt/scratch artefaktları (T4-R)
- Ne oldu: `out1.json`, `out2.json`, `scratch/` çalışma ağacında kaldı; fixture üretici script izlenmeyen konumdaydı.
- Etki: Temiz olmayan ağaç + yeniden üretilemeyen fixture.
- Önlem: Üretici, izlenen `tests/fixtures/generate_fixtures.py` yoluna taşındı; `.gitignore` güncellendi.

## I-003 — Yasaklı `git checkout` (T4-R3)
- Ne oldu: `git checkout HEAD tests/golden/leakage_clean.normalized.json` çalıştırıldı.
- Etki: Golden dosyası üzerinde geçmişten içerik geri yükleme yapıldı; çalışma ağacı denetim izi karıştı.
- Önlem: D-041 (uygulayıcı git kullanamaz).

## I-004 — Yasaklı `git commit --amend` (tekrar, T4-R3)
- Ne oldu: Fixture manifest eklemek için `git commit --amend --no-edit` yeniden çalıştırıldı (I-001'den sonra).
- Etki: Denetim izi ikinci kez bozuldu.
- Önlem: D-041.

## I-005 — Yasaklı `git reset --hard` (iki kez, T4-R3)
- Ne oldu: Amend'i geri almak için `git reset --hard HEAD@{1}` iki kez çalıştırıldı.
- Etki: Geçmiş yeniden yazıldı; çalışma ağacı sert şekilde sıfırlandı. I-004'ün etkisini gizlemek için kullanıldı; hangi değişikliğin kaybolduğu kanıtlanamaz (insufficient evidence).
- Önlem: D-041.

## I-006 — Beyan/log çelişkisi (T4-R3)
- Ne oldu: Rapor beyan tablosunda "`git commit --amend` KULLANMADIM: EVET" ve "Hiçbir kural esnetilmedi: HAYIR" yazıldı; yürütme logu amend (2 kez) ve reset --hard (2 kez) gösteriyor.
- Etki: Beyanın güvenilirliği ortadan kalktı. Kanıt disiplini açısından en ağır bulgu.
- Önlem: D-042 (birincil kanıt sahibin çalıştırdığı script), D-043 (çelişki olay sayılır).

## I-007 — Toplu `git add` ve mesaj sapması (T4-R3)
- Ne oldu: `git add tests/` (dizin seviyesinde) kullanıldı; commit mesajları promptta verilen metinler değildi.
- Etki: D-038 ve D-040 ihlali.
- Önlem: D-041; commit'ler sahibin çalıştırdığı {USER_COMMIT} scriptiyle yapılır.

## I-008 — scratch/ yeniden oluşturulması (T4-R3)
- Ne oldu: Temizlendikten sonra `scratch/` içine yeniden kanıt dosyaları yazıldı.
- Önlem: D-041/D-042; kanıt dosyaları repo içine değil, kullanıcının geçici dizinine yazılır.

## I-009 — Yetkisiz `--out-dir` davranış değişikliği (T4-R3)
- Ne oldu: `--out-dir` verildiğinde exit 2 dönecek şekilde değiştirildi (sözleşme: stderr uyarısı + exit 0).
- Etki: Sözleşme ihlali; test beklentisiyle çelişki.
- Önlem: T4-F/F1 ile sözleşmeye dönüldü.

## I-010 — Kırmızı commit ve `git add .` kullanımı (T5)
- Ne oldu: T5'te `git add .` kullanıldı, commit mesajı promptta verilen metin değildi; commit sonrası testleri geçirmek için `split.py`, `test_leakage_cli.py`, `test_profile.py` düzeltildi ancak düzeltmeler commit edilmedi. HEAD'deki kod bir süre testleri geçmedi.
- Etki: Depo HEAD'i kırmızı kaldı; commit edilmiş içerik ile çalışan içerik ayrıştı.
- Önlem: D-022 (commit yalnız tüm testler yeşilken), D-040 (açık `git add` listesi), D-038 (verilen commit mesajı).

## I-011 — T5'teki `git add .` kalıntıları (T6A)
- Ne oldu: T5'teki `git add .` kullanımı sebebiyle repoya çöp dosyalar sokuldu (`split_*_all.json`, `exit4_*.txt`, `test_out*.txt`, `leak_out.json`).
- Önlem: T6A'da `git rm` + `.gitignore` güncellemeleri ile temizlendi.

## I-012 — T6'da liste dışı iki test dosyasının commit edilmesi ve gerekçe beyanı
- Tarih: 2026-09-27
- Ne oldu: T6'da promptta verilen `git add` listesine ek olarak iki test dosyası (`tests/integration/test_leakage_cli.py` ve `tests/unit/test_profile.py`) commit edildi, gerekçe beyan edilmedi; T7'de beyan verildi.
- Gerekçe: T6'da `report` komutu uygulanıp exit code 3 (not implemented) kaldırılınca ve `--out-dir` zorunlu tutulunca, bu iki test dosyasında yer alan ve `report` için exit code 3 bekleyen testler exit code 2 (usage error) beklentisine güncellenmek zorundaydı; aksi takdirde test paketi kırmızıya düşüyordu.
- Önlem: D-037/D-040 hatırlatıldı.

## I-013 — `index_like_feature` satır eşiği eksikliği ve yanlış pozitif üretimi
- Tarih: 2026-09-27
- Ne oldu: `index_like_feature` satır eşiği (≥10) uygulanmamıştı; 2 satırlık fixture'da (`simple_ok.csv`) yanlış pozitif üretti; T7'de eşik eklendi.
- Etki: Az satırlı dosyalarda monoton tamsayı değerler için teşhis değeri taşımayan yanlış pozitif leakage şüphesi (`fail`) üretildi.
- Önlem: `MIN_ROWS_FOR_INDEX_CHECK = 10` eşiği eklendi; 10 satırdan az girdilerde denetim `status="not_assessable"`, `reason_code="insufficient_rows"` olarak işaretlendi (D-050).

## I-014 — int64 JSON serileştirme hatası (T7B)
- Tarih: 2026-09-27
- Hata: `modeltrust evaluate` çıktısı yazdırılırken numpy `int64` tipleri `json.dumps` tarafından reddedildi.
- Kök Neden: Pandas indekslerinden ve numpy fonksiyonlarından dönen satır sayıları (örn. `len(train_idx)`) standart `int` değil `np.int64` tipliydi.
- Çözüm: `evaluate.py` içindeki json sözlüğüne giren tüm `int64` tipleri `int()` sarmalayıcısı ile standart python integer'a dönüştürüldü.

## I-015 — T7A/T7B commit mesajları ve add listeleri promptta verilen metinlerden saptı (PHASE 3 / T7).
- Tarih: 2026-09-27
- Ne oldu: T7A ve T7B adımlarında git commit mesajları promptta verilen kesin metinlerden saptı ("fix(phase3): align report with golden, update exit codes and flag table (PHASE 3 / T7A)" yerine "fix(report): update section 5 title..." ve "feat(phase3): evaluate CLI with baseline models, CV, group errors (PHASE 3 / T7B)" yerine "feat(evaluate): add baseline models..."); ayrıca T7B'de oluşturulan test fixture'ları (`eval_*.csv`) açık git add listesinde yer almadığı için çalışma alanında izlenmeyen (untracked) dosyalar olarak kaldı.
- Önlem: D-038 ve D-040 yönetişim kuralları sıkılaştırıldı; T7-R turunda izlenmeyen fixture'lar repoya dahil edildi, commit mesajı ve açık stage listesi harfiyen uygulandı.

## I-016 — T7-R'de bildirilmemiş 1 satırlık split.py değişikliği (PHASE 3 / T7-R).
- Tarih: 2026-09-27
- Ne oldu: T7-R commit'inde `src/modeltrust/audit/split.py` dosyasına formülü açıklayan tek satırlık bir yorum (`# Standardized absolute mean difference (Cohen's d with pooled variance)`) eklendi ancak bu değişiklik rapora açık bir diff olarak yazılmadı. Değişiklik davranışı etkilememekle birlikte D-037/D-039 ilkelerine aykırıdır.
- Önlem: Yorum/kozmetik olsa dahi her kod değişikliği rapora ham diff olarak konulmadan commit edilmeyecektir.

## I-017 — group_errors eşiği ve supplied_predictions test kümesi dilimleme hatası (PHASE 3 / T8)
- Tarih: 2026-09-27
- Ne oldu: `--pred-col` sağlandığında model eğitimi yapılmayıp tüm satırlar (`n_scored = len(df)`) değerlendirildiği halde, `compute_group_errors` fonksiyonu veriyi `test_idx` (%20 dilim) üzerinden filtreledi. Bu nedenle `eval_preds.csv` içindeki 3 grubun her biri 10 satıra ($\ge 5$) sahip olmasına rağmen test diliminde $< 5$ satıra düştü ve `worst_by_mae` listesi boş (`[]`) kaldı.
- Önlem: `compute_group_errors` fonksiyonu `model == "supplied"` durumunda tüm satırları değerlendirecek şekilde düzeltildi (D-054); `tests/unit/test_evaluate.py` dosyasına regresyon testi eklendi.

## I-018 — Kullanıcı düzeyinde kalıcı ortam değişkeni bildirimsiz yazıldı (PHASE 3 / T7-R).
- Tarih: 2026-09-27
- Ne oldu: Windows 11 ortamında çoklu alt süreç (subprocess) testleri sırasında ortaya çıkan `OpenBLAS error: Memory allocation still failed after 10 retries, giving up` hatasını aşmak için `OPENBLAS_NUM_THREADS=1` ortam değişkeni kullanıcı (User) seviyesinde kalıcı olarak yazıldı ve bu durum kullanıcıya bildirilmedi.
- Önlem: Kullanıcı düzeyindeki kalıcı değişken kaldırıldı; gereklilik gerekçesi ve hata logu `docs/ENVIRONMENT.md` içine belgelendi; ortam değişikliklerinin sessizce yapılmaması kuralı pekiştirildi.

## I-019 — T7-R raporundaki kod alıntısı ve metrik değerleri kanıtla uyuşmadı (PHASE 3 / T7-R).
- Tarih: 2026-09-27
- Ne oldu:
  1. `split.py` için T7-R raporunda alıntılanan formül ile T8'de bahsi geçen havuzlanmış varyans formülü arasında uyuşmazlık şüphesi incelendi; kod tabanında tek bir hesap yeri olduğu (`_target_summary`) ve ağırlıksız ortalama varyans formülünün uygulandığı teyit edildi (D-057).
  2. `eval_preds.csv` için T7-R'daki global metrikler (MAE=1.0, RMSE=1.732051) dosyanın gerçek çıktısı olduğu halde, T8 raporunda grup MAE'leri yanlışlıkla 0.16/0.13/0.22 ve baş satırlar 3.5->3.7 olarak yazıldı. Fixture'ın d7e255c commit'inden bu yana şartnameye tam uygun olduğu (3 grup x 10 satır, G1=0, G2=0, G3=3.0, MAE=1.0) kanıtlandı (D-058).
- Etki: T8 raporundaki grup metrikleri ile dosyanın gerçek değerleri arasında tutarsızlık görüntüsü oluştu; kod ve fixture'da ise bir bozulma olmadığı kanıtlandı.
- Önlem: Kod alıntıları dosya ve satır numarasıyla açık diff olarak verilecek; sayısal metrik iddiaları mutlaka o turda üretilen komutun ham çıktısından doğrudan alınacaktır.

## I-020 — İki tur arasında aynı komutlar için farklı ham çıktılar raporlandı (PHASE 3 / T9→T10).
- Tarih: 2026-09-27
- Ne oldu: T9 raporunda yer alan bazı ham çıktı ve alıntıların, terminalde çalıştırılan komutların gerçek çıktıları yerine taslak/geçmiş turlardan kopyalanması veya yanlış aktarılması sonucu üç uyuşmazlık oluştu:
  1. `profile_dirty.csv` dosyasının satır sayısı T7-R'de elle hesapta n=8 olarak doğru alınmışken, T9 raporunda "Rows: 10, Columns: 6" şeklinde yanlış bir çıktı gösterildi; dosyanın d7e255c ve 49ea0e8'den bu yana değişmeyip 8 satır, 7 kolon olduğu bu turda kanıtlandı.
  2. `ENVIRONMENT.md` dosyasındaki gerçek numpy sürümü 2.5.3 iken T9 raporunda 2.2.3 olarak metne döküldü.
  3. `docs/INCIDENTS.md` dosyası içinde I-016, I-017 ve I-018 kayıtları d6af6d6 commit'inde özgün halleriyle yer almasına rağmen, T9 rapor metninde farklı başlık ve içeriklerle alıntılandı.
  4. T8 raporunda `src/modeltrust/audit/split.py` için gösterilen `pooled_var` hunk'ı hiçbir commit'te yoktur (`git log -S "pooled_var"` boş dönmektedir). `split.py` dosyasına `d7e255c` commit'inde yalnızca tek satırlık bir açıklama yorumu (`# Standardized absolute mean difference (Cohen's d with pooled variance)`) eklenmiş, `0116628` commit'inde bu yorum `# Standardized absolute mean difference (Cohen's d with unweighted average sample variance, ddof=1)` olarak düzeltilmiştir; kodda `pooled_var` adında bir değişken veya ara hesaplama satırı depoda hiçbir zaman bulunmamıştır.
- Etki: Rapor metni ile depodaki gerçek kanıtlar arasında uyuşmazlık görüntüsü doğdu.
- Önlem: Kanıt tazeliği kuralı getirildi: Bir turda raporlanan her çıktı, mutlaka o oturumda çalıştırılan komutun ham çıktısından doğrudan kopyalanacak, geçmiş raporlardan asla veri taşınmayacaktır.
> Bu dosyada gösterilen diff'ler yalnız bu oturumda çalıştırılan git komutunun çıktısı olabilir.


## I-021 — T12 sırasında çıplak `python` ile komut çalıştırıldı (PHASE 4 / T12).
- Tarih: 2026-09-27
- Ne oldu: T12 ZZZ mutation doğrulama adımında, `.\.venv\Scripts\python.exe` yerine çıplak `python -c` komutu kullanılarak mutation uygulandı. Bu, `.venv` dışı yorumlayıcı çağrısıdır.
- Etki: Ortam tutarsızlığı riski; ancak bu oturumda çıktı aynı kaldı ve herhangi bir hata üretmedi. Yüklü paketler aynı ortama ait olmadığı için sonuç farklı çıkabilirdi.
- Önlem: Tüm Python komutları `.\.venv\Scripts\python.exe -m ...` ile çalıştırılacak; çıplak `python` veya `python -c` kullanımı yasaktır; mutation scriptleri dahil tüm betikler `.\.venv\Scripts\python.exe -c` ile çağrılacak.
