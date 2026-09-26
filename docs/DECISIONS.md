# Mimari Kararlar

Bu kararlar mimar tarafından verilmiştir. Değişiklik gerekirse yeni bir karar satırı eklenir; mevcut satır silinmez (append-only).

| # | Karar |
|---|---|
| D-001 | Ortam: proje-yerel `.venv` (Python 3.12); global ortama kurulum yasak. |
| D-002 | Paketleme: pip + PEP 621 `pyproject.toml` (setuptools backend); Poetry/uv zorunlu değil. |
| D-003 | CLI: argparse (stdlib); Typer/Click kullanılmayacak. Yeniden değerlendirme kapısı: PHASE 2 exit gate. |
| D-004 | Kapsam: yalnızca tabular regression; sınıflandırma/forecasting/görüntü/metin MVP dışı. |
| D-005 | Model yükleme yok (pickle/joblib yasak). Tahminler dosyadan: `y_true`, `y_pred` + opsiyonel `group_id`, `timestamp`, `subset_id`. |
| D-006 | `--group-col` / `--time-col` yalnızca açıkça verilir; otomatik tespit yok; verilmezse ilgili kontrol `not_assessable` + reason_code. |
| D-007 | Kanonik JSON: `sort_keys=True`, `ensure_ascii=False`, `allow_nan=False`; float 6 ondalık; NaN/Inf → `null` + `non_finite_count`; çıktı üreten yerde `set` yasak. |
| D-008 | Hash'lenen gövdede wall-clock timestamp yok; zaman bilgisi yalnızca `run_metadata.generated_at` (varsayılan `null`, `--run-timestamp` ile verilir). |
| D-009 | `--seed` parametresi (varsayılan 42), raporda kayıtlı; fonksiyon içinde gömülü sabit yok. |
| D-010 | Determinizm iddiasının kapsamı: aynı ortam + aynı girdi + aynı seed. Makineler arası byte-identiklik iddia edilmez. |
| D-011 | Zorunlu provenance: girdi SHA-256, satır/kolon sayısı, kolon adları hash'i, tool/python/pandas sürümü, seed. |
| D-012 | Kontrol durum modeli: `performed` / `skipped` / `not_assessable` + `reason_code` + `evidence_ref`; rapor bu sayımları zorunlu yazar. |
| D-013 | CSV sağlamlığı: `utf-8-sig` varsayılan + BOM temizliği; ayırıcı tespiti (`,` `;` `\t`); ondalık virgül tespit edilirse uyarı + `--decimal`; sessiz yorumlama yok. |
| D-014 | Sessiz kırpma yok; `--max-rows` açıkça verilirse uygulanır ve `truncated=true` olarak rapora ve provenance'a yazılır. |
| D-015 | Opsiyonel ekstralar: `[parquet]`=pyarrow, `[ml]`=scikit-learn; çekirdek kurulumda yok; kurulu değilse ilgili kontrol `not_assessable`. |
| D-016 | Dil: kod/CLI/JSON anahtarları/README = İngilizce; `docs/PHASE-*.md` ve `DECISIONS.md` = Türkçe. LICENSE seçimi PHASE 2 sonunda kullanıcı kararı. |
| D-017 | Veri okuma: CSV varsayılan olarak utf-8-sig ile okunur ve BOM varsa temizlenir. Parquet opsiyonel ekstra gerektirir. |
| D-018 | Ayırıcı ve ondalık tespiti: Deterministik sniff (ilk 50 satır/64KB) yapılır. Ambiguous durumlarda sessiz fallback yapılmaz. |
| D-019 | Path raporlama: Kullanıcının verdiği dosya yolu olduğu gibi provenance'a yazılır (mutlak yola genişletilmez). |
| D-020 | Max rows: Açıkça verilirse uygulanır, sessiz kırpma yasaktır. Truncation durumu rapora yazılır. |
| D-021 | Hata yönetimi: Şema kontrolleri fail üretirse araç Exit Code 4 ile sonlanır. "not_assessable" uyarı mahiyetindedir. |
| D-022 | CLI: `inspect` alt komutu kanonik JSON basar. `--out-dir` bu aşamada reserve edilmiştir. |
