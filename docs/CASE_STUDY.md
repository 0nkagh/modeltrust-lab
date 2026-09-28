# Vaka Çalışması: Kasten Bozulmuş Sentetik Veri ile Tanı Denetimi

## 1. Amaç ve Dürüstlük Çerçevesi

Bu bir kıyaslama (benchmark) değildir.
Kusurlar veriye bilinerek enjekte edilmiştir; tespit başarısı gerçek dünya dağılımlarına genellenemez.
Sonuçlar yalnız bu veri kümesi, bu araç sürümü ve bu komutlar için geçerlidir.

Bu çalışmanın amacı, ModelTrust Lab tanı modüllerinin (`inspect`, `profile`, `leakage`, `split`, `evaluate`, `shift`, `card`, `report`) bilinen veri ve model kusurları karşısındaki davranışını, hangi kusurları tespit edebildiğini ve hangi kusurları kapsamı dışında bıraktığını şeffaf ve somut kanıtlarla belgelemektir.

## 2. Veri Kümesi Künyesi

- **Dosya yolu**: `examples/case_study/case_study.csv`
- **Satır sayısı**: 600 veri satırı (başlık dâhil 601 satır)
- **Kolon sayısı**: 12 kolon (`row_id, ts, site, region, x1, x2, x3, y, pred, lo, hi, y_proxy`)
- **RNG Seed**: `20260928`
- **Üretici komutu**: `python examples/case_study/generate_case_study.py --out-dir examples/case_study`
- **CSV SHA-256**: `9587b66886a942ee9e9589fe65f000406f6f9f40f41ba7e7bf0b5e0cf9e942da`
- **Zaman damgası (`ts`) biçimi**: `YYYY-MM-DD` (ISO-8601 takvim günü, `2024-01-01` ile `2025-08-16` arası)
- **Sayısal biçim**: Ondalık nokta, `float_format="%.6f"`, UTF-8 kodlama, LF satır sonu.

## 3. Enjekte Edilen Kusurlar

| # | Kusur Türü | Nasıl Enjekte Edildi (Kod / Ölçek) | Ölçek Referansı |
|---|---|---|---|
| D1 | **Yinelenen satırlar** | 6 satırın tüm kolonlarıyla birebir kopyası (satır 10, 20, 30, 40, 50, 60 kopyalanıp sona eklendi) | `split_dupes.csv` / `profile_dirty.csv` |
| D2 | **Eksik hücreler** | `x3` kolonu içinde 12 hücre `NaN` yapıldı | `profile_dirty.csv` |
| D3 | **Hedefe yakın kopya** | `y_proxy = 0.98 * y + N(0, 0.005)` (hedefle korelasyon > 0.999) | `leak_nearcopy.csv` |
| D4 | **Yüksek kardinaliteli id** | `row_id = 1..N` (tekilleştirici tamsayı kimlik) | `high_card_id.csv` |
| D5 | **Grup sızıntısı** | `site` ∈ {S1..S10}; her siteye sabit `y` kayması (site etkisi); rastgele bölmede gruplar iki tarafa da düşer | `leak_group_overlap.csv`, `split_groups.csv` |
| D6 | **Dağılım kayması** | Satırların son %30'unda (zaman sıralı) `x2 += 2.0` ve gürültü ölçeği 1.0 → 1.5; `ts` artan | `shift_drift.csv` |
| D7 | **Aşırı dar aralıklar** | `lo = pred - 0.2`, `hi = pred + 0.2`; aralık genişliği model artık ölçeğinden dar | `intervals_overconfident.csv` |
| D8 | **Bölgesel hata yoğunlaşması** | `region` ∈ {A, B, C}; B bölgesinde gerçek hata ~3× daha yüksek | `eval_preds.csv` |
| D9 | **Etiket gürültüsü** | Rastgele %4 satırda `y` değerine büyük sapma (±15..25) eklendi | — (araç bu kontrolü yapmaz; tespit yok) |

## 4. Gözlenen Tespitler

### D1 — Yinelenen Satırlar
- **İlgili Soru**: Q1 ("Missing or duplicate records?")
- **Koşulan Komut**: `modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --pred-col pred --group-col site --evaluate --shift --card --out-dir $t/cs_report`
- **Durum**: `answered` (tespit edildi)
- **Ham Kanıt Alıntısı**:
  ```json
  "duplicate_rows": {
    "duplicate_row_ratio": 0.01,
    "exact_duplicate_count": 6,
    "example_row_indices": [594, 595, 596, 597, 598],
    "null_equals_null": true
  }
  ```
  Ayrıca `split` komutunda `warnings: ["duplicate_rows_cross_split"]` ve `random` modunda `row_overlap_count: 3` olarak gözlenmiştir.
- **Yorum**: Araç tüm kolonları aynı olan 6 yinelenen satırı profilleme aşamasında tespit etmiş ve bölme denetiminde çapraz sızıntı uyarısı üretmiştir.

### D2 — Eksik Hücreler
- **İlgili Soru**: Q1 ("Missing or duplicate records?")
- **Koşulan Komut**: `modeltrust report` (ve `card`)
- **Durum**: `answered` (tespit edildi)
- **Ham Kanıt Alıntısı**:
  ```json
  {
    "name": "x3",
    "role": "feature",
    "observed_dtype": "float64",
    "is_numeric": true,
    "missing_count": 12,
    "missing_ratio": 0.02
  }
  ```
- **Yorum**: `x3` kolonundaki 12 eksik değer (oran: %2.0) profil özetinde tam sayı ve oran olarak bildirilmiştir.

### D3 — Hedefe Yakın Kopya
- **İlgili Soru**: Q2 ("Target leakage or future leakage?")
- **Koşulan Komut**: `modeltrust leakage --input examples/case_study/case_study.csv --target-col y --group-col site`
- **Durum**: `answered` (check: `fail`, tespit edildi)
- **Ham Kanıt Alıntısı**:
  ```json
  {
    "name": "target_copy_near",
    "status": "performed",
    "result": "fail",
    "detail": "Target near copy found",
    "evidence": [
      {
        "abs_correlation": 1.0,
        "column": "y_proxy",
        "equality_ratio": 0.0
      }
    ]
  }
  ```
- **Yorum**: `y_proxy` hedefle 0.999 eşiğinin üzerinde mutlak korelasyona sahip olduğundan `target_copy_near` tarafından sızıntı göstergesi olarak bayraklandırılmıştır.

### D4 — Yüksek Kardinaliteli Kimlik
- **İlgili Soru**: Q2 ("Target leakage or future leakage?")
- **Koşulan Komut**: `modeltrust leakage` / `report`
- **Durum**: `performed` (check: `pass`, **tespit edilmedi**)
- **Ham Kanıt Alıntısı**:
  ```json
  {
    "name": "index_like_feature",
    "status": "performed",
    "result": "pass",
    "detail": "",
    "evidence": null
  }
  ```
- **Yorum**: `row_id` kolonu tamsayıdır; ancak D1 kusuruyla eklenen yinelenen satırlar nedeniyle seride ardışık farkların tümü kesin pozitif (`diffs > 0`) kalmamış, bu sebeple katı monotonluk koşulu sağlanamadığından `index_like_feature` tetiklenmemiştir. Şartnameye sadık kalınmış, veride yapay düzeltme yapılmamıştır.

### D5 — Grup Sızıntısı
- **İlgili Soru**: Q3 ("Train/test split strategy and group/time leakage?")
- **Koşulan Komut**: `modeltrust split --input examples/case_study/case_study.csv --target-col y --group-col site --time-col ts`
- **Durum**: `answered` (rastgele bölmede `fail`, grup bölmesinde `pass`)
- **Ham Kanıt Alıntısı**:
  ```json
  "random": {
    "group_overlap": {
      "count": 10,
      "groups": ["S1", "S10", "S2", "S3", "S4"],
      "ratio_of_smaller": 1.0,
      "status": "performed"
    }
  },
  "group": {
    "group_overlap": {
      "count": 0,
      "groups": [],
      "ratio_of_smaller": 0.0,
      "status": "performed"
    }
  }
  ```
- **Yorum**: `random` modunda 10 sitenin tamamı eğitim ve test kümeleri arasında sızmış (`ratio_of_smaller: 1.0`), buna karşılık `group` modunda grupların kesin ayrıklığı (`count: 0`) doğrulanmıştır.

### D6 — Dağılım Kayması
- **İlgili Soru**: Q6 ("Distribution drift?") ve Q7 ("Out-of-distribution (OOD) data?")
- **Koşulan Komut**: `modeltrust report --input examples/case_study/case_study.csv --target-col y --time-col ts --shift ...`
- **Durum**: `performed` (check: `pass`, **eşik altı / tespit edilmedi**)
- **Ham Kanıt Alıntısı**:
  ```json
  {
    "name": "drift.feature_ks",
    "status": "performed",
    "result": "pass",
    "detail": "Diagnostic indicator: max KS stat=0.114583 across features (heuristic threshold 0.25)"
  },
  {
    "name": "ood.feature_range",
    "status": "performed",
    "result": "pass",
    "detail": "Diagnostic indicator: 0.008333 max outside ratio (heuristic threshold 0.10)"
  }
  ```
- **Yorum**: `report --shift` komutu varsayılan olarak rastgele bölme uyguladığı için zamanın son %30'undaki kayma eğitim ve test alt kümelerine eşit dağılmış, KS istatistiği 0.1146 seviyesinde kalarak 0.25 sezgisel eşiğini aşmamıştır. Zaman tabanlı bir `shift` çağrısı olmaksızın rastgele bölmede kayma sezilmemiştir.

### D7 — Aşırı Dar Aralıklar
- **İlgili Soru**: Q8 ("Uncertainty intervals?")
- **Koşulan Komut**: `modeltrust evaluate --input examples/case_study/case_study.csv --target-col y --lower-col lo --upper-col hi --nominal-coverage 0.9`
- **Durum**: `performed` (check: `fail`, tespit edildi)
- **Ham Kanıt Alıntısı**:
  ```json
  "uncertainty": {
    "coverage": 0.191667,
    "coverage_gap": -0.708333,
    "nominal_coverage": 0.9,
    "status": "performed",
    "warnings": ["non_nominal_coverage"]
  }
  ```
  Ve kontrol sonucu: `"name": "interval.nominal_gap", "result": "fail", "detail": "gap=-0.708333"`.
- **Yorum**: %90 nominal kapsama karşılık gerçekleşen kapsam %19.17 olarak ölçülmüş, fark toleransı (0.05) aşıldığı için aralık güvenilirliği doğrudan fail olarak raporlanmıştır.

### D8 — Bölgesel Hata Yoğunlaşması
- **İlgili Soru**: Q5 ("Subpopulation or fairness disparities?")
- **Koşulan Komut**: `modeltrust report` (ve `evaluate`)
- **Durum**: `answered` (koşulan komutta `--group-col site` verildiği için site düzeyinde değerlendirildi)
- **Ham Kanıt Alıntısı**:
  `report` çıktısında grup hataları site bazında raporlanmıştır:
  ```json
  "worst_by_mae": ["S5", "S8", "S4"]
  ```
- **Yorum**: Koşulan komutlarda `--group-col site` kullanıldığı için alt-küme analizi site düzeyinde çalışmıştır. Bölgesel (`region`) eşitsizlik bu komutta grup kolonu olarak girilmediği için doğrudan incelenmemiştir; girdi parametresi ne verildiyse araç yalnız onu denetler.

### D9 — Etiket Gürültüsü
- **İlgili Soru**: —
- **Koşulan Komut**: Tüm komutlar
- **Durum**: **Tespit edilmedi / Kontrol mevcut değil**
- **Yorum**: ModelTrust Lab v1 tanı kapsamında ham tablolarda etiket gürültüsünü (ground-truth label corruption) doğrudan tespit eden bağımsız bir denetim modülü bulunmamaktadır. Bu durum tasarım gereği kapsam dışıdır ve bir bulgu olarak not edilmiştir.

## 5. Tespit Edilmeyenler ve Değerlendirilemeyenler

1. **D9 (Etiket Gürültüsü)**: Yukarıda açıklandığı üzere, araç bu kontrolü yapacak modüle sahip değildir (`kontrol mevcut değil`).
2. **D4 (Yüksek Kardinaliteli ID)**: `row_id` tamsayıdır ancak D1 ile gelen kopyalar nedeniyle katı monotonluk bozulduğundan `index_like_feature` tetiklenmemiştir.
3. **D6 (Dağılım Kayması)**: `report --shift` çağrısında `--split-mode temporal` verilmediğinde varsayılan rastgele bölme kullanıldığı için KS eşiği aşılmamıştır.
4. **Değerlendirilemeyen Kontroller (`not_assessable`)**:
   - `leakage.preprocess.fit_scope` (`requires_pipeline_code`): Bir CSV tablosundan veri ön işleme adımlarının (scaler, encoder) yalnız eğitim kümesinde fit edilip edilmediği anlaşılamaz. Boru hattı kodu zorunludur.
   - `leakage.subset_row_overlap`, `subset_group_overlap`, `subset_time_ranges` (`not_provided`): Girdi tablosunda ayrık bir `subset` kolonu (örn. `train`/`test`) sağlanmamıştır.
   - `card` tekil koşusunda (C1) `shift.drift.feature_ks` (`not_provided`): `card` komutuna `--time-col` parametresi girilmediğinde zaman serisi kayması değerlendirilemez.

## 6. Kapsam Envanteri

`cs_report/card.json` içinden alınan ham denetim özeti (`checks_summary`):

```json
[
  {"module": "leakage", "total": 12, "performed": 8, "fail": 2, "not_assessable": 4},
  {"module": "split", "total": 3, "performed": 3, "fail": 0, "not_assessable": 0},
  {"module": "shift", "total": 4, "performed": 4, "fail": 0, "not_assessable": 0}
]
```

Bu envanter, aracın neleri fiilen değerlendirdiğini, neleri fail olarak bayraklandırdığını ve nelerin eksik parametre ya da boru hattı kodu gereksinimi nedeniyle değerlendirilemediğini net biçimde göstermektedir.

## 7. Sınırlar

- **Genellenemezlik**: Bu vaka çalışmasında elde edilen tespit ve başarısızlıklar yalnızca kasten tasarlanan sentetik `case_study.csv` verisi için geçerlidir; farklı veri kümelerine, farklı gürültü rejimlerine veya karmaşık doğrusal olmayan ilişkilere genellenemez.
- **Tek sürüm**: Sonuçlar ModelTrust Lab `0.0.1.dev0` sürümünün mevcut eşikleri ve kuralları altında elde edilmiştir.
- **Yalnızca tanı göstergesi**: Flaglenen bulgular kesin kanıt değil tanısal göstergedir; bayrak üretilmemesi de sızıntı veya kusur bulunmadığının kanıtı sayılamaz.
