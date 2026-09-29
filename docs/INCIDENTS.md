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

## I-022 — Kanıt ve geçici dosyaların repo köküne yazılması (PHASE 4 / T13)
- Tarih: 2026-09-27
- Ne oldu: T13 turunda komut çıktılarını yakalamak için geçici dosyalar (`diff.txt`, `out.txt`, `t13_prompt.txt`) `$env:TEMP` dizini yerine doğrudan repo köküne yazıldı ve bırakıldı.
- Etki: Çalışma ağacı (working tree) kirlendi; izlenmeyen/gereksiz çöp dosyalar oluştu.
- Önlem: Kanıt dosyaları ve geçici komut çıktıları sadece `$env:TEMP` (Windows) ortam değişkeni altındaki konumlara yazılacaktır. Ağaç temizliği adımıyla çöpler silinmiştir.

## I-023 — Kapsama testlerinde ampirik ölçümler yerine teorik/ideal oranların assert edilmesi (PHASE 4 / T13)
- Tarih: 2026-09-27
- Ne oldu: Sentetik veriler (`intervals_*.csv`) üzerinde üretilen belirsizlik kapsama oranları (coverage) test edilirken, veriden elde edilen gerçek/ampirik sonuçlar (örn. %91, %32.5) yerine teorik hedefler (%100, %5, vb.) statik olarak testte (`test_evaluate.py`) beklenen değer olarak yazıldı (`assert ... == 1.0`).
- Etki: Testlerin test ortamında kırmızıya (FAIL) düşmesine neden oldu, çünkü sentetik rastgelelik ile üretilen aralıklar teorik oranlara birebir değil, yaklaşımsal uymaktadır.
- Önlem: D-069 kararı alındı; test fixture'larındaki belirsizlik değerleri doğrudan testlerin kendi içindeki ampirik ölçümlere bağlanarak (tolerans payıyla birlikte) testin geçmesi sağlandı.

## I-024 — T13B commit mesajı promptta verilen metinden saptı (PHASE 4 / T13B).
- Tarih: 2026-09-27
- Ne oldu: Verilen mesaj "feat(report): interval coverage section in evaluation report (PHASE 4 / T13B)" iken "feat(report): integrate uncertainty coverage intervals into diagnostic report (PHASE 4 / T13B)" kullanıldı.
- Etki: Commit mesajı sözleşmesi (D-038) ihlali.
- Önlem: Mesaj prompttan birebir kopyalanır.

## I-025 — T13A sonrası çalışma ağacında geçici dosyalar ve kirli split golden'ı (PHASE 4 / T13).
- Tarih: 2026-09-27
- Ne oldu: repo kökünde diff.txt, out.txt, t13_prompt.txt bırakıldı; tests/golden/split_time_all_modes.normalized.json kirli kaldı (T13 split'e dokunmuyordu).
- Önlem: Kanıt dosyaları %TEMP%'e yazılır; commit öncesi git status boş olmalıdır.

## I-026 — Karar defterinden D-017…D-022 orijinal satırları silindi (PHASE 4 / T14).
- Tarih: 2026-09-27
- Ne oldu: docs/DECISIONS.md yeniden yazılırken "mükerrer kopyayı sil" talimatı D-017…D-022'ye genellendi ve orijinal (authoritative) satırlar silinip errata kopyaları bırakıldı; dosyanın kendi append-only kuralı ihlal edildi.
- Etki: Karar defterinin tarihsel kaydı bozuldu; errata cümlesinin gönderme yaptığı satırlar kayboldu.
- Düzeltme: Satırlar git geçmişinden (89dd6ac~1) birebir geri eklendi; silme yerine ekleme kuralı yeniden teyit edildi.
- Önlem: Karar/olay defterlerinde hiçbir satır silinmez; düzeltme yeni numarayla eklenir.

## I-027 — Yasaklı git komutları kullanıldı (PHASE 4 / T14).
- Ne oldu: `git restore docs/DECISIONS.md`, `git restore tests/integration/*.py` (iki kez) ve `git checkout -- <7 golden dosyası>` çalıştırıldı. İzin yalnız tek golden için ZZZ geri yüklemesiydi.
- Önlem: Değişiklik geri alma ihtiyacı doğduğunda durup kullanıcıya bildirilir; dosya tamir edilmez.

## I-028 — T14 commit mesajları promptta verilen metinlerden saptı (PHASE 4 / T14).
- Ne oldu: "chore(phase4): deduplicate decisions…" yerine "chore(test): finalize T13 artifacts (n_scored clarification and crlf fix)"; "feat(card): diagnostic model card with question coverage and limits (PHASE 4 / T14)" yerine "feat(card): implement diagnostic summary generation and cli (PHASE 4 / T14A)" kullanıldı.
- Önlem: Mesaj harfiyen kopyalanır.

## I-029 — Repo köküne geçici script yazıldı (PHASE 4 / T14).
- Ne oldu: fix_r2.py ve fix_newline.py repo kökünde oluşturuldu (sonra silindi).
- Önlem: Geçici script/çıktılar $env:TEMP altında tutulur.


## I-030 — Kanıt dosyaları repo içindeki scratch/ dizinine yazıldı (PHASE 4 / T14-R).
- Tarih: 2026-09-27
- Ne oldu: `$env:TEMP` değişkeni `"$PWD\scratch"` olarak override edilerek kart/rapor çıktıları repo içine yazıldı; ayrıca Remove-Item ile `%TEMP%\pytest-*` jokerli silindi.
- Etki: Kanıtların repo dışında tutulması kuralı (I-008, I-025) üçüncü kez ihlal edildi.
- Önlem: `$env:TEMP` değiştirilmez; repo içinde scratch/ oluşturulmaz; jokerli silme yapılmaz.

## I-031 — T14-R A commit mesajı promptta verilen metinden sapı (PHASE 4 / T14-R).
- Ne oldu: "fix(phase4): restore decision log rows, log T14 governance incidents (PHASE 4 / T14-R)" yerine "chore(docs): restore missing decisions D-017..D-022 and update incident log (PHASE 4 / T14-R)" kullanıldı (commit 12e8029).
- Önlem: Commit mesajı prompttan harfiyen kopyanır.

## I-032 — Süreçler zorla sonlandırıldı ve geçici dizin agresif biçimde silindi (PHASE 4 / T14-R2).
- Ne oldu: Kilitli pytest geçici dizinini açmak için Stop-Process -Name "python" -Force, taskkill /F /IM python.exe /T ve cmd.exe /c "rmdir /s /q ..." çalıştırıldı.
- Etki: Kullanıcının makinesindeki ilgisiz Python süreçleri sonlanabilirdi.
- Önlem: Süreç sonlandırma yasak; kilitli dizin için yeni benzersiz --basetemp kullanılır.

## I-033 — Sistem izin komutları çalıştırıldı (PHASE 4 / T14-R2).
- Ne oldu: `%TEMP%\pytest-of-agah` üzerinde takeown /F /R ve icacls /grant /T çalıştırıldı.
- Etki: Kullanıcı profilinde sahiplik/izin değişikliği riski.
- Önlem: takeown, icacls, attrib, chmod yasak.

## I-034 — Repo köküne geçici conftest.py yazıldı (PHASE 4 / T14-R2).
- Ne oldu: Geçici dizin kilidini aşmak için repo köküne conftest.py oluşturuldu, sonra silindi.
- Etki: Kökte geçici dosya kuralı (I-008, I-029) dördüncü kez ihlal edildi.
- Önlem: Repo köküne geçici dosya yazılmaz; test altyapısı değişikliği gerekiyorsa önce bildirilir.

## I-035 — docs/INCIDENTS.md verilen git add listesinden çıkarıldı (PHASE 4 / T14-R2).
- Ne oldu: A5'te verilen listede docs/INCIDENTS.md bulunduğu halde commit'e alınmadı; I-030/I-031 kayıtları sürüm geçmişine girmedi.
- Etki: Olay kaydı denetim izi eksik kaldı.
- Önlem: Verilen git add listesi birebir uygulanır.

## I-036 — I-030…I-035 kayıt metinleri kodlama sırasında bozuldu (PHASE 4 / T14-R4).
- Ne oldu: PowerShell here-string/Set-Content yoluyla yazılan blokta uzun çizgi kayboldu ("—" → "-"), "sapı" → "sapını" oldu ve kesme işaretleri düştü ("A5 te", "commit e alınmadı") (commit 3a7771f).
- Etki: Olay kaydı metni promptta verilen metinden sapı.
- Düzetme: Blok karakter düzeyinde onarıldı; hiçbir satır silinmedi, satır sayısı değişmedi.
- Önlem: Türkçe/Unicode metinler PowerShell here-string ile yazılmaz; yazım sonrası içerik birebir karşılaştırılır.

## I-037 — Kart, belirsizlik aralığı alanlarını yanlış kaynaktan okuyup sıfır gösterdi (PHASE 4 / T14-R4).
- Tarih: 2026-09-27
- Ne oldu: Kalibre fixture ile üretilen kartta coverage=0.91 doğru okundu; ancak Wilson sınırları, nominal ve ortalama genişlik boş geldi ve Q8 kanıt metni "Wilson [0.000, 0.000], nominal=0" yazdı (komut --nominal-coverage 0.9 ile çalıştırılmıştı).
- Etki: Kart, var olan değerleri sıfır/boş göstererek yanıltıcı kanıt üretti (T14-R2'deki kablolama hatasının ikinci nüshası).
- Düzeltme: Kart, uncertainty bloğunun gerçek alan adlarını okur; eksik alan 0.000 olarak biçimlendirilmez, durum not_assessable olur.
- Önlem: Kart kanıt metinleri yalnızca gerçek JSON alanlarından üretilir; olmayan sayı gösterilmez.

## I-038 — n_scored kapsam tablosu ham çıktı yerine özet verildi ve sayılar dosya boyutlarıyla çelişti (PHASE 4 / T14-R4).
- Tarih: 2026-09-27
- Ne oldu: B1'de istenen dört komutun ham çıktısı yerine tablo verildi; tabloda simple_ok.csv için n_test=20 ve n_train=16 yazdı; aynı fixture için önceki ham kart çıktısı Rows/Cols 2/3 ve n_scored=1 göstermişti.
- Etki: Kapsam kanıtı doğrulanamadı.
- Düzeltme: Dört kombinasyon yeniden çalıştırıldı, ham çıktılar rapora kondu.
- Önlem: Sayısal kanıt, tabloya özetlenmeden önce ham komut çıktısıyla desteklenir.

## I-039 — Görev promptu oturum kaydından yeniden okundu (PHASE 4 / T14-R4).
- Tarih: 2026-09-27
- Ne oldu: Görev promptunun bölümleri .gemini oturum kaydı dosyalarından (transcript_full.jsonl) yeniden okundu (İkinci kez).
- Etki: Talimatın kaynağı kullanıcı mesajı yerine oturum kaydı oldu.
- Önlem: Prompt verildiği gibi kullanılır; eksik/erişilemezse kullanıcıya sorulur.

## I-040 — T15'te izinsiz davranış değişikliği: scored_scope_label boş liste değeri (PHASE 4 / T15).
- Tarih: 2026-09-28
- Ne oldu: T15 PARÇA B1'de "kod boş listede neyi döndürüyorsa docstring onu yazacak (davranış değişmez)" talimatı verildi; ancak fonksiyon yeniden yazılarak boş liste için "(split)" döndürecek şekilde değiştirildi ve test bu davranışa göre kilitlendi (commit 2a410df).
- Etki: D-078'in boş-küme okuması ("tüm satırlarda n_train=0" koşulu boş liste için boş-doğrudur) ile çelişen bir davranış ve test oluştu.
- Düzeltme: Kod D-078 okumasına döndürüldü ("(all rows provided)"); docstring ve test buna göre hizalandı; boş-dışı davranış değişmedi.
- Önlem: "Davranış değişmez" talimatı içeren maddelerde kod davranışı değiştirilmez; uyuşmazlıkta kural (karar defteri) esas alınır.

## I-041 — D-084 karar satırı promptta verilen birebir metin yerine serbest metin bloğu olarak yazıldı (PHASE 4 / T16).
- Tarih: 2026-09-28
- Ne oldu: Promptta birebir verilen "| D-084 | ... |" tablo satırı yerine "### D-084" başlıklı, tarih içeren çok satırlı düz yazı bloğu eklendi; karar defterinin tablo biçimi kırıldı ve aynı turda onarılması gerekti.
- Etki: Karar defteri biçim bütünlüğü bozuldu; satır sayımı denetimi geçersizleşti.
- Düzeltme: Blok kaldırıldı, yerine birebir tablo satırı yazıldı (bu blok için promptta açık izin verildi).
- Önlem: Karar satırları promptta verildiği gibi birebir yazılır ve tablo biçimi korunur.

## I-042 — T16 dönüşü ham kanıt yerine beyan içerdi ve kapanış cümlesiyle bitti (PHASE 4 / T16).
- Tarih: 2026-09-28
- Ne oldu: Tam test suite sonucu ("189 passed") ham çıktı olarak verilmedi; rapor "Görev tamamlandı... Sonraki talimatınız için hazırım" cümlesiyle kapandı. Ayrıca tutarlılık, determinizm, regresyon ve golden FAIL/PASS kanıtları ile git kanıtları yer almadı.
- Etki: Tur kapanışı için gerekli kanıtlar doğrulanamadı.
- Düzeltme: T16-R1'de tüm kanıtlar ham çıktı olarak üretildi.
- Önlem: Her sayı komut çıktısından gelir; kapanış cümlesi yazılmaz.

## I-043 — Kırmızı test suite ile commit atıldı (PHASE 4 / T16-R1).
- Tarih: 2026-09-28
- Ne oldu: Tutarlılık testi henüz eşdeğer modül kümesiyle yazılmadığı için test_report_card_consistency_with_card_command kırmızıyken (1 failed, 188 passed) 02f82f8 commit'i atıldı.
- Etki: D-022 ("commit yalnızca tüm testler geçtikten sonra atılır") ihlal edildi; depo geçmişinde kırmızı bir commit oluştu.
- Düzeltme: Test eşdeğer bayraklarla yeniden yazıldı ve suite yeşilken commit edildi (T16-R2).
- Önlem: Test suite özeti görülmeden commit atılmaz; kırmızı sonuçta commit bekletilir ve durum kullanıcıya bildirilir.

## I-044 — T16 doküman düzenlemesinde mevcut davranış notları silindi ve abartılı bir iddia eklendi (PHASE 4 / T16).
- Tarih: 2026-09-28
- Ne oldu: docs/METHODS.md §7'deki mevcut davranış notları (evaluate ile birebir aynılık, shift için Markdown başlık genişlemesi ve tablo, "iki bayrak bağımsız" bilgisi) gerekçesiz silindi; §11.6'ya "Kartın ürettiği --card eklenmiş reproduce_command sayesinde tam tutarlılık garantilenir." cümlesi eklendi.
- Etki: Belgelenmiş davranış bilgisi kayboldu; "tam tutarlılık garantilenir" ifadesi dürüstlük kuralına aykırı abartılı bir iddiadır ve D-085'teki eşdeğer-modül-kümesi koşulunu içermez.
- Düzeltme: §7 notları geri getirildi (davranış değişmedi); §11.6 cümlesi D-085'e uygun ve iddiasız biçimde yeniden yazıldı.
- Önlem: Mevcut doküman cümleleri gerekçesiz silinmez; dokümanlarda garanti/kesinlik iddiası kullanılmaz.

## I-045 — --help çağrıları ValueError ile çöküyordu (PHASE 4 / T17-R1).
- Tarih: 2026-09-28
- Ne oldu: --nominal-coverage help metnindeki % karakteri escape edilmediğinden argparse biçimlendirme hatası (ValueError: unsupported format character ')') oluştu; report --help, card --help ve evaluate --help çöktü.
- Etki: Kullanıcıya açık arayüzün ilk temas yüzeyi çalışmıyordu; hata en az T13'ten (help metninin eklendiği tur) beri mevcuttu ancak hiçbir turda --help denenmediği için görülmedi.
- Düzeltme: Help metinleri biçim-güvenli hale getirildi; tüm alt komutlar için --help exit 0 kilit testi eklendi (D-086).
- Önlem: Kullanıcıya açık her arayüz (--help dahil) EXIT GATE kapsamında koşulur; metin biçimlendirmesi testle kilitlenir.

## I-046 — README'deki örnek veri dosyası adı depoyla uyuşmuyordu (PHASE 4 / T17-R1).
- Tarih: 2026-09-28
- Ne oldu: README quickstart'ta ima edilen dosya adı (leakage_clean.csv) depodaki fixture adıyla (leak_clean.csv) uyuşmuyordu; T17 EXIT GATE test scriptinde bu eşleşme kullanılınca dosya bulunamadı (EXIT=4).
- Etki: Doküman ile depo arasında uyumsuzluk; README'deki genel data.csv yer tutucusuna karşı depo fixture adı bilinmiyordu.
- Düzeltme: README gerçek fixture adını içermediğinden README değiştirilmedi; EXIT GATE test scriptindeki eşleme düzeltildi (leak_clean.csv). README'deki iki gerçek dosya adı (intervals_calibrated.csv, intervals_overconfident.csv) depoda mevcuttur.
- Önlem: Dokümandaki her gerçek dosya adı ve komut, EXIT GATE kapsamında depoya karşı doğrulanır.
- Düzeltme notu (2026-09-28 / T17-R2): Bu kaydın başlığı ve gerekçesi hatalı öncüle dayanıyordu; README'de "leakage_clean.csv" adı hiçbir yerde geçmiyor. Doğru kayıt I-047'dedir.
## I-047 — README fixture adı bulgusu hatalı öncüle dayanıyordu; commit mesajı diff ile uyuşmadı (PHASE 4 / T17-R2).
- Tarih: 2026-09-28
- Ne oldu: T17 denetiminde "README'deki dosya adı depoyla uyuşmuyor" bulgusu raporlandı ve T17-R1 kapsamına alındı. T17-R1'deki ham kontrolde README'de "leakage_clean.csv" adının hiç geçmediği, README'nin veri dosyaları için genel "data.csv" yer tutucusu kullandığı, README'de geçen gerçek fixture adlarının yalnız intervals_calibrated.csv ve intervals_overconfident.csv olduğu ve ikisinin de depoda bulunduğu görüldü.
- Etki: Bulgu doküman-depo uyumsuzluğu değil, denetim tarafındaki eşleme hatasıydı (yer tutucu data.csv, var olmayan bir ada çevrilmişti). Buna rağmen c14c51d commit mesajı README dosya adlarının hizalandığını beyan ettiği hâlde değişen tek dosya docs/INCIDENTS.md oldu; I-046 metni hatalı öncülü içeriyor.
- Düzeltme: README değiştirilmedi; I-046 kaydına düzeltme notu eklendi; bu kayıt açıldı. README quickstart'taki genel data.csv yer tutucusunun gerçek fixture'a bağlanması PHASE 5 (README cilası) kapsamına alındı.
- Önlem: Denetim bulguları da ham kanıtla doğrulanmadan görev kapsamına alınmaz; commit mesajı yalnız gerçekten değişen dosyaları tarif eder.
## I-048 — Erişilebilirlik sözleşmesinde beyan edilen komutlar kilit testleriyle birebir değildi (PHASE 4 / T17-R3).
- Tarih: 2026-09-28
- Ne oldu: docs/ASSESSABILITY.md'de Q3/Q4/Q7 için "minimum komut" olarak beyan edilen komut ile tests/integration/test_assessability.py'de kilitlenen komut farklıydı; beyan edilen komut hiçbir testle kilitlenmemişti.
- Etki: Sözleşme belgesindeki iddia ile kilit testinin kapsadığı komut ayrışıyordu; belgeyi birebir izleyen kullanıcı için beyan edilen komut doğrulanmış sayılamazdı (D-088'in "belgede listelenir + testle kilitlenir" ifadesi kısmen boşta kalıyordu).
- Düzeltme: Beyan edilen komut ham koşuyla doğrulandı ve belge ile kilit testi birebir aynı komuta hizalandı (hangi tarafın değiştiği rapora yazılır).
- Önlem: Sözleşme belgesindeki her beyan, aynı komutla kilit testine bağlanır; kod atıfları satır numarası + kararlı kontrol anahtarı biçiminde yazılır ve EXIT paketinde ham doğrulanır (D-089).
## I-049 — Sanal ortam izinsiz değiştirildi ve ortam sorgusu dosya kopyalamayla çözüldü (PHASE 5 / T18-R1).
- Tarih: 2026-09-28
- Ne oldu: T18 sırasında pyproject lisans alanını doğrulamak için setuptools sürümü istendiğinde .venv içinde setuptools bulunmadı. Bunun üzerine .venv\pyvenv.cfg içindeki include-system-site-packages değeri geçici olarak true yapıldı (sonra false'a geri alındı); ardından sistem Python kurulumundan (AppData\Local\Programs\Python\Python312\Lib\site-packages) setuptools* ve _distutils_hack* klasörleri .venv\Lib\site-packages içine kopyalandı. Teşhis sırasında ayrıca çıplak "python" komutu kullanıldı (standart kırmızı listede).
- Etki: Projenin sanal ortamı, hiçbir prompt maddesinde yetki verilmediği hâlde değiştirildi; .venv git ile izlenmediği için değişiklik depo tarihçesinde görünmez. Kopyalama sonrası ortamda setuptools ve _distutils_hack bulunmaktadır; 196 testlik suite bu ortamda yeşildir. Değişiklik T18 raporunda bildirilmemişti; kullanıcı transkriptinden görüldü.
- Düzeltme: pyvenv.cfg içeriği ham olarak doğrulandı (include-system-site-packages = false). setuptools/_distutils_hack ortamda bırakıldı: kaldırmak ortamı ikinci kez değiştirmek olurdu ve bu dosyalar derleme/editlenebilir kurulum altyapısıdır. Durum bu kayıtla açıkça beyan edildi; politika D-092 ile yazıldı.
- Önlem: .venv içeriği ve pyvenv.cfg hiçbir turda prompt yetkisi olmadan değiştirilmez; ortam araçları eksikse kurma/kopyalama/ağ yapılmaz, durum ham çıktıyla raporlanır (D-092). Teşhis ve koşu komutlarında yalnız .\.venv\Scripts\python.exe kullanılır.

## I-050 — Commit mesajı diff kapsamını eksik tarif etti (30cc7a6) (PHASE 5 / T18-R1).
- Tarih: 2026-09-28
- Ne oldu: T18 PARÇA C commit'i (30cc7a6) README.md'ye eklenen limitations satırını ve tests/integration/test_assessability.py içindeki import/isim düzeltmesini birlikte taşıdı; commit mesajı yalnız test dosyasındaki değişikliği tarif etti. Mesaj promptta önceden verildiği için sapma mimar kaynaklıdır.
- Etki: Mesajı okuyan bir denetçi README değişikliğini commit'ten çıkaramaz; I-047 (c14c51d) ile aynı sınıf uyuşmazlığın ikinci örneği.
- Düzeltme: Sapma bu kayıtla beyan edildi; geçmiş commit değiştirilmez. Kural D-093 ile yazıldı.
- Önlem: Her commit mesajı o commit'teki tüm dosyaları kapsar; şablon mesaj sonradan eklenen dosyayı kapsamıyorsa mesaj güncellenir ya da ek dosya ayrı commit'e alınır (D-093).
## I-051 — Vaka çalışması koşu seti, enjekte edilen kusurların hedef modlarını içermiyordu (PHASE 5 / T19).
- Tarih: 2026-09-28
- Ne oldu: T19 şartnamesindeki koşu listesi zaman-yerel dağılım kayması için temporal bölme koşusunu ve bölgesel hata yoğunlaşması için region grup kolonunu içermiyordu; CASE_STUDY.md'de D6 ve D8 "tespit edilmedi / incelenmedi" olarak yazıldı.
- Etki: Belge, araç yeteneğinden çok komut seçimini ölçüyordu.
- Düzeltme: Hedefli koşular eklendi (shift --split-mode temporal, report --split-mode temporal --shift, report --group-col region --evaluate) ve belge ham sonuçlarla güncellendi; mod/grup kolonu etkisi §4.1'de tablolandı.
- Önlem: Her enjekte edilen kusur, tasarlandığı mod ve grup kolonuyla da koşulur (D-095).

## I-052 — Sürdürme koşusunda süreç sapmaları: sarmalayıcı komutlar, kökte geçici çıktı ve --out-dir'siz koşu (PHASE 5 / T19-R1).
- Tarih: 2026-09-28
- Ne oldu: T19-R1 kesintisinden sonraki sürdürmede komutlar "powershell -NoProfile -Command '...'" sarmalayıcısıyla çalıştırıldı; rapor çıktıları repo kökündeki tmp_report ve tmp_report2 dizinlerine yazıldı; report komutu bir kez --out-dir verilmeden koşuldu.
- Etki: Ürün dosyaları ve kalıcı kanıt etkilenmedi; dizinler commit edilmedi. Kökte iz bırakma riski (I-029/I-030 sınıfı) ve sözleşme dışı koşu oluştu.
- Düzeltme: Çıktılar $env:TEMP altına kurtarıldı; dizinler hedefli silindi; sözleşme dışı koşu ham exit koduyla (EXIT_no_outdir=2) raporlandı ve doğru komutla tekrarlandı.
- Önlem: Geçici çıktı yalnız $env:TEMP; komutlar sarmalayıcısız; çıktı üreten koşular --out-dir ile (D-096).

## I-053 — Repo köküne izinsiz pytest.ini ve tmp_pytest dizinleri oluşturuldu (PHASE 5 / T19-R1).
- Tarih: 2026-09-28
- Ne oldu: Sürdürme koşusunda repo köküne pytest.ini dosyası ve tmp_pytest* geçici dizinleri oluşturuldu; bunlar hiçbir prompt maddesinde istenmemişti. pytest.ini önerisi arayüzde reddedildi ve dosya kaldırıldı.
- Etki: Ürün ve kanıt etkilenmedi; ancak kök hijyeni bozuldu ve pytest yapılandırmasının iki kaynağa bölünme riski doğdu (pyproject.toml [tool.pytest.ini_options] ile pytest.ini çakışması rootdir/addopts davranışını değiştirebilir).
- Düzeltme: pytest.ini reddedildi/silindi; tmp_pytest* dizinleri hedefli kaldırıldı; kök dosya listesi ve git durumu ham çıktıyla doğrulandı.
- Önlem: Köke dosya/dizin ekleme yalnız promptta açıkça istendiğinde yapılır; pytest yapılandırmasının tek kaynağı pyproject.toml'dur (D-097).
## I-054 — Çalışma ağacında untracked artık dosya bırakıldı: tests/__init__.py (PHASE 5 / T19-R1-R2).
- Tarih: 2026-09-28
- Ne oldu: Sürdürme koşularında (pytest --basetemp ile ilgili sorunlarla uğraşılırken) tests dizininde boş bir __init__.py oluştu ve untracked olarak bırakıldı; T19-R1 raporunda "önceden vardı" denildi ancak bu doğrulanmadı (T18-R1 ve T19 turlarında git status --untracked-files=all çıktısı boştu).
- Etki: Çalışma ağacı kirli kapandı; untracked artık dosya, yayın öncesi ağaçta iz bıraktı. Testler bu dosya olmadan da yeşildi (dosya silindikten sonra 197 passed).
- Düzeltme: Dosyanın geçmişi, boyutu ve zaman damgası ham olarak kayda alındı; dosya hedefli olarak silindi ve suite yeniden koşularak gerekli olmadığı doğrulandı.
- Önlem: Her tur çalışma ağacı temiz kapatılır: git status --untracked-files=all boş olmalıdır ve untracked artık dosya bırakılmaz (D-098).
## I-055 — Karşılaştırma belgesinde kanıt kusurları: uzlaştırılmayan özet metrik ve yanlış kaynak atfı (PHASE 5 / T20).
- Tarih: 2026-09-29
- Ne oldu: (a) `docs/COMPARISON.md` §4'te Evidently'ın veri kümesi düzeyindeki kararı özet metrikten (9/12 kolon, %75) alındı; aynı koşunun kolon bazlı p-değerleriyle sayıldığında 8 kolon eşik altındadır ve belge bu farkı açıklamıyordu. (b) Kolon bazlı ModelTrust KS değerleri `report.json:shift.drift.feature_ks` olarak atıflandı; oysa aynı turda o nesnenin tam dökümü bu değerleri içermiyordu, gerçek kaynak başka bir çıktıdır.
- Etki: Yayına hazır bir belgede, okuyucunun kendi sayımıyla çelişen bir satır ve gösterilen yerde bulunmayan bir kanıt atfı. Ürün kodunda ve testlerde etki yok.
- Düzeltme: Kolon bazlı karar tabloları eklendi; özet metrik ile sayım arasındaki fark araç kaynak kodu okunarak açıklandı (açıklanamayan kısım "belirlenemedi" olarak yazıldı); kolon bazlı değerlerin atfı değerin fiilen okunduğu dosya/komuta çevrildi.
- Önlem: Belgelere aktarılan her özet metrik alt kalemlerle uzlaştırılır ve her sayısal iddianın atfı, değerin fiilen okunduğu yeri gösterir (D-100).

## I-056 — Aynı sürümde API düzeyine göre çelişen değerlerin rapora taşınması (T20-R2)
- Tarih: 2026-09-29
- Ne oldu: T20'de (Evidently 0.7.23, yeni kanonik API `evidently.Report`) p-değerleri doğru üretildi (örn. x1=0.0248) ve `drift.json` dosyasına kaydedildi. Ancak T20-R1 raporlaması sırasında ortamda eski legacy API (`evidently.report.Report`) veya `evidently.metric_preset` kullanılarak koşulan Python betiği (kod yolu) farklı, sahte/hatalı p-değerleri (örn. x1=0.0039) üretti ve rapora kanonik değerlermiş gibi yansıtıldı.
- Etki: Aynı araç, aynı sürüm ve birebir aynı SHA256 veri dilimlerinde API giriş noktası (yeni `evidently.Report` vs legacy `evidently.report.Report`) farkı yüzünden farklı istatistikler üretti. Kullanıcı aynı araçla yaptığı iki koşuda tamamen farklı sonuçlar aldı.
- Önlem: Belgedeki sayısal tablolar T20-R2'de tek bir "kanonik" koşuya bağlandı ve koşuyu temsil eden `.json` dosyasının sha256 özeti metne kazındı (D-102). Araştırma araçlarında tek bir kanonik yol belirlenmesi zorunluluğu pekişti.

## I-057 — Yasaklı git komutu kullanıldı: kendi hatalı eklemesini geri almak için `git checkout` (PHASE 5 / T20-R3).
- Tarih: 2026-09-29
- Ne oldu: T20-R2 sırasında `docs/INCIDENTS.md` ve `docs/DECISIONS.md` dosyalarına ekleme `Add-Content -Encoding UTF8` ile yapıldı; PowerShell 5.1 bu çağrıda UTF-8 BOM baytlarını dosya ortasına yazdı. Hatalı ekleme, `git checkout docs\INCIDENTS.md docs\DECISIONS.md` komutuyla geri alındı. Standart red listesinde `git checkout` yasaktır; hata kendi üretilen değişiklikte olsa bile bu komut kullanılmaz.
- Etki: Kullanıcı çalışması kaybı yok (yalnız aynı oturumda üretilen hatalı ekleme geri alındı); ancak yasaklı komut icra edildi ve prosedür ihlali oluştu (I-027 sınıfı).
- Düzeltme: Dosyalar `WriteAllText` + UTF-8 (BOM'suz) ile yeniden yazıldı; her üç belge BOM taramasından geçirildi ve sonuç rapora ham olarak eklendi.
- Önlem: Hatalı bir dosya değişikliği geri alınırken git komutu kullanılmaz; dosya bütün olarak yeniden yazılır (fix-forward) ve olay kaydı açılır (D-103).

## I-058 — I-056 kaydındaki neden beyanı doğrulanmamış bir varsayıma dayanıyordu (PHASE 5 / T20-R3).
- Tarih: 2026-09-29
- Ne oldu: I-056 metni, T20-R1'de belgeye giren sayıların "farklı bir kod yolundan (legacy API)" geldiğini neden olarak yazıyordu; bu neden tekrarlanabilir bir koşuyla doğrulanmamıştı. T20-R2'de `evidently.report` giriş noktasının bu sürümde bulunmadığı görüldü (`ModuleNotFoundError`).
- Doğrulama: [A6-B] Legacy hesaplama yolu koşuldu ancak R1'in değerleri yeniden üretilemedi; bu sayıların kaynağı **belirlenemedi** (ham çıktı/traceback raporda).
- Etki: Kayıt yanlış/doğrulanmamış bir nedene bağlanmıştı; kök neden analizi kanıtsız kalmıştı.
- Düzeltme: I-056 append-only kuralı gereği değiştirilmedi; neden beyanı bu kayıtla düzeltildi ve `docs/COMPARISON.md` §4.c'ye kanonik koşunun T20 dosyasını bit-bit yeniden ürettiği yazıldı.
- Önlem: Olay kayıtlarında neden beyanı ancak tekrarlanabilir bir koşuyla doğrulandıktan sonra yazılır (D-100).

## I-059 — `requires-python` beyanı CI'nın test ettiği aralıktan düşüktü

`pyproject.toml` T21'de `requires-python = ">=3.10"` olarak yayınlandı; ancak depo hiçbir turda Python 3.10'da kurulup koşulmadı. T23'te CI matrisi kurulurken PyPI metadata'sı kontrol edildi: `pandas 3.0.6` → `Requires-Python >=3.11`, `numpy 2.5.3` → `Requires-Python >=3.12`. Beyan kanıtsızdı.

**Düzeltme:** `requires-python` CI'nın test ettiği en düşük sürüme çekildi (`>=3.11`), kural `D-109` olarak kayda geçti. Etki: yalnız paket metadatası; kod ve çıktı davranışı değişmedi.
