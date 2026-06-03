# Pandas vs Polars — Karşılaştırma Sonuçları

> Kaynak: `pandas_karsilastirma.ipynb` (gerçek koşum). Tüm ölçümler aynı kanonik sorgu ve
> aynı `data/ucus_verisi.csv` (150.000 satır) üzerinde, her iki motorda da **simetrik**
> (CSV okuma dahil) alınmıştır.

## Kanonik Sorgu

2024 yılı **iç hat** uçuşları → `kalkis_havaalani` + `havayolu` bazında:
`toplam_gelir` (bilet_fiyati toplamı), `ort_gecikme_dk` (gecikme ortalaması),
`ucus_adedi` (uçuş sayısı), `toplam_gelir`'e göre azalan. Sonuç: **50 satır**.

Hem Polars (lazy `scan_csv`) hem pandas (`read_csv`) aynı sorguyu uygular; sonuçlarının
**birebir eşdeğer** olduğu notebook'ta doğrulanır (şekil/sütun/grup/int-tam/float-toleranslı):
**EŞDEĞER ✅**.

## Süre & Bellek (tam veri, 150K satır)

| Kütüphane | Süre | Bellek (girdi çerçevesi) |
|---|---|---|
| pandas (eager) | ~0,070 sn | ~14,2 MB |
| Polars (lazy) | ~0,0075 sn | ~7,4 MB |

Polars bu işte pandas'tan **~9× hızlı** ve **~yarı bellek** kullandı. (Tek-seferlik ölçüm
gürültülüdür; eğilim için ölçekleme testine bakın.)

## Ölçekleme Testi (10K / 50K / 100K satır)

| Satır | pandas (sn) | Polars (sn) | Hız farkı (pandas/Polars) | pandas bellek | Polars bellek |
|---|---|---|---|---|---|
| 10.000 | 0,0076 | 0,0033 | **2,3×** | 0,95 MB | 0,49 MB |
| 50.000 | 0,0251 | 0,0037 | **6,8×** | 4,75 MB | 2,46 MB |
| 100.000 | 0,0472 | 0,0048 | **9,8×** | 9,49 MB | 4,92 MB |

**Anahtar gözlem:** Polars'ın hız avantajı veri büyüdükçe **artıyor** (2,3× → 9,8×). pandas
süresi satır sayısıyla doğrusal büyürken Polars neredeyse sabit kalıyor — lazy motor +
paralel yürütme + sütun bazlı okuma sayesinde. Bellekte de Polars tutarlı biçimde ~yarı yer kaplıyor.

## Ne Zaman Polars Mantıklı?

Polars; **büyük veri** (yüz binlerce–milyonlarca satır), **lazy evaluation** (sorguyu
çalıştırmadan optimize etme) ve **çok çekirdekli paralellik** gerektiren işlerde pandas'a göre
belirgin biçimde hızlıdır — yukarıdaki ölçeklemede avantaj 100K'da ~10×'e çıkıyor. Örneğin
günlük milyonlarca uçuş/log kaydını filtreleyip gruplayan **ETL** işlerinde Polars'ın lazy
motoru gereksiz sütun ve satırları daha okumadan eler. Buna karşılık **küçük veri**, zengin
**ekosistem entegrasyonu** (scikit-learn, statsmodels, matplotlib ile doğrudan uyum) ve
**öğrenme kolaylığı** gereken durumlarda pandas hâlâ pratiktir; ekip pandas biliyorsa ve veri
belleğe rahat sığıyorsa pandas yeterlidir. **Özet:** büyük veri + tekrarlı/ETL → Polars;
küçük veri + hızlı keşif + geniş kütüphane ihtiyacı → pandas.

## Sonuç

Aynı kanonik sorgu iki motorda da aynı sonucu verir (doğrulandı). Performans/bellekte Polars
bu veri boyutunda ve üzerinde net üstün; pandas küçük veri ve ekosistem kolaylığında tercih
sebebidir.
