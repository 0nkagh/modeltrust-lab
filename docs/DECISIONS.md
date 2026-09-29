# Mimari Kararlar

Bu kararlar mimar tarafından verilmiştir. Değişiklik gerekirse yeni bir karar satırı eklenir; mevcut satır silinmez (append-only).
> Karar numaraları tekrar kullanılmaz; mükerrer satır tespit edilirse ikinci kopya silinir ve içeriği gerekiyorsa yeni numarayla eklenir.

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
| D-017 | `provenance.py` T3'ten T2'ye taşındı: provenance, yüklenen girdi artefaktının özelliğidir; rapor entegrasyonu T6'da yapılır. |
| D-018 | `reason_code` kontrollü sözlüğü: `not_provided`, `dependency_missing`, `ambiguous_input`, `unsupported_dtype`, `insufficient_rows`, `insufficient_groups`, `time_column_missing`, `tool_not_implemented`. |
| D-019 | Girdi yolu rapora kullanıcının verdiği haliyle yazılır; mutlak yola genişletilmez. |
| D-020 | CLI sözleşmesi: stdout **yalnızca** kanonik JSON içerir; tüm uyarılar stderr'e gider. |
| D-021 | Satır sonu politikası: `.gitattributes` ile repo kanonik LF; `tests/fixtures/**` byte kararlılığı için korunur. |
| D-022 | Commit yalnızca **tüm testler geçtikten sonra** atılır; bitmemiş iş commit edilmez. |
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
| D-017 (errata) | `provenance.py` T3'ten T2'ye taşındı: provenance, yüklenen girdi artefaktının özelliğidir; rapor entegrasyonu T6'da yapılır. (errata — bkz. I-026) |
| D-018 (errata) | `reason_code` kontrollü sözlüğü: `not_provided`, `dependency_missing`, `ambiguous_input`, `unsupported_dtype`, `insufficient_rows`, `insufficient_groups`, `time_column_missing`, `tool_not_implemented`. (errata — bkz. I-026) |
| D-019 (errata) | Girdi yolu rapora kullanıcının verdiği haliyle yazılır; mutlak yola genişletilmez. (errata — bkz. I-026) |
| D-020 (errata) | CLI sözleşmesi: stdout **yalnızca** kanonik JSON içerir; tüm uyarılar stderr'e gider. (errata — bkz. I-026) |
| D-021 (errata) | Satır sonu politikası: `.gitattributes` ile repo kanonik LF; `tests/fixtures/**` byte kararlılığı için korunur. (errata — bkz. I-026) |
| D-022 (errata) | Commit yalnızca **tüm testler geçtikten sonra** atılır; bitmemiş iş commit edilmez. (errata — bkz. I-026) |

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
| D-065 | `shift` ve `report --shift` için --target-col zorunludur (target_ks drift kontrolü hedef gerektirir); eksikse exit 2. |
| D-066 | report --shift verilmeden --split-mode/--test-size kullanılamaz (exit 2); --shift ile birlikte kullanılabilir. |
| D-067 | Belirsizlik (Uncertainty) değerlendirmesi evaluation bloğunun bir parçasıdır; `--lower-col` ve `--upper-col` (ve opsiyonel `--nominal-coverage`) verildiğinde aktifleşir. |
| D-068 | Belirsizlik aralıklarının kapsamı "single split, no distribution-free guarantee" varsayımıyla çalışır ve kalibrasyon güvencesi ("aralıklar kalibre olduğu kanıtlandı") vermez; sadece ampirik "observed coverage" hesaplanır. Küçük örneklem aralığı için Wilson Score Interval kullanılır. |

| D-069 | Test fixture'larındaki belirsizlik değerleri testlerdeki teorik/ideal oranlar yerine ampirik ölçümlere (tolerans payıyla birlikte) bağlanır. |
| D-070 | Belirsizlik aralık genişlikleri değerlendirilirken numpy.inf değerleri dışlanmaz; metriklerde aralıkların doğası gereği hesaba katılır, ancak bucket hesaplamalarında veya test verilerinde sonsuz değer beklenmediği için standart yaklaşımlar kullanılır. |
| D-071 | Kapsama metriklerinde hata toleransı 0.05 (%5) olarak sabitlenmiştir. |
| D-072 | Belirsizlik fixture'ları hata σ'sına göre ölçeklenmiş yarıçaplarla üretilir (σ=1; R=1.645 kalibre, R=0.4 aşırı güvenli); testler ölçülen kapsamaya şartname bandıyla bağlanır. |
| D-073 | Golden dosyaları depoda LF satır sonuyla saklanır; Windows çalışma kopyasındaki CRLF git normalizasyonuyla commit edilir. |
| D-074 | Model card bir sertifika değildir; yalnız bu veri kümesi ve bu ayarlarla üretilmiş teşhis özetini taşır ve performans garantisi içermez. |
| D-075 | modeltrust card modülü: schema+profile+leakage+split her zaman çalışır; evaluate/shift girdileri isteğe bağlıdır ve ayrı bayrak gerektirmez. |
| D-076 | Karttaki 10 sorunun durum kuralları METHODS §11 tablosuyla sabittir; kural değişikliği yeni karar numarası gerektirir. |
| D-077 | Model card bir sertifika değildir; performans/uyumluluk iddiası içermez, yalnız teşhis özetidir. |
| D-078 | Metrik tablosunda n_scored kapsamı dinamiktir: tüm satırlarda n_train=0 ise "n_scored (all rows provided)", aksi hâlde "n_scored (split)"; karışık kümede "n_scored (scope varies)" ve warnings notu. Card ve report aynı yardımcı fonksiyonu kullanır. |
| D-079 | card komutu verilen kolon bayraklarının girdide bulunmasını zorunlu kılar; bulunmayan kolon için exit 2 ve "Error: --<bayrak> '<ad>' not found in input columns". Diğer alt komutların kolon doğrulanması bilinçli olarak bu sürümün kapsamı dışındadır (T15 adayı). |
| D-080 | Karar defteri append-only'dir: aynı numaranın birden fazla satırı bulunabilir (errata); errata satırları numarasında "(errata)" işareti taşır ve hiçbir satır silinmez. |
| D-081 | D-075'e errata: kart her zaman schema+profile+leakage çalıştırır; split modülü yalnız --group-col veya --time-col verildiğinde çalışır. Verilmediğinde split atlanır ve atlama, checks summary ile not_assessable kayıtlarında reason_code=not_provided olarak görünür (I-037/I-038 sonrası davranış). |
| D-082 | Reproducibility manifest: card komutuna --manifest bayrağı eklenir ve out-dir içine manifest.json yazılır (manifest_schema_version=1). Manifest zaman damgası içermez; tool, command, input (yol+sha256+satır/kolon), environment, seed, git (commit, dirty; erişilemezse null + reason_code=not_available), config.thresholds ve outputs (card.json/card.md sha256) alanlarını taşır. --manifest yokken stderr mesajı değişmez; varken manifest.json da listelenir. Manifest report/evaluate/shift için kapsam dışıdır. |
| D-083 | Değerlendirilemeyen (not_assessable) sayısal alanlar raporda 0.000000 olarak gösterilmez; N/A ve reason_code yazılır (ör. grup hata kapsamı oranı). Gerçekten sıfır olan geçerli değerler (ör. R²) değişmez. |
| D-084 | report komutuna --card bayrağı eklenir: --card verildiğinde kart, raporla aynı provenance üzerinden üretilir ve aynı out-dir'e yazılır; girdi yeniden okunmaz, modüller yeniden çalıştırılmaz. Eşdeğer bayraklarla üretilen kartın questions, checks_summary, not_assessable, metrics, thresholds ve scope blokları card komutunun çıktısıyla aynı olmalıdır. stderr: "wrote <DIR>\report.json, <DIR>\report.md, <DIR>\card.json and <DIR>\card.md". --card yokken report çıktısı ve stderr mesajı değişmez; report için manifest üretimi bu sürümde kapsam dışıdır (D-082 korunur). |

| D-085 | D-084'e errata: report --card ile üretilen kartın card komutuyla blok eşitliği yalnız aynı modül kümesinde beklenir. card komutu schema+profile+leakage+split ile birlikte evaluation ve shift modüllerini varsayılan olarak çalıştırır; report yalnız verilen bayraklarla çalıştırdığından eşdeğerlik için report tarafında --evaluate --shift --card birlikte verilir. Modül kümeleri farklıysa kartın daha az modül listelemesi beklenen davranıştır, hata değildir. |
| D-086 | CLI sözleşmesi: tüm alt komutlar --help ile exit 0 döner ve help metinleri biçim-güvenlidir (argparse % kaçışı). Bu davranış test_all_subcommands_help_exit_zero testiyle kilitlenir. |
| D-087 | Errata (T17-R2): I-046 hatalı öncüle dayanıyordu — README veri dosyaları için genel data.csv yer tutucusu kullanır; README'de geçen gerçek fixture adları yalnız intervals_calibrated.csv ve intervals_overconfident.csv'dir ve ikisi de depodadır. Ayrıca: denetim bulguları da ham kanıtla doğrulanmadan görev kapsamına alınmaz ve commit mesajı yalnız değişen dosyaları tarif eder (c14c51d mesaj-diff uyuşmazlığı; tarih düzeltilemez, kayıt altına alındı). |
| D-088 | Soru erişilebilirliği sözleşmesi: 10 sorunun her biri, dokümante edilmiş en az bir girdi kombinasyonunda answered döner (Q10 kural gereği her zaman partial); minimum kombinasyonlar docs/ASSESSABILITY.md'de listelenir ve tests/integration/test_assessability.py ile kilitlenir. |
| D-089 | Erişilebilirlik sözleşmesi (netleştirme): docs/ASSESSABILITY.md'de beyan edilen minimum komutlar ile tests/integration/test_assessability.py'deki koşular birebir aynıdır; belgedeki kod atıfları satır numarası + kararlı kontrol anahtarı biçiminde yazılır ve EXIT paketinde ham doğrulanır. |
| D-090 | LICENSE = MIT (telif: Ömer Agah Koyun, 2026) ve paket metadata'sı PEP 639 uyumlu lisans alanıyla bildirilir; LICENSE dosyasının SHA-256'sı bu karar kaydının düzenlendiği turda raporlanır ve commit ile sabitlenir. MIT seçildi çünkü lisans metni çevrimdışı ve hatasız yazılabilir, depo kanıt disipliniyle doğrulanabilir ve bu tanı aracı için patent maddesi maddi değildir. |
| D-091 | README determinizm kapsamı: aynı komut + aynı girdi + aynı --out-dir → bit-bit aynı çıktı; çıktı dosyaları invocation metnini (out-dir yolu dâhil) gömer, manifest.json ayrıca git.commit alanı taşır, bu nedenle farklı dizin veya yeni commit hash'i değiştirir. Bu davranış provenance amaçlıdır ve sınırı README'de yazılıdır. |
| D-092 | Ortam politikası: .venv içeriği ve .venv\pyvenv.cfg prompt yetkisi olmadan değiştirilmez; ortam araçları (ör. setuptools) eksikse kurma/kopyalama/ağ yapılmaz, durum ham çıktıyla raporlanır ve karar mimara bırakılır. Teşhis ve koşu komutları yalnız .\.venv\Scripts\python.exe üzerinden verilir (çıplak python/pip yasak). 2026-09-28 itibarıyla .venv içinde sistem Python'dan kopyalanmış setuptools ve _distutils_hack bulunmaktadır (I-049); bu bir çalışma-zamanı bağımlılığı değil, derleme/kurulum altyapısıdır ve 196 testlik suite bu ortamda yeşildir. |
| D-093 | Commit kapsam kuralı: commit mesajı o commit'teki tüm dosyaları tarif eder; mesaj kapsamı ile diff kapsamı birebir olmalıdır. Şablon bir mesaj sonradan eklenen dosyayı kapsamıyorsa ya mesaj güncellenir ya da ek dosya ayrı commit'e alınır (kayıtlar: I-047 ve I-050). |
| D-094 | Vaka çalışması çerçevesi: examples/case_study deterministik (sabit seed, üretici script'li) sentetik bir veri kümesidir; kusurlar bilinerek enjekte edilmiştir ve sonuçlar kıyaslama değil, gösterim niteliğindedir — yalnız bu veri kümesi, bu sürüm ve koşulan komutlar için geçerlidir. Tespit edilmeyen kusurlar CASE_STUDY.md'de açıkça listelenir; veri, araç lehine sonuç çıkacak şekilde ayarlanmaz. |
| D-095 | Vaka çalışması koşu kuralı: her enjekte edilen kusur, hedeflendiği mod ve grup kolonuyla (ör. zaman-yerel kayma için --split-mode temporal, bölgesel etki için --group-col region) ayrıca koşulur; varsayılan mod davranışı ayrı satır olarak raporlanır. Gerekçe: aksi hâlde "tespit edilmedi" bulgusu araç yeteneği yerine komut seçimini ölçer (I-051). |
| D-096 | Koşu hijyeni: geçici çıktılar yalnız $env:TEMP altında üretilir; komutlar sarmalayıcı kullanılmadan doğrudan oturumda çalıştırılır; çıktı üreten koşular (report/card) her zaman --out-dir ile yapılır (I-052). |
| D-097 | Kök hijyeni (netleştirme): repo köküne yeni dosya/dizin ekleme yalnız promptta açıkça istendiğinde yapılır; pytest yapılandırmasının tek kaynağı pyproject.toml'dur ve geçici test dizinleri yalnız $env:TEMP altında --basetemp ile kurulur (I-053). |
| D-098 | Çalışma ağacı temizliği: her tur, git status --untracked-files=all çıktısı boş olacak şekilde kapatılır. Geçici test/aid dosyaları (ör. tests/__init__.py, pytest.ini) yalnız prompt yetkisiyle ve yalnız $env:TEMP kapsamında üretilir; depo içinde untracked artık dosya bırakılmaz (I-053/I-054). |
| D-099 | Dış araç karşılaştırması repo dışında ve geçici bir venv'de yapılır: kurulum, `python -m venv` ile `$env:TEMP` altında oluşturulan ayrı ortama yapılır; ana `.venv`, `pyproject.toml` ve proje bağımlılıkları değişmez. Karşılaştırma belgesi araç sürümünü, koşu tarihini, kurulum komutunu ve ham çıktı alıntılarını taşır; koşu yapılamazsa belge "yürütülemedi" olarak yazılır ve kurulum zorlanmaz (K-3, I-049). |
| D-100 | Belgelere aktarılan özet/agrega metrikler, aynı koşunun alt kalem değerleriyle uzlaştırılır; sayılar tutmuyorsa fark kaynağıyla birlikte belgeye yazılır, açıklanamıyorsa "farkın kaynağı belirlenemedi" denir. Her sayısal iddianın atfı, değerin fiilen okunduğu dosyayı ve alanı (veya komutu) gösterir (I-055). |
| D-101 | Dil politikası: `README.md` tek dilde (İngilizce) tutulur; kod, test ve CLI metinleri İngilizcedir. `docs/` altındaki belgeler (DECISIONS, INCIDENTS, CASE_STUDY, COMPARISON, METHODS, ASSESSABILITY) Türkçe olabilir; ancak her belge kendi içinde tek dilde olur. Yeni bir belge hangi dilde başlarsa öyle bitirilir. |
| D-102 | Araştırma makalelerinde (COMPARISON.md vb.) her sayısal tablo tek bir kanonik koşuya ve o koşunun çıktı dosyasının sha256 özetine bağlanmak zorundadır. Aynı araç için geriye uyumlu ikinci bir kod yolu (legacy API vb.) veya alternatif bir yöntem kullanıldıysa (ve üretilen değerler farklıysa), bu değerler aynı tabloda karıştırılmaz; farklı dosya ve kaynak gösterilerek ayrı bir alt paragrafta tartışılır. |
| D-103 | Yasaklı git komutları kendi hatalarımızı geri almak için de kullanılmaz: `git checkout` / `git restore` / `git reset` / `git stash` / `git clean` hiçbir koşulda çalıştırılmaz. Hatalı bir dosya değişikliği, dosya bütün olarak yeniden yazılarak düzeltilir (fix-forward) ve olay kaydı açılır (I-027, I-057). |
| D-104 | Promptta birebir verilen metinler (commit mesajı, olay ve karar gövdeleri) aynen kullanılır; değiştirilmesi gerekiyorsa önce gerekçesiyle bildirilir ve onay beklenir. Commit mesajı kapsamı diff kapsamına eşit kalır (D-093, I-050). |
| D-105 | Kaynağı belirlenemeyen farklar için "sahte", "hatalı", "yanlış" gibi nitelemeler kullanılmaz; "kaynağı belirlenemedi" denir. I-056 kaydındaki "sahte/hatalı p-değerleri" nitelemesi bu kararla geçersiz sayılır; I-058'deki "kaynağı belirlenemedi" beyanı geçerlidir. Kanıtlanmamış niteleme, kanıtlanmamış sayıdan ayrı bir kusurdur (I-055/I-056). |
| D-106 | Yayın öncesi doğrulama: yayınlanacak ağaç temiz bir klonda kurulup test edilir. Kaynak depo klondan kurulabilmeli, suite klonda yeşil olmalı, vaka çalışması üreticisi klonda depodaki CSV ile aynı sha256'yı üretmeli, CLI çıktıları aynı çıktı dizininde bit-bit aynı olmalı ve paket metadata'sı (sürüm, lisans ifadesi, bağımlılıklar) denetlenmelidir. Bu doğrulama geçmeden push ve etiket yapılmaz (D-092, I-049). |
| D-107 | Yayınlanacak belgelerdeki kanıt alıntıları, yazarın kendi makinesine ait yerel yollar içerebilir (ör. `C:\Users\agah\AppData\Local\Temp\...`). Bu yollar kabul edilir: üçüncü kişilere ait veri içermezler ve commit yazarı kimliği (ad, e-posta) zaten kamuya açıktır. Kanıt metinleri ham bırakılır; yerel yolların maskelenmesi kanıt bütünlüğünü bozacağı için yapılmaz (T21-R1 temiz klon taraması sonucu). |
| D-108 | **CI politikası (GitHub Actions):** Her `main` push'unda ve her PR'da CI koşar. İzinli action'lar yalnız `actions/checkout@v7.0.1` ve `actions/setup-python@v7.0.0`; üçüncü parti action kullanılmaz, action sürümleri tam etiketle sabitlenir. Workflow izinleri `contents: read` ile sınırlıdır. CI'da sabit hash olarak yalnız tohumlu üreticiyle üretilip depoya işlenmiş `examples/case_study/case_study.csv` sha256'sı doğrulanır; ortama bağlı diğer hash'ler CI'da sabitlenmez (D-091). CI yeşil olmadan yeni sürüm etiketi oluşturulmaz. |
| D-109 | **Desteklenen Python aralığı = CI'da koşulan aralık:** `requires-python` beyanı, CI matrisinin en düşük sürümünden küçük olamaz. Bağımlılık metadata'sı (PyPI `requires_python`) bir sürümde kurulumu imkânsız kılıyorsa o sürüm matrise girmez ve beyan yukarı çekilir. Kanıtsız taban beyanı yayınlanmaz (T23; `I-059`). |
| D-110 | Dil politikası rafinesi: Türkçe KALACAK (tarihsel kayıt, append-only): docs/DECISIONS.md, docs/INCIDENTS.md, docs/PHASE-1-PLAN.md, docs/PHASE-3-EXIT.md. LICENSE'taki hak sahibi adı (Ömer Agah Koyun) çevrilmez. |
