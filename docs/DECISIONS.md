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
| D-023 | Kontrol durum modeli (`reason_code`): `performed` (null), `not_assessable` (not_provided vb.), `skipped` (tool_not_implemented). `result="fail"` yalnızca koşul sağlanmadı demektir, model güvenliği hakkında karar vermez. |
| D-024 | Fixture hijyeni: Tüm fixture'lar `tests/fixtures/README.md` içinde belgelenmeli, `turkish_bom_semicolon.csv` istisnası dışında BOM'suz ve LF satır sonlu UTF-8 olmalıdır. |
| D-025 | Golden normalizasyonu: Environment alanı exclude edilerek normalized test gerçekleştirilir. |
| D-026 | Profil çıktısı bir teşhis göstergesidir; veriyi temizlemez, hiçbir kalite iddiası üretmez. |
| D-027 | Karar metinleri her zaman promptun içinde verilir; ayrı bir dosyaya atıf yapılmaz. |
| D-028 | İdempotency: bir task'ın çıktısı repoda zaten mevcutsa uygulayıcı düzenleme yapmaz; durur, durumu bildirir ve onay bekler. Kendi düzeltmesini `git restore`/`checkout`/`reset` ile geri alması yasaktır. |
| D-029 | `tests/conftest.py` repo kökü `parents[1]` ile bulunur (dosya `tests/` altındadır). Mimardan gelen `parents[2]` talimatı hatalıydı; mimar hatası kayda geçirilmiştir. |
| D-030 | High-cardinality eşiği 0.95'tir; `profile_dirty.csv`'deki `txt` (0.875) flag'lenmez. Pozitif yol için `high_card_id.csv` eklenir. Mimardan gelen 4.3 beklentisi hatalıydı. |
| D-031 | `ColumnSpec`'e `subset` alanı, CLI'ya `--subset-col` eklendi (D-005'teki `subset_id`). Verilmezse alt küme bağımlı kontroller `not_assessable` + `not_provided`. |
| D-032 | Her denetim çıktısında zorunlu `interpretation` alanı: "Diagnostic indicators only. A flagged pattern may be legitimate. Absence of a flag does not establish absence of leakage." |
| D-033 | Satır çakışması ölçütü: subset kolonu hariç tüm kolonların string birleşimi üzerinden SHA-256 satır parmak izi; aynı parmak izi iki subset'te görünüyorsa çakışma sayılır. |
| D-034 | Tüm eşikler kodda adlandırılmış sabit olarak tanımlanır ve çıktıda `thresholds` bloğunda raporlanır. |
| D-035 | `pyproject.toml`'a `[tool.pytest.ini_options] pythonpath = ["."]` eklendi; `tests.conftest` importu çağrı dizininden bağımsız hale getirildi. |
| D-036 | `docs/METHODS.md` zorunlu: her kontrolün ne ölçtüğü/ölçmediği, eşik gerekçeleri ve kapsam dışı sızıntı türleri (preprocessing, feature engineering, örnekleme bias'ı, etiket gürültüsü, join kaynaklı sızıntı, temporal nedensellik). |

### Errata — D-017…D-022
D-017…D-022 satırları, karar metinleri prompt içinde verilmediği için uygulayıcı tarafından farklı içerikle doldurulmuştur. Aşağıdaki metinler bu kararların geçerli (authoritative) halidir; eski satırlar silinmez ve `superseded` sayılır.

| # | Geçerli metin |
|---|---|
| D-017 | `provenance.py` T3'ten T2'ye taşındı: provenance, yüklenen girdi artefaktının özelliğidir; rapor entegrasyonu T6'da yapılır. |
| D-018 | `reason_code` kontrollü sözlüğü: `not_provided`, `dependency_missing`, `ambiguous_input`, `unsupported_dtype`, `insufficient_rows`, `insufficient_groups`, `time_column_missing`, `tool_not_implemented`. |
| D-019 | Girdi yolu rapora kullanıcının verdiği haliyle yazılır; mutlak yola genişletilmez. |
| D-020 | CLI sözleşmesi: stdout **yalnızca** kanonik JSON içerir; tüm uyarılar stderr'e gider. |
| D-021 | Satır sonu politikası: `.gitattributes` ile repo kanonik LF; `tests/fixtures/**` byte kararlılığı için korunur. |
| D-022 | Commit yalnızca **tüm testler geçtikten sonra** atılır; bitmemiş iş commit edilmez. |

### Errata & Sapmalar (T4-R2)
* `run_leakage_audit` adı `build_leakage` olarak uygulandı.

| # | Karar |
|---|---|
| D-037 | Dosya listesi sözleşmedir. Promptta listelenmeyen bir dosyanın değiştirilmesi gerekiyorsa uygulayıcı durur, gerekçesini yazar ve onay bekler. Onay alınmadan yapılan liste dışı değişiklik, sonradan beyan edilse bile ihlal sayılır. |
| D-038 | Commit mesajı promptta verilen metindir; kısaltılamaz, yeniden yazılamaz. Verilen mesajla commit edilemiyorsa uygulayıcı durur ve bildirir. |
| D-039 | Kanıt = ham çıktı. Özet, liste veya "tüm testler geçti" ifadesi kanıt değildir. Rapor ham komut çıktısı içermiyorsa task kabul edilmez; eksik kanıt için ayrı tur açılır. |
| D-040 | `git add` her zaman açık dosya listesiyle yapılır. `git add .`/`-A` yasaktır; commit'e giren dosya kümesi promptta verilen liste ile birebir aynı olmalıdır. |
| D-041 | Uygulayıcı (Antigravity) hiçbir git komutu çalıştırmaz; commit ve stage işlemleri depo sahibi tarafından, denetçinin verdiği sabit script ile yapılır. |
| D-042 | Birincil kanıt, depo sahibinin çalıştırdığı doğrulama scriptinin ham çıktısıdır. Uygulayıcının özeti/raporu tek başına kanıt değildir. |
| D-043 | Beyan ile yürütme logu çelişirse beyan geçersizdir ve olay kaydı (INCIDENTS) açılır. |
| D-044 | Random split yöntemi `numpy.random.default_rng(seed).permutation`; tekrarlanabilirlik kapsamı aynı ortam + aynı numpy sürümü; sürümler arası kararlılık iddia edilmez. |
| D-045 | Her bölmenin train/test satır indeksleri SHA-256 ile kayda geçirilir (`*_row_indices_sha256`); bölme karşılaştırmaları bu hash'ler üzerinden yapılır. |
| D-046 | Group split kuralı: gruplar (satır sayısı azalan, ad artan) sıralanır, test kümesi hedefe ulaşana kadar sırayla doldurulur; deterministiktir. |
| D-047 | Commit edilmiş içerik ile çalışma ağacı ayrışamaz: commit her zaman testler yeşilken ve çalışma ağacında commit edilmemiş düzeltme bırakmadan atılır. |
| D-048 | CLI exit code 3 (not implemented) kullanımdan kaldırıldı. `--out-dir` artık `report` komutu için zorunludur ve bu komut diske JSON/Markdown dosyaları yazar. Diğer komutlar `--out-dir` aldığında dosya yazmaz, yönlendirici hata mesajıyla (exit 0) sonlanır. |
| D-049 | Markdown raporu JSON çıktısının doğrudan izdüşümüdür; Markdown raporuna, canonical JSON yapısında bulunmayan hiçbir ek veri (timestamp vb.) eklenemez, böylece içerik hash-identical determinizm korunur. |
| D-050 | `MIN_ROWS_FOR_INDEX_CHECK = 10`; bu eşiğin altında `index_like_feature` değerlendirilemez (`insufficient_rows`). Gerekçe: az satırlı dosyalarda ID benzeri kolonlar teşhis değeri taşımaz ve yanlış pozitif üretir. |
| D-051 | Baseline ve CV araç içinde numpy ile uygulanır (np.linalg.lstsq); scikit-learn çekirdek bağımlılık değildir, opsiyonel ekstra olarak kalır. |
| D-052 | NaN politikası: hedefi boş satırlar skorlanmaz; özelliklerde NaN olan satırlar model eğitiminden düşülür; her düşme sayısı raporda görünür. |
| D-053 | Uyarı listesi sabit sıradadır; yalnız o an geçerli uyarılar yazılır. |
| D-054 | --pred-col verildiğinde tüm satırlar skorlanır; holdout iddiası yoktur, bu durum raporda ve METHODS'ta açıkça yazılır. |
| D-055 | Preprocessing kontrolleri imza temelli göstergelerdir; kanıt değildir. Pipeline fit kapsamı CSV'den değerlendirilemez ve açıkça not_assessable raporlanır. |
| D-056 | Yeni reason_code: requires_pipeline_code (yalnız preprocess.fit_scope). |
| D-057 | abs_std_mean_diff tek formülden (ağırlıksız ortalama varyans, ddof=1) hesaplanır: denom = sqrt((var_tr + var_te)/2). Holdout bölmelerinde (ör. %80/%20) n_train >> n_test olduğundan, serbestlik derecesine göre ağırlıklı havuzlanmış varyans kullanılsaydı payda tamamen train varyansı tarafından domine edilir ve test kümesindeki dağılım kayması/kararsızlığı maskelenirdi; bu nedenle iki küme eşit ağırlıklandırılmıştır. Testle (1.341641 vs 1.732051) sabitlenir. |
| D-058 | eval_preds.csv şartnameye sabitlendi: 3 grup × 10 satır, ilk 20 satır pred=y, son 10 satır pred=y+3 (MAE=1.0, RMSE=√3). |
| D-059 | evaluation bloğu şeması T7-B3 sözleşmesiyle tam uyumludur: models[].{mae,rmse,r2,n_scored}, group_errors.{groups[],worst_by_mae,coverage_ratio,model}, cv.folds[].{n_groups_train,n_groups_test}; coverage_ratio = n_rows_evaluated / n_rows_scored olarak tanımlanır. |
| D-060 | report --evaluate opsiyoneldir (varsayılan kapalı); açıldığında evaluation bloğu JSON'a ve md'ye eklenir, davranış evaluate komutuyla birebir aynıdır. |
| D-061 | Yeni modül: audit/shift.py (OOD + drift). Yeni reason_code: degenerate_covariance. |
| D-062 | OOD/drift eşikleri heuristiktir; p-değeri hesaplanmaz (scipy yok). Bulgular "diagnostic indicator" dilinde raporlanır. |
| D-063 | split.py indeks üretimi compute_split_indices yardımcısına çıkarıldı; build_split çıktı sözleşmesi ve golden'lar değişmedi. |
| D-064 | report --shift opsiyoneldir; açıldığında §6 iki tabloya genişler (split karşılaştırma + distribution shift & OOD) ve JSON'a shift bloğu eklenir; diğer golden'lar değişmez. --split-mode ve --test-size artık --evaluate veya --shift varlığını gerektirir. |



