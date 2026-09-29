# Dış Araç Karşılaştırması: Evidently

## 1. Amaç ve dürüstlük çerçevesi

Bu bir kıyaslama (benchmark) değildir.
Bu çalışma, ModelTrust Lab'in tanı denetim sonuçlarını mevcut ve yaygın bir açık kaynaklı veri sürüklenme aracı olan Evidently ile yan yana koyarak sözleşme, yöntem ve çıktı farklarını somut biçimde belgelemeyi amaçlar.
Çalışma tek araç (Evidently), tek sürüm (0.7.23), tek veri kümesi (`case_study.csv`) ve tek tarih (2026-09-29) ile sınırlandırılmıştır.
Araçlar arasında bir üstünlük iddiasında ("daha iyi", "üstün", "rakipsiz") bulunulmaz; yalnızca doğrudan gözlenen değerler, yöntem seçimleri ve sözleşme semantikleri tarafsız olarak aktarılır.
Evidently, açık kaynak dünyasında tabular veri kalitesi ve sürüklenme izlemede en yaygın referans kabul edildiği için karşılaştırma aracı olarak seçilmiştir.

## 2. Ortam ve sürümler

- **Çalışma Tarihi**: 2026-09-29
- **ModelTrust Lab Sürümü**: 0.0.1.dev0 (Python 3.12.8, numpy 2.5.3, pandas 3.0.6)
- **Evidently Sürümü**: 0.7.23
- **Geçici Ortam Yolu**: `C:\Users\agah\AppData\Local\Temp\mt_ev_venv`
- **Kurulum Komutu**: `& "$env:TEMP\mt_ev_venv\Scripts\python.exe" -m pip install --disable-pip-version-check evidently`
- **Not**: Kurulum paket indirme aşamasında ağ erişimi gerektirir; veri analizi ve rapor koşusu tamamen yerel ve çevrimdışı gerçekleştirilmiştir.
- **`pyvenv.cfg` içeriği**:
  ```ini
  home = C:\Users\agah\AppData\Local\Programs\Python\Python312
  include-system-site-packages = false
  version = 3.12.8
  executable = C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe
  command = C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe -m venv C:\Users\agah\AppData\Local\Temp\mt_ev_venv
  ```
- **Bağımlılık Durumu**: `pip freeze` çıktısı toplam **80** satırdır. İlk 20 satırı aşağıdadır:
  ```text
  annotated-doc==0.0.5
  annotated-types==0.8.0
  anyio==4.15.1
  appdirs==1.4.4
  certifi==2026.7.22
  cffi==2.1.1
  charset-normalizer==3.5.1
  click==8.5.0
  cloudpickle==3.1.2
  colorama==0.4.6
  cryptography==50.0.1
  defusedxml==0.7.1
  deprecation==2.1.0
  distro==1.9.0
  dynaconf==3.3.5
  evidently==0.7.23
  Faker==40.40.0
  filelock==4.0.6
  formulaic==1.2.2
  fsspec==2026.9.0
  ```
- **Telemetri**: Evidently `iterative_telemetry` kütüphanesini kullanmaktadır (kaynak: `iterative_telemetry/__init__.py:29-166` — `DO_NOT_TRACK_ENV = "ITERATIVE_DO_NOT_TRACK"`, `is_enabled` metodunda `os.environ.get(DO_NOT_TRACK_ENV) is None` kontrolü). Koşu sırasında `DO_NOT_TRACK=1` tanımlanarak telemetri çağrıları engellenmiştir.

## 3. Girdi hizalaması

Her iki araca da birebir aynı veri satırları ve aynı dilimler sağlanmıştır.

- **Kaynak Veri**: `examples/case_study/case_study.csv` (600 satır, 12 kolon, SHA-256: `9587B66886A942EE9E9589FE65F000406F6F9F40F41BA7E7BF0B5E0CF9E942DA`)
- **Bölme Yöntemi**: Zaman damgasına (`ts`) göre kararlı sıralama (`mergesort`), ilk %80 (480 satır) referans/eğitim, son %20 (120 satır) test/akım dilimi olarak ayrılmıştır.
- **ModelTrust Eşlemesi**: `report.json` içindeki `split.modes.temporal` (ve `shift.split.mode: "temporal"`) alanında `n_train: 480`, `n_test: 120`. `time_ranges`: `train_max: 2025-04-18 00:00:00`, `test_min: 2025-04-19 00:00:00`. Blok sıralama kuralını doğrudan metin olarak belirtmez; ancak `ts` kolonunun artan sıralanmasıyla ilk 480 satır eğitim, son 120 satır test olarak ayrılmış ve `train_row_indices_sha256` ile kilitlenmiştir.
- **Evidently Eşlemesi**: `Report.run(reference_data=ref, current_data=cur)` çağrısında `reference.csv` ve `current.csv` dilimleri kullanılmıştır.
- **Dilim Dosyaları**:
  - `reference.csv`: 480 satır, SHA-256: `C8168216AAA1A859B25194A6AEE8D4F04774844FD82B71AD2D79FBFDEC3FD26D`
  - `current.csv`: 120 satır, SHA-256: `0F1502DF4EA780D77B70881C9A080CA2200F798139B88442ADA0CC02A724788D`
- **Kolonlar**: `['row_id', 'ts', 'site', 'region', 'x1', 'x2', 'x3', 'y', 'pred', 'lo', 'hi', 'y_proxy']`
- **Doğrulama**: Aynı satırların iki araca da verildiği SHA-256 özetleriyle kesinleştirilmiştir.

## 4. Ölçülen sonuçlar (yan yana)

### 4.a ModelTrust Lab (temporal bölme) — kolon bazlı KS

| Kolon | KS istatistiği | Eşik | Karar | Kaynak |
|---|---|---|---|---|
| `row_id` | 1.000000 | 0.25 | fail | `report.json:shift.drift.feature_ks.features[3]` |
| `x1` | 0.150000 | 0.25 | pass | `report.json:shift.drift.feature_ks.features[4]` |
| `x2` | 0.650000 | 0.25 | fail | `report.json:shift.drift.feature_ks.features[5]` |
| `x3` | 0.123932 | 0.25 | pass | `report.json:shift.drift.feature_ks.features[6]` |
| `pred` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features[2]` |
| `lo` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features[1]` |
| `hi` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features[0]` |
| `y_proxy` | 0.333333 | 0.25 | fail | `report.json:shift.drift.feature_ks.features[7]` |
| `y` (hedef, `drift.target_ks`) | 0.331250 | 0.25 | fail | `report.json:shift.drift.target_ks.ks_stat` |

Ayrıca `ood.feature_range` kontrolünde max outside ratio = 1.000000 (`fail`, eşik 0.10, kaynak: `report.json:shift.ood.feature_range`) ve `ood.mahalanobis` kontrolünde mesafe oranı = 1.516192 (`pass`, eşik 2.00, kaynak: `report.json:shift.ood.mahalanobis`) ölçülmüştür.

### 4.b Evidently (`DataDriftPreset`) — kolon bazlı (12 kolon)

| Kolon | Yöntem | Değer | Eşik | Karar | Kaynak (`drift.json` metrik yapılandırması) |
|---|---|---|---|---|---|
| `row_id` | K-S p_value | 1.987767e-129 | 0.05 | Drift | `ValueDrift(column=row_id,method=K-S p_value,threshold=0.05)` |
| `x1` | K-S p_value | 0.024860 | 0.05 | Drift | `ValueDrift(column=x1,method=K-S p_value,threshold=0.05)` |
| `x2` | K-S p_value | 3.722182e-39 | 0.05 | Drift | `ValueDrift(column=x2,method=K-S p_value,threshold=0.05)` |
| `x3` | K-S p_value | 0.096779 | 0.05 | No Drift | `ValueDrift(column=x3,method=K-S p_value,threshold=0.05)` |
| `y` | K-S p_value | 8.309481e-10 | 0.05 | Drift | `ValueDrift(column=y,method=K-S p_value,threshold=0.05)` |
| `pred` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `ValueDrift(column=pred,method=K-S p_value,threshold=0.05)` |
| `lo` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `ValueDrift(column=lo,method=K-S p_value,threshold=0.05)` |
| `hi` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `ValueDrift(column=hi,method=K-S p_value,threshold=0.05)` |
| `y_proxy` | K-S p_value | 6.293809e-10 | 0.05 | Drift | `ValueDrift(column=y_proxy,method=K-S p_value,threshold=0.05)` |
| `site` | chi-square p_value | 0.999999 | 0.05 | No Drift | `ValueDrift(column=site,method=chi-square p_value,threshold=0.05)` |
| `region` | chi-square p_value | 1.000000 | 0.05 | No Drift | `ValueDrift(column=region,method=chi-square p_value,threshold=0.05)` |
| `ts` | Percentile text content drift | 0.933528 | 0.95 | Drift | `ValueDrift(column=ts,method=Percentile text content drift,threshold=0.95)` |

### 4.c Uzlaştırma (özet ↔ kolon bazlı)

- **Evidently özet metriği**: 9/12 kolon (%75.0) sürüklenmiş (`Dataset Drift: True`, eşik `drift_share=0.5`) [kaynak: `drift.json:DriftedColumnsCount`].
- **Kolon bazlı p-değerleriyle sayım**: 8/12 kolon (%66.7). Sayısal kolonlardan 8 tanesinde p-değeri < 0.05 olduğu için kayma tespit edilmiştir (`row_id, x1, x2, y, pred, lo, hi, y_proxy`). `x3` (p=0.0968) ile kategorik `site` (p=0.999999) ve `region` (p=1.0) eşik altındadır.
- **Farkın Açıklaması (9 ↔ 8)**: 9. sürüklenen kolon `ts` metin kolonudur. Bu kolonda kullanılan `Percentile text content drift` yönteminde raporlanan değer (0.933528) bir p-değeri değil, referans ve akım metinlerini ayırt etmek üzere eğitilen alan sınıflandırıcısının ROC-AUC skorudur. Karar kuralı `ROC-AUC > rastgele sınıflandırıcı yüzdeliği (~0.55)` şeklinde çalışır (kaynak: `evidently/legacy/utils/data_drift_utils.py:256`). ROC-AUC skoru rastgele sınıflandırıcı eşiğini aştığından `ts` kolonu da sürüklenmiş olarak işaretlenir. Böylece özet sayımdaki 9 kolon (8 sayısal + 1 metin) kolon bazlı sonuçlarla tam olarak uzlaşır.
- **ModelTrust tarafı**: 4 shift denetiminden 3 `fail` (`drift.feature_ks`, `drift.target_ks`, `ood.feature_range`), 1 `pass` (`ood.mahalanobis`).
- **Gözlem Notları**:
  - `x2` (enjekte edilen kayma): Her iki araçta da güçlü biçimde `fail` / `Drift`.
  - `x1`: ModelTrust pratik etki büyüklüğü eşiği (KS stat 0.15 < 0.25) altında kaldığı için `pass` verirken; Evidently istatistiksel anlamlılık (p=0.0249 < 0.05) nedeniyle `Drift` bildirmiştir. Bu, etki büyüklüğü ile hipotez testi yaklaşımı arasındaki metodoloji farkını yansıtır.
  - `row_id`: Monoton artan kimlik kolonu her iki araçta da yapay olarak kayma üretmiştir.
  - `OOD aralık ve Mahalanobis`: ModelTrust'ta bağımsız tanı kontrolleri olarak yer alırken, Evidently `DataDriftPreset` içinde doğrudan karşılığı bulunmamaktadır.
  - `Kategorik kolonlar`: ModelTrust numerik odaklı çalışırken, Evidently otomatik olarak ki-kare testi uygulamıştır.

## 5. Sözleşme farkları

1. **Cevap Verilebilirlik Semantiği (`not_assessable`)**: Evidently'de "bu girdiyle bu kontrol yapılamaz + nedeni" (`status: not_assessable`, `reason_code`) ayrımı bulunmaz; araç uygun veri türü bulduğunda çalışır, bulamadığında hata verir veya sessiz kalır. ModelTrust Lab'de eksik parametre (örn. zaman/grup kolonu verilmemesi) veya boru hattı kodu zorunluluğu açık bir sözleşme durumudur.
2. **Çıktı Ayrıntısı ve Görselleştirme**: Evidently kolon bazında ayrıntılı istatistiksel dağılımlar, histogramlar ve interaktif HTML panoları üretir. ModelTrust Lab ise görsel arayüz sunmaz; makine tarafından okunabilir JSON, hafif Markdown ve tek sayfalık tanı kartı (`card`) üretir.
3. **Eşik Yaklaşımı**: ModelTrust Lab, pratik etki büyüklüğüne odaklanan önceden belirlenmiş sezgisel eşikler (heuristic thresholds, ör. KS stat >= 0.25) kullanır. Evidently ise seçilen istatistiksel testin p-değerine (varsayılan alfa = 0.05) göre karar verir. Bu durum `x1` gibi küçük sapmalarda karar farkı yaratabilir; hangisinin doğru olduğu iddia edilmez, metodoloji farkıdır.
4. **Bağımlılık Profili ve Taşınabilirlik**: ModelTrust Lab yalnızca `numpy` ve `pandas` bağımlılığı taşır; derleme, harici C/Fortran kütüphaneleri veya ağır görselleştirme bağımlılığı içermez. Evidently ise görselleştirme, istatistik ve web servisleri için 80 paketlik geniş bir ekosisteme dayanır.

## 6. Ölçülmeyen araçlar (doküman temelli)

- **Deepchecks (AGPL)**: Bu çalışmada kurulmamış ve doğrudan çalıştırılmamıştır. AGPL lisans modeli ticari/kapalı kod tabanlarında farklı yasal yükümlülükler getirebilir. Yayınlanmış dokümanlarına göre kapsamlı bir veri ve model doğrulama paketi sunar; train/test sızıntısı, veri bütünlüğü ve sürüklenme kontrollerini içerir (`ölçülmedi (doküman)`).
- **NannyML (Apache-2.0)**: Bu çalışmada kurulmamış ve doğrudan çalıştırılmamıştır. Yayınlanmış dokümanlarına göre özellikle üretim ortamında geciken veya bulunmayan etiketler karşısında model performansını tahmin etmeye (CBPE yöntemi) ve sürüklenme zamanlamasını tespit etmeye odaklanır (`ölçülmedi (doküman)`).

## 7. Neden sıfırdan yazıldı?

ModelTrust Lab yeni bir istatistiksel yöntem icat etmez.
Araç; ağır bağımlılıklardan kaçınmak (yalnızca `numpy` ve `pandas`), telemetri ve ağ erişimi olmadan tamamen çevrimdışı çalışmak, aynı girdide bit-bit deterministik manifest üretmek ve her denetimde açık cevap verilebilirlik (`answered`/`partial`/`not_assessable`) sözleşmesi sağlamak amacıyla geliştirilmiş odaklı bir tanısal araştırma prototipidir.
Kapsamı bilinçli olarak dar tutulmuştur.

## 8. Yeniden üretim

Aşağıdaki adımlar geçici bir ortamda sonuçları yeniden üretmek için kullanılabilir:

```powershell
# 1. Geçici venv oluştur ve Evidently kur
$ev = "$env:TEMP\mt_ev_venv"
.\.venv\Scripts\python.exe -m venv $ev
& "$ev\Scripts\python.exe" -m pip install --disable-pip-version-check evidently

# 2. Veri dilimlerini üret (Windows üzerinde to_csv satır sonu os.linesep (
) kullanır, hash'ler platforma bağlıdır)
python -c "import pandas as pd; df = pd.read_csv('examples/case_study/case_study.csv').sort_values('ts', kind='mergesort'); k=int(len(df)*0.8); df.iloc[:k].to_csv('$env:TEMP/reference.csv', index=False); df.iloc[k:].to_csv('$env:TEMP/current.csv', index=False)"

# 3. ModelTrust temporal raporunu çalıştır
python -m modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --split-mode temporal --shift --out-dir "$env:TEMP/mt_rep"

# 4. Evidently raporunu çalıştır
& "$ev\Scripts\python.exe" -c "import pandas as pd; from evidently import Report; from evidently.presets import DataDriftPreset; rep=Report([DataDriftPreset()]); snap=rep.run(reference_data=pd.read_csv('$env:TEMP/reference.csv'), current_data=pd.read_csv('$env:TEMP/current.csv')); snap.save_html('$env:TEMP/drift.html')"

# 5. Geçici venv ortamı istendiğinde silinebilir
# Remove-Item -Recurse -Force $ev
```

## 9. Sınırlar

- **Kapsam**: Karşılaştırma yalnızca tek bir sentetik veri kümesi (`case_study.csv`) ve temporal bölme senaryosu üzerinde yapılmıştır.
- **Sürüm Bağımlılığı**: Bulgular ModelTrust Lab `0.0.1.dev0` ve Evidently `0.7.23` sürümleri için geçerlidir; gelecekteki sürümlerde test yöntemleri veya varsayılan eşikler değişebilir.
- **Tanısal Nitelik**: Elde edilen p-değerleri veya KS istatistikleri tanısal göstergelerdir; modelin üretim ortamındaki genel güvenilirliğine dair kesin bir garanti oluşturmaz.
