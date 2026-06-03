# Test & Doğrulama Raporu

> 3. Kişi (Fatih) — Test & Doğrulama görevi. Tüm sonuçlar `test_dogrulama.ipynb`'in
> gerçek koşumundan ve `tests/test_kanonik.py` pytest çıktısından alınmıştır.

## 1. Yöntem

Başlangıçta iki notebook **farklı sorgular** çalıştırıyordu, bu yüzden eşdeğerlik testi
anlamsızdı. Tek bir **kanonik sorgu** belirlendi (Zühre'nin vitrin sorgusu) ve hem Polars
(lazy) hem pandas ile uygulanıp birebir karşılaştırıldı.

**Kanonik sorgu:**
- Filtre: `kalkis_tarihi` "2024" ile başlar **VE** `ucus_tipi == "ic_hat"`
- Group by: `[kalkis_havaalani, havayolu]`
- Agregasyon: `toplam_gelir`=bilet_fiyati.sum, `ort_gecikme_dk`=gecikme_dk.mean, `ucus_adedi`=adet
- Sıralama: `toplam_gelir` azalan → **50 satır × 5 sütun**

Mantık `kanonik.py` modülünde tek kaynak olarak yaşar; notebook ve testler onu import eder.

## 2. Girdi Sabitleme (tekrarlanabilirlik)

| | Değer |
|---|---|
| Veri dosyası | `data/ucus_verisi.csv` |
| MD5 | `a7a4ca24173b4f4b101c0ca70bf7a9d7` (notebook'ta assert edilir) |
| Şekil | (150000, 8) |
| Ortam | Python 3.14.5 · polars 1.41.2 · pandas 3.0.3 · numpy 2.4.6 · pyarrow 24.0.0 |

İki motor da aynı commit'li CSV baytlarını okur; testler aynı girdiyi MD5 ile sabitler.

## 3. Eşdeğerlik Sonucu: **PASS ✅**

| Kontrol | Sonuç |
|---|---|
| Şekil eşit (50×5) | ✅ |
| Sütun adları eşit | ✅ |
| Grup kümesi eşit | ✅ |
| `ucus_adedi` TAM eşit (int) | ✅ |
| `toplam_gelir`, `ort_gecikme_dk` toleranslı eşit (`rtol=1e-9, atol=1e-6`) | ✅ |

**dtype notu:** Polars `ucus_adedi`'yi `u32`, pandas `int64` üretir; karşılaştırmadan önce
`normalize()` ikisini de `int64`'e çevirir (kozmetik fark, gerçek fark değil).

**Örnek sonuç (ilk 3 satır, iki motorda da aynı):**

| kalkis_havaalani | havayolu | toplam_gelir | ort_gecikme_dk | ucus_adedi |
|---|---|---|---|---|
| IST | THY | 16.962.276,01 | 20,15 | 6828 |
| IST | Pegasus | 12.640.409,14 | 19,31 | 5052 |
| SAW | THY | 9.771.611,58 | 20,30 | 3919 |

## 4. Edge-Case Sonuçları

| Senaryo | Polars | pandas | Eşit? | Not |
|---|---|---|---|---|
| Boş DataFrame (yalnız başlık) | (0, 5) | (0, 5) | ✅ | Bkz. bulgu (a) |
| Null `ucus_tipi` (filtre dışı) | (0, 5) | (0, 5) | ✅ | Bkz. bulgu (b) |
| Tek satır | (1, 5) | (1, 5) | ✅ | `ucus_adedi=1`, `toplam_gelir=1000.0` |

**Yakalanan bulgular ve düzeltmeler:**
- **(a) Polars boş-girdi şema çıkarımı:** Boş CSV'de Polars sayısal sütunları `str`
  tahmin edip `.sum()`'da patlıyordu. `scan_csv(schema_overrides={...})` ile sayısal
  tipler sabitlendi. Gerçek 150k veride aynı tipler → davranış değişmez.
- **(b) Boş groupby-agg dtype'ı:** pandas boş çerçevede float sütunu `object` üretip
  `assert_allclose`'u patlatıyordu. `normalize()` float sütunları `float64`'e sabitler.
- **(c) Null hizalaması:** Polars `filter` null'ları eler; pandas tarafı
  `str.startswith("2024", na=False)` ile aynı semantiğe hizalandı.

## 5. Zaman Ölçümü (N=5 tekrar ortalaması)

| Motor | Süre |
|---|---|
| Polars (lazy) | ~5 ms |
| pandas (eager) | ~66 ms |

Aynı kanonik sorgu, aynı tam 150k-satır girdi. Polars bu işte **~13× daha hızlı**.
Tek-seferlik ölçüm gürültülü olduğundan 5 tekrar ortalaması alındı.

## 6. Birim Test Özeti

`python -m pytest` → **9 passed** (kanonik sorgu şekil/sütun ×2, grup kümesi, eşdeğerlik
pozitif + negatif, 3 edge-case, zaman ölçümü).

## 7. Uzlaştırma Notu (neyin değiştiği)

Başlangıçta:
- `polars_pipeline.ipynb`: filtre `2024 & ic_hat`, grup `[kalkis_havaalani, havayolu]`, gelir analizi.
- `pandas_karsilastirma.ipynb`: filtre `gecikme>30 & fiyat>2000`, grup `[havayolu, ucus_tipi]`.

İki sorgu farklıydı (hatta `sum`/`mean` rolleri terstti). Kanonik sorgu olarak Polars
vitrin sorgusu seçildi; eşdeğerlik bu sorgu üzerinde **bağımsız** `test_dogrulama.ipynb`
ile kanıtlandı. Takım notebook'larına dokunulmadı.

## 8. Açık Takım Maddeleri (test kapsamı dışında)

- **Dilara:** `pandas_karsilastirma.ipynb`'i kanonik sorguya hizala; cell-10 ölçekleme
  hatası (Polars her iterasyonda tam dosyayı işliyor) ve bellek metriği (girdi vs çıktı)
  düzeltilmeli; `karsilastirma_sonuclari.md` + "Ne zaman Polars" paragrafı yazılmalı.
- **Takım/Zühre:** Veride %10,1 (15.161/150.000) satır `kalkis_havaalani == varis_havaalani`
  (kendine uçuş) — filtrele-mi-belgele kararı. (Kanonik sorgu kalkış-bazlı olduğundan bu
  anomali eşdeğerliği etkilemez, ama "gerçekçi veri" kriterini zayıflatır.)
- **Genel:** Veri dosyası adı `ucus_verisi.csv` (spec'te `sentetik_veri.csv`) — belgelenmeli.
