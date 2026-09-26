# Olay Kayıtları

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
