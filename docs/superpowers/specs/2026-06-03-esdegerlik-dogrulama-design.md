# Tasarım: Bağımsız Eşdeğerlik Doğrulama Notebook'u + Test Raporu

- **Tarih:** 2026-06-03
- **Sahip:** Fatih (3. Kişi — Dokümantasyon, Test & Sunum Koordinatörü)
- **Kapsam:** Challenge "Polars vs Pandas Pipeline" — 3. kişi görevi *Test & Doğrulama*
- **Durum:** Onaylandı (kullanıcı tasarımı onayladı), spec yazımı

## 1. Amaç ve Problem

Challenge'ın 4. kabul kriteri "pandas tarafı **aynı** mantığı göstersin" diyor ve 3. kişinin
görevi "Polars ve pandas pipeline'larının **aynı sonucu** ürettiğini doğrula" şeklinde.

Denetimde tespit edilen blokaj: iki notebook **farklı sorgular** çalıştırıyor.

| | Polars (`polars_pipeline.ipynb`, vitrin) | Pandas (`pandas_karsilastirma.ipynb`) |
|---|---|---|
| Filtre | `kalkis_tarihi~'2024' & ucus_tipi=='ic_hat'` | `gecikme_dk>30 & bilet_fiyati>2000` |
| Group by | `[kalkis_havaalani, havayolu]` (50 grup) | `[havayolu, ucus_tipi]` (10 grup) |
| Agg | fiyat.**SUM**, gecikme.**MEAN**, len | fiyat.**MEAN**, gecikme.**SUM**, count |
| Sıralama | toplam_gelir DESC | yok |

`sum`/`mean` rolleri ters çevrilmiş — bu haliyle eşdeğerlik testi anlamsız.

**Karar (kullanıcı onaylı):** Kanonik (tek) sorgu = **Zühre'nin vitrin sorgusu**. Her iki
motor da bu sorguyu uygulayacak ve eşdeğerliği kanıtlanacak.

## 2. Kanonik Sorgu (tek doğruluk kaynağı)

- **Filtre:** `kalkis_tarihi` "2024" ile başlar **VE** `ucus_tipi == "ic_hat"`
- **Group by:** `[kalkis_havaalani, havayolu]`
- **Agregasyon (sütun adları iki motorda birebir aynı):**
  - `toplam_gelir`   = `bilet_fiyati`.sum()
  - `ort_gecikme_dk` = `gecikme_dk`.mean()
  - `ucus_adedi`     = satır sayısı (Polars `pl.len()`, pandas `count`)
- **Sıralama:** `toplam_gelir` azalan
- **Beklenen sonuç:** 50 satır (10 havaalanı × 5 havayolu), 5 sütun

Tarih filtresi **iki tarafta da** `str.startswith("2024")` ile yapılır. Gerekçe: Polars
`scan_csv` tarihi varsayılan `Utf8` okur; pandas tarafını da string-prefix tutmak eşitliği
kod seviyesinde şeffaf kılar (datetime'a çevirip `dt.year==2024` aynı satırları seçer ama
farklı kod yolundan, "neden farklı?" şüphesi doğurur).

## 3. Mimari ve Veri Akışı

```
data/ucus_verisi.csv (commit'li, MD5 = a7a4ca24173b4f4b101c0ca70bf7a9d7)
        │  (aynı baytlar, iki motora)
        ├──────────► polars_kanonik(path)  [lazy: scan_csv→filter→group_by→agg→sort→collect]
        └──────────► pandas_kanonik(path)   [read_csv→filter→groupby→agg→sort→reset_index]
                              │
            normalize: to_pandas, sort [kalkis_havaalani,havayolu], reset_index, ucus_adedi→int64
                              │
              ┌───────────────┴───────────────┐
        eşdeğerlik assert'leri          edge-case'ler (boş / null / tek satır)
                              │
                  zaman ölçümü (N=5 tekrar ort.) + grafik
                              │
                    test_raporu.md  ◄── gerçek çıktıları alıntılar
```

## 4. Bileşenler

### 4.1 `test_dogrulama.ipynb` (yeni — takım notebook'larına dokunmaz)

- **Hücre A — Girdi sabitleme:** `data/ucus_verisi.csv` yüklenir; MD5 ==
  `a7a4ca24173b4f4b101c0ca70bf7a9d7` ve şekil `(150000, 8)` assert edilir. Uyuşmazlıkta
  net mesajla sert hata (yanlış baytlarla test edilmesin).
- **Hücre B — Kanonik sorgu, iki motor:** `polars_kanonik(path) -> pl.DataFrame` (lazy
  zincir, `.collect()`), `pandas_kanonik(path) -> pd.DataFrame`. İkisi de Bölüm 2'deki
  tanımı ve aynı sütun adlarını üretir.
- **Hücre C — Eşdeğerlik kanıtı:** `pl_sonuc.to_pandas()` → her ikisini `[kalkis_havaalani,
  havayolu]`'na göre `sort_values` + `reset_index(drop=True)` → `ucus_adedi`'yi `int64`'e
  cast → assert: aynı şekil, aynı sütun adları, aynı grup kümesi, `ucus_adedi` tam eşit,
  `toplam_gelir` & `ort_gecikme_dk` için `np.testing.assert_allclose(rtol=1e-9, atol=1e-6)`.
  PASS/FAIL + fark özeti yazdırılır.
- **Hücre D — Edge case'ler:** boş DataFrame (0 satır, aynı şema), filtre sütununda tüm-null,
  tek satır. Üçü de iki motordan geçirilir, **aynı davrandıkları** doğrulanır ve davranış
  belgelenir. Motorlar farklı davranırsa gizlenmez, bulgu olarak raporlanır.
- **Hücre E — Zaman ölçümü:** `time.perf_counter`, **N=5 tekrar ortalaması** (tek-seferlik
  gürültülü ölçüm açığını kapatır), aynı kanonik sorgu + aynı tam girdi üzerinde Polars vs
  pandas.
- **Hücre F — Görseller:** matplotlib bar grafik (Polars vs pandas süre) + sonuç tablosu
  (head). Bu hücre 3. kişinin "görseller" teslimatını da karşılar.

### 4.2 `test_raporu.md`

İçerik: yöntem, girdi sabitleme (MD5), kanonik sorgu tanımı, eşdeğerlik sonucu (PASS +
gerçek sayılar), edge-case sonuç tablosu, süre tablosu/grafik referansı, dtype-cast notu,
neyin uzlaştırıldığının açık beyanı (iki farklı sorgunun tek kanonik sorguya indirgenmesi)
ve kalan takım-sync maddeleri. Her iddia gerçek bir koşumla desteklenir.

### 4.3 `requirements.txt`

`matplotlib` (pinli) eklenir. Pinli yığının temiz venv'de kurulduğu doğrulanır.

## 5. Hata Yönetimi

- **MD5 uyuşmazlığı:** sert hata, net mesaj.
- **Pinli yığın kurulmazsa** (pandas 3.0.3 / numpy 2.4.6 yeni major riski): bilinen-iyi
  sürümlere düşülür ve raporda belgelenir.
- **Edge-case'te motor farkı:** gizlenmez, bulgu olarak belgelenir.

## 6. Kapsam Sınırları (YAGNI / Non-Goals)

- `polars_pipeline.ipynb` ve `pandas_karsilastirma.ipynb` **değiştirilmez** (takım sahipliği).
- Dilara'nın cell-10 benchmark hatası burada düzeltilmez — ona flag'lenir (sync maddesi).
- `README.md` ve `paylasim_metni.txt` bu işin parçası değil (sonraki görevler).
- Veri kalitesi anomalisi (%10 aynı-havaalanı uçuş) burada düzeltilmez; raporda not edilir.

## 7. Learning-Mode Katkı Noktaları (kullanıcı yazacak)

- **Eşdeğerlik kriteri (Hücre C):** float toleransı ve "eşit" sayılma kuralı.
- **Edge-case beklenen davranış (Hücre D):** boş/null/tek-satırda "doğru" sonucun ne olduğu.

## 8. Kabul Kriterleri (bu iş için)

- [ ] `test_dogrulama.ipynb` Restart & Run All ile hatasız koşar.
- [ ] Eşdeğerlik testi kanonik sorgu için PASS verir (int tam, float toleranslı).
- [ ] 3 edge-case (boş/null/tek satır) iki motorda da koşar ve sonucu belgelenir.
- [ ] Süre ölçümü N=5 tekrar ortalamasıyla raporlanır; en az 1 grafik + 1 tablo.
- [ ] `test_raporu.md` tüm sonuçları gerçek koşum çıktısıyla belgeler.
- [ ] `requirements.txt` matplotlib dahil güncel ve temiz venv'de kurulur.

## 9. Bağımlılıklar / Açık Takım Maddeleri

- Dilara: `pandas_karsilastirma.ipynb`'i kanonik sorguya hizalamalı; cell-10 ve bellek
  metriğini düzeltmeli; `karsilastirma_sonuclari.md` + "Ne zaman Polars" paragrafını yazmalı.
- Takım: %10 aynı-havaalanı veri anomalisi için filtrele-mi-belgele kararı; `ucus_verisi.csv`
  isim sapması kararı.
