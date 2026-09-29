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
- **Telemetri Bulgusu**: Paket kod tabanında (`evidently/telemetry.py`) `iterative_telemetry` kütüphanesine ve `DO_NOT_TRACK_ENV = "DO_NOT_TRACK"` ortam değişkenine rastlanmıştır (`TELEMETRY_ADDRESS = "https://telemetry-321112.ew.r.appspot.com/post_data"`). Koşu sırasında `DO_NOT_TRACK=1` tanımlanarak telemetri devre dışı bırakılmıştır.

## 3. Girdi hizalaması

Her iki araca da birebir aynı veri satırları ve aynı dilimler sağlanmıştır.

- **Kaynak Veri**: `examples/case_study/case_study.csv` (600 satır, 12 kolon, SHA-256: `9587B66886A942EE9E9589FE65F000406F6F9F40F41BA7E7BF0B5E0CF9E942DA`)
- **Bölme Yöntemi**: Zaman damgasına (`ts`) göre kararlı sıralama (`mergesort`), ilk %80 (480 satır) referans/eğitim, son %20 (120 satır) test/akım dilimi olarak ayrılmıştır.
- **ModelTrust Eşlemesi**: `modeltrust report --split-mode temporal` (`report.json` içindeki `split.modes.temporal` alanında `n_train: 480`, `n_test: 120`).
- **Evidently Eşlemesi**: `Report.run(reference_data=ref, current_data=cur)` çağrısında `ref` ve `cur` dilimleri kullanılmıştır.
- **Dilim Dosyaları**:
  - `reference.csv`: 480 satır, SHA-256: `C8168216AAA1A859B25194A6AEE8D4F04774844FD82B71AD2D79FBFDEC3FD26D`
  - `current.csv`: 120 satır, SHA-256: `0F1502DF4EA780D77B70881C9A080CA2200F798139B88442ADA0CC02A724788D`
- **Kolonlar**: `['row_id', 'ts', 'site', 'region', 'x1', 'x2', 'x3', 'y', 'pred', 'lo', 'hi', 'y_proxy']`
- **Doğrulama**: Aynı satırların iki araca da verildiği SHA-256 özetleriyle kesinleştirilmiştir.

## 4. Ölçülen sonuçlar (yan yana)

Aşağıdaki tablo, temporal bölme üzerinde ModelTrust Lab ve Evidently (`DataDriftPreset`) tarafından üretilen tanı sonuçlarını yan yana özetlemektedir.

| Kontrol / Değişken | ModelTrust Lab (ham değer, eşik) | Evidently (ham değer, eşik / kural) | Not |
|---|---|---|---|
| `x2` (enjekte edilen kayma) | KS stat = 0.650000, eşik 0.25 (`fail`) [kaynak: `report.json:shift.drift.feature_ks`] | KS p-value = 3.722e-39, eşik 0.05 (Drift) [kaynak: `drift.json:ValueDrift(x2)`] | Her iki araç da `x2` üzerindeki yapay dağılım kaymasını güçlü biçimde tespit etti. |
| `x1` (küçük sapma) | KS stat = 0.150000, eşik 0.25 (`pass`) [kaynak: `report.json:shift.drift.feature_ks`] | KS p-value = 0.024860, eşik 0.05 (Drift) [kaynak: `drift.json:ValueDrift(x1)`] | ModelTrust etki büyüklüğü eşiği (0.25) altında kaldığı için geçirdi; Evidently p < 0.05 nedeniyle kayma bildirdi. |
| `x3` (eksik verili kolon) | KS stat = 0.123932, eşik 0.25 (`pass`) [kaynak: `report.json:shift.drift.feature_ks`] | KS p-value = 0.096779, eşik 0.05 (No Drift) [kaynak: `drift.json:ValueDrift(x3)`] | Her iki araç da kayma tespit etmedi (eşik altı / p > 0.05). |
| `row_id` (tamsayı kimlik) | KS stat = 1.000000, eşik 0.25 (`fail`) [kaynak: `report.json:shift.drift.feature_ks`] | KS p-value = 1.988e-129, eşik 0.05 (Drift) [kaynak: `drift.json:ValueDrift(row_id)`] | Monoton artan indeks her iki tarafta da zaman dilimleri arası kayma olarak bayraklandı. |
| `y_proxy` (hedef kopyası) | KS stat = 0.333333, eşik 0.25 (`fail`) [kaynak: `report.json:shift.drift.feature_ks`] | KS p-value = 6.294e-10, eşik 0.05 (Drift) [kaynak: `drift.json:ValueDrift(y_proxy)`] | Her iki araç da kayma tespit etti. |
| `pred, lo, hi` | KS stat = 0.314583, eşik 0.25 (`fail`) [kaynak: `report.json:shift.drift.feature_ks`] | KS p-value = 7.167e-09, eşik 0.05 (Drift) [kaynak: `drift.json:ValueDrift(pred)`] | Her iki araç da tahmin ve aralık kolonlarında kayma tespit etti. |
| Hedef kolonu `y` | KS stat = 0.331250, eşik 0.25 (`fail`) [kaynak: `report.json:shift.drift.target_ks`] | KS p-value = 8.309e-10, eşik 0.05 (Drift) [kaynak: `drift.json:ValueDrift(y)`] | Her iki araç da hedef dağılımı kaymasını tespit etti. |
| Kategorik (`site`, `region`) | Hesaplanmadı (`shift` numerik odaktadır) | `site`: chi-square p=0.999999, `region`: chi-square p=1.0 (No Drift) | Evidently kategorik kolonlarda otomatik ki-kare testi uyguladı. |
| Aralık Dışı Oran (OOD Range) | max outside ratio = 1.000000 (`row_id`), `x1`/`x2` = 0.008333, eşik 0.10 (`fail`) [kaynak: `report.json:shift.ood.feature_range`] | Karşılığı yok (DataDriftPreset kapsamında değil) | ModelTrust eğitim kümesi min/max aralığı dışına çıkan satır oranını bağımsız OOD metriği olarak ölçer. |
| Mahalanobis Mesafesi | Oran = 1.516192, eşik 2.00 (`pass`) [kaynak: `report.json:shift.ood.mahalanobis`] | Karşılığı yok (DataDriftPreset kapsamında değil) | ModelTrust çok değişkenli mesafe oranını kontrol eder; Evidently önayarlı sürüklenme raporunda yer almaz. |
| Veri Kümesi Sürüklenme Kararı | 4 kontrolden 3 `fail`, 1 `pass` [kaynak: `report.json:shift.checks`] | 9 / 12 kolon sürüklenmiş (%75.0 > %50 eşiği, Dataset Drift) [kaynak: `drift.json:DriftedColumnsCount`] | Her iki araç da veri kümesinin bütününde sürüklenme olduğu sonucuna vardı. |

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
& "$ev\Scripts\python.exe" -m pip install --disable-pip-version-check evidently

# 2. Veri dilimlerini üret
python -c "import pandas as pd; df = pd.read_csv('examples/case_study/case_study.csv').sort_values('ts', kind='mergesort'); k=int(len(df)*0.8); df.iloc[:k].to_csv('$env:TEMP/ref.csv', index=False); df.iloc[k:].to_csv('$env:TEMP/cur.csv', index=False)"

# 3. ModelTrust temporal raporunu çalıştır
python -m modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --split-mode temporal --shift --out-dir "$env:TEMP/mt_rep"

# 4. Evidently raporunu çalıştır
& "$ev\Scripts\python.exe" -c "import pandas as pd; from evidently import Report; from evidently.presets import DataDriftPreset; rep=Report([DataDriftPreset()]); snap=rep.run(reference_data=pd.read_csv('$env:TEMP/ref.csv'), current_data=pd.read_csv('$env:TEMP/cur.csv')); snap.save_html('$env:TEMP/drift.html')"

# 5. Geçici venv ortamı istendiğinde silinebilir
# Remove-Item -Recurse -Force $ev
```

## 9. Sınırlar

- **Kapsam**: Karşılaştırma yalnızca tek bir sentetik veri kümesi (`case_study.csv`) ve temporal bölme senaryosu üzerinde yapılmıştır.
- **Sürüm Bağımlılığı**: Bulgular ModelTrust Lab `0.0.1.dev0` ve Evidently `0.7.23` sürümleri için geçerlidir; gelecekteki sürümlerde test yöntemleri veya varsayılan eşikler değişebilir.
- **Tanısal Nitelik**: Elde edilen p-değerleri veya KS istatistikleri tanısal göstergelerdir; modelin üretim ortamındaki genel güvenilirliğine dair kesin bir garanti oluşturmaz.
