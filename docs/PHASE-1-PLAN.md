# ModelTrust Lab / ML Assurance Lab · PHASE 1: Keşif ve Planlama Raporu

Bu planın kabul durumu: koşullu kabul; düzeltmeler C1–C7 uygulanmıştır.

## Uygulanacak düzeltmeler (C1–C7)

- **C1:** 4 haftalık plan yalnızca PHASE 2'yi kapsar (T1–T6). Hafta 4, PHASE 3 işini (baseline model, GroupKFold, MAE/RMSE/R²) plana çekmez; PHASE 3, Hafta 5'te ayrı bir "exit gate" kararıyla başlar.
- **C2:** DoD'de "%100 yakalama" ifadesi kaldırılır. Yerine: "Bilerek eklenmiş ve dokümante edilmiş leakage kalıpları (hedef-kolon kopyası, train/test satır çakışması, grup çakışması) synthetic fixture'larda flag'lenir. Bu kalıpların dışındaki durumlar için tespit davranışı 'current scenarios tested' düzeyindedir ve bilinen limitasyon olarak rapora yazılır."
- **C3:** Determinizm boşlukları D-007/D-008/D-009/D-010 ile kapatılır (timestamp politikası, NaN/Inf temsili, seed parametreleştirme, determinizm iddiasının kapsamı, `set` kullanımının yasaklanması).
- **C4:** Mimari boşlukları kapatılır: `schema.py` (T2), `provenance.py` (T3), `synthetic.py` (T5), kontrol durum modeli (D-012). `audit/drift.py` PHASE 2 ağacından çıkarılır (PHASE 4).
- **C5:** Proje-yerel `.venv` zorunlu; "global paket zaten kurulu" gerekçesi geçersiz; CLI çerçevesi `argparse`.
- **C6:** Risk listesi tamamlanır: her maddeye "erken sinyal" alanı eklenir; ayrıca şu riskler eklenir: Türkçe yerel ayar (`;` ayırıcı / virgül ondalık), UTF-8 BOM / `\ufeff` kolon adı, çevrimdışı `pip install` başarısızlığı, Windows yol/encoding sorunları, kullanıcının global Python'a paket kurması.
- **C7:** Kanıt hijyeni: `docs/ENVIRONMENT.md` içine ham komut+çıktı kanıtı yazılır; komut listesi gerçek yürütme loguyla birebir uyuşur.
