# Dış Araç Karşılaştırması: Evidently

## 1. Amaç ve dürüstlük çerçevesi

Bu bir kıyaslama (benchmark) değildir.
Bu çalışma, ModelTrust Lab'in tanı denetim sonuçlarını mevcut ve yaygın bir açık kaynaklı veri sürüklenme aracı olan Evidently ile yan yana koyarak sözleşme, yöntem ve çıktı farklarını somut biçimde belgelemeyi amaçlar.
Çalışma tek araç (Evidently), tek sürüm (0.7.23), tek veri kümesi (`case_study.csv`) ve tek tarih (2026-09-29) ile sınırlandırılmıştır.
Araçlar arasında bir üstünlük iddiasında ("daha iyi", "üstün", "rakipsiz") bulunulmaz; yalnızca doğrudan gözlenen değerler, yöntem seçimleri ve sözleşme semantikleri tarafsız olarak aktarılır.
Evidently, açık kaynak dünyasında tabular veri kalitesi ve sürüklenme izlemede en yaygın referans kabul edildiği için karşılaştırma aracı olarak seçilmiştir.

## 2. Ortam ve sürümler

- **Tarih**: 2026-09-29
- **Platform**: Microsoft Windows 10.0.26200, Win32NT, PowerShell Core 7.6.6
- **ModelTrust Lab Sürümü**: 0.0.1.dev0
- **Evidently Sürümü**: 0.7.23 — Python 3.12.8, geçici sanal ortam `$env:TEMP\mt_ev_venv`
- **Kurulum Komutu**: `& "$env:TEMP\mt_ev_venv\Scripts\python.exe" -m pip install --disable-pip-version-check "evidently==0.7.23"`
- **`pyvenv.cfg` içeriği**:
  ```ini
  home = C:\Users\agah\AppData\Local\Programs\Python\Python312
  include-system-site-packages = false
  version = 3.12.8
  executable = C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe
  command = C:\Users\agah\Documents\modeltrust-lab\.venv\Scripts\python.exe -m venv C:\Users\agah\AppData\Local\Temp\mt_ev_venv
  ```
- **Pip dökümü (Evidently venv)**: 80 paket, SHA-256: `DD0004C1F9CBE8D279D28A1F0D897DEA7D2B519E158E595719033BA302BB7925`. İlk 20 paket:
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
- **Telemetri**: Koşular `DO_NOT_TRACK=1` ve `ITERATIVE_DO_NOT_TRACK=1` ile yapılmıştır; kurulu `iterative_telemetry` paketi `DO_NOT_TRACK_ENV = "ITERATIVE_DO_NOT_TRACK"` anahtarını okumakta ve `is_enabled()` içinde `os.environ.get(DO_NOT_TRACK_ENV, None) is None` koşulunu kullanmaktadır (kaynak: `iterative_telemetry/__init__.py:29-30, 164-169`).

## 3. Girdi hizalaması

Her iki araca da birebir aynı veri satırları ve aynı dilimler sağlanmıştır.

- **Kaynak Veri**: `examples/case_study/case_study.csv` (600 satır, 12 kolon, SHA-256: `9587B66886A942EE9E9589FE65F000406F6F9F40F41BA7E7BF0B5E0CF9E942DA`)
- **Bölme Yöntemi**: Zaman damgasına (`ts`) göre kararlı sıralama, ilk %80 (480 satır) referans/eğitim, son %20 (120 satır) test/akım dilimi olarak ayrılmıştır.
- **ModelTrust Eşlemesi**: `report.json` içindeki `split.modes.temporal` (ve `shift.split.mode: "temporal"`) alanında `n_train: 480`, `n_test: 120`. `time_ranges`: `train_max: 2025-04-18`, `test_min: 2025-04-19`. Blok sıralama kuralını doğrudan metin olarak belirtmez; ancak `ts` kolonunun artan sıralanmasıyla ilk 480 satır eğitim, son 120 satır test olarak ayrılmış ve `report.json:split.modes.temporal.train_row_indices_sha256` ile kilitlenmiştir.
- **Evidently Eşlemesi**: `Report.run(reference_data=ref, current_data=cur)` çağrısında `reference.csv` ve `current.csv` dilimleri kullanılmıştır.
- **Dilim Dosyaları**:
  - `reference.csv`: 480 satır, SHA-256: `C8168216AAA1A859B25194A6AEE8D4F04774844FD82B71AD2D79FBFDEC3FD26D`
  - `current.csv`: 120 satır, SHA-256: `0F1502DF4EA780D77B70881C9A080CA2200F798139B88442ADA0CC02A724788D`
- **Kolonlar**: `['row_id', 'ts', 'site', 'region', 'x1', 'x2', 'x3', 'y', 'pred', 'lo', 'hi', 'y_proxy']`

## 4. Ölçülen sonuçlar (yan yana)

*Koşu Künyesi: Yeni API kanonik koşusu, 2026-09-29. Çıktı dosyası `drift.json` SHA-256: `9EE1D72256B63C45B7E0173F9959B25A4903BB4DC3D40AA885F987984FD2DEA1`.*

### 4.a ModelTrust Lab (temporal bölme) — kolon bazlı KS

| Kolon | KS istatistiği | Eşik | Karar | Kaynak |
|---|---|---|---|---|
| `row_id` | 1.000000 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.row_id` |
| `x1` | 0.150000 | 0.25 | pass | `report.json:shift.drift.feature_ks.features.x1` |
| `x2` | 0.650000 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.x2` |
| `x3` | 0.123932 | 0.25 | pass | `report.json:shift.drift.feature_ks.features.x3` |
| `pred` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.pred` |
| `lo` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.lo` |
| `hi` | 0.314583 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.hi` |
| `y_proxy` | 0.333333 | 0.25 | fail | `report.json:shift.drift.feature_ks.features.y_proxy` |
| `y` (hedef, `drift.target_ks`) | 0.331250 | 0.25 | fail | `report.json:shift.drift.target_ks.ks_stat` |

*Not: ModelTrust tanı raporunda kategorik kolonlar (`site`, `region`) ve zaman damgası kolonu (`ts`) için iki örneklemli KS drift metriği hesaplanmaz.*

### 4.b Evidently (`DataDriftPreset`, Yeni API) — kolon bazlı (12 kolon)

| Kolon | Yöntem | Değer | Eşik | Karar | Kaynak (`drift.json` metrik yapılandırması) |
|---|---|---|---|---|---|
| `row_id` | K-S p_value | 1.987767e-129 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `x1` | K-S p_value | 0.024860 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `x2` | K-S p_value | 3.722182e-39 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `x3` | K-S p_value | 0.096779 | 0.05 | No Drift | `evidently:metric_v2:ValueDrift` |
| `y` | K-S p_value | 8.309481e-10 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `pred` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `lo` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `hi` | K-S p_value | 7.167164e-09 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `y_proxy` | K-S p_value | 6.293809e-10 | 0.05 | Drift | `evidently:metric_v2:ValueDrift` |
| `site` | chi-square p_value | 0.999999 | 0.05 | No Drift | `evidently:metric_v2:ValueDrift` |
| `region` | chi-square p_value | 1.000000 | 0.05 | No Drift | `evidently:metric_v2:ValueDrift` |
| `ts` | Percentile text content drift | 0.933528 | 0.95 | Drift | `evidently:metric_v2:ValueDrift` |

### 4.c Uzlaştırma (özet ↔ kolon bazlı)

- **Evidently özet metriği**: `DriftedColumnsCount(drift_share=0.5)` -> `{'count': 9.0, 'share': 0.75}` (9/12 kolon sürüklenmiş) [kaynak: `drift.json:DriftedColumnsCount` — `evidently:metric_v2:DriftedColumnsCount`].
- **Kolon bazlı sayım**: 8/12 sayısal/kategorik kolon (`row_id, x1, x2, y, pred, lo, hi, y_proxy`) eşik değerini (0.05) aştığı için kayma tespit edilmiştir.
- **Farkın Açıklaması (9 ↔ 8)**: 9. sürüklenen kolon `ts` metin kolonudur. Kütüphane kaynak kodu incelendiğinde (`evidently/legacy/calculations/stattests/text_content_drift.py:10-15` ve `evidently/legacy/utils/data_drift_utils.py:224-257`), `ts` için alan sınıflandırıcısı eğitildiği görülür. Karar kuralı "ROC-AUC > rastgele sınıflandırıcı yüzdeliği (~0.55)" şeklinde çalışmaktadır; `ts` için ROC-AUC skoru 0.9335'tir.
- **İki Kod Yolu (API Farkı)**: Aynı sürümde iki API yolu aynı dilimlerde farklı değerler üretti; kanonik yol (Yeni API: `evidently.Report`) §4.b'dedir. Legacy yol (Eski API: `evidently.report.Report` ve `evidently.metric_preset.DataDriftPreset`) çalıştırılamamıştır (`ModuleNotFoundError`).
- **ModelTrust tarafı**: 4 shift denetiminden 3 `fail` (`drift.feature_ks`, `drift.target_ks`, `ood.feature_range`), 1 `pass` (`ood.mahalanobis`).
- **Gözlem Notları**:
  - `x1`: ModelTrust pratik etki büyüklüğü eşiği (KS stat 0.15 < 0.25) altında kaldığı için `pass` verirken; Evidently istatistiksel anlamlılık (p=0.0249 < 0.05) nedeniyle `Drift` bildirmiştir. Bu, etki büyüklüğü ile hipotez testi yaklaşımı arasındaki metodoloji farkını yansıtır.
  - `x2` (enjekte edilen kayma): Her iki araçta da güçlü biçimde `fail` / `Drift`.
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
python -m venv $ev
& "$ev\Scripts\python.exe" -m pip install --disable-pip-version-check "evidently==0.7.23"

# 2. Veri dilimlerini üret (Windows üzerinde to_csv satır sonu \r\n kullanır, hash'ler platforma bağlıdır)
$script = @'
import os, pandas as pd
df = pd.read_csv("examples/case_study/case_study.csv")
df_sorted = df.sort_values("ts").reset_index(drop=True)
cmp_dir = os.path.join(os.environ["TEMP"], "mt_cmp")
os.makedirs(cmp_dir, exist_ok=True)
df_sorted.iloc[:480].to_csv(os.path.join(cmp_dir, "reference.csv"), index=False)
df_sorted.iloc[480:].to_csv(os.path.join(cmp_dir, "current.csv"), index=False)
'@
python -c $script

# 3. ModelTrust temporal raporunu çalıştır
python -m modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --split-mode temporal --shift --out-dir "$env:TEMP/mt_rep"

# 4. Evidently raporunu çalıştır (Yeni API kanonik koşusu)
$ev_script = @'
import os, json
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

temp = os.environ["TEMP"]
ref = pd.read_csv(os.path.join(temp, "mt_cmp", "reference.csv"))
cur = pd.read_csv(os.path.join(temp, "mt_cmp", "current.csv"))

rep = Report([DataDriftPreset()])
snap = rep.run(reference_data=ref, current_data=cur)

out_dir = os.path.join(temp, "mt_cmp_ev")
os.makedirs(out_dir, exist_ok=True)
snap.save_html(os.path.join(out_dir, "drift.html"))
data = snap.dict()
with open(os.path.join(out_dir, "drift.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
'@
$env:DO_NOT_TRACK = "1"
$env:ITERATIVE_DO_NOT_TRACK = "1"
& "$ev\Scripts\python.exe" -c $ev_script
```

## 9. Sınırlar

- **Kapsam**: Karşılaştırma yalnızca tek bir sentetik veri kümesi (`case_study.csv`) ve temporal bölme senaryosu üzerinde yapılmıştır.
- **Sürüm Bağımlılığı**: Bulgular ModelTrust Lab `0.0.1.dev0` ve Evidently `0.7.23` sürümleri için geçerlidir; gelecekteki sürümlerde test yöntemleri veya varsayılan eşikler değişebilir.
- **Tanısal Nitelik**: Elde edilen p-değerleri veya KS istatistikleri tanısal göstergelerdir; modelin üretim ortamındaki genel güvenilirliğine dair kesin bir garanti oluşturmaz.
