# Polars vs Pandas Pipeline

> YZTA Challenge — Büyükçe tablo üzerinde **filtre → group_by → aggregation** akışını
> Polars (lazy) ile yazıp aynı mantığı pandas ile kıyaslayan pratik proje.

~150.000 satırlık sentetik **uçuş verisi** üzerinde, tek bir kanonik sorgu hem Polars'ın
lazy motoruyla hem pandas ile uygulanır; sonuçların **birebir aynı** olduğu doğrulanır ve
süre/bellek karşılaştırılır.

## Amaç ve Kapsam

- **Veri:** En az 100.000 satır (bu projede 150.000) gerçekçi dağılımlı sentetik uçuş verisi
  — kategorik (havaalanı, havayolu, uçuş tipi), tarih (kalkış tarihi), sayısal (bilet fiyatı,
  gecikme dk).
- **Polars pipeline:** `scan_csv` ile **lazy** üç-adımlık zincir (filtre → group_by → agg) + `.collect()`.
- **Pandas kıyas:** Aynı sorgunun `read_csv` + `groupby().agg()` ile yazımı, süre/bellek karşılaştırması ve ölçekleme testi.
- **Doğrulama:** İki motorun aynı sonucu ürettiğinin testlerle kanıtlanması + edge-case'ler.

### Kanonik sorgu
2024 yılı **iç hat** uçuşları → `kalkis_havaalani` + `havayolu` bazında **toplam gelir**
(bilet fiyatı toplamı), **ortalama gecikme**, **uçuş adedi**; toplam gelire göre azalan
(50 satır sonuç).

## Kurulum

```bash
# 1) Depoyu klonla
git clone https://github.com/zuhrekorhn/polars-vs-pandas-pipeline.git
cd polars-vs-pandas-pipeline

# 2) Sanal ortam oluştur ve etkinleştir
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3) Bağımlılıkları kur
pip install -r requirements.txt
```

Sabitlenmiş sürümler (`requirements.txt`): `polars==1.41.2`, `pandas==3.0.3`,
`numpy==2.4.6`, `pyarrow==24.0.0`, `matplotlib==3.10.9` (+ `jupyter`, `ipykernel`).
Python 3.14 ile test edilmiştir.

## Çalıştırma Sırası

Veri dosyası (`data/ucus_verisi.csv`) depoya dahildir; doğrudan 2. adımdan başlayabilirsiniz.
Sıfırdan üretmek isterseniz 1. notebook'u önce çalıştırın (deterministik, `seed=42`).

| Sıra | Notebook | Ne yapar | Sahip |
|---|---|---|---|
| 1 | [`notebooks/polars_pipeline.ipynb`](notebooks/polars_pipeline.ipynb) | Sentetik veriyi üretir (`data/ucus_verisi.csv`) + Polars lazy pipeline | Zühre |
| 2 | [`notebooks/pandas_karsilastirma.ipynb`](notebooks/pandas_karsilastirma.ipynb) | Aynı sorguyu pandas ile yazar, süre/bellek + ölçekleme kıyası | Dilara |
| 3 | [`notebooks/test_dogrulama.ipynb`](notebooks/test_dogrulama.ipynb) | Eşdeğerlik + edge-case + zaman doğrulaması, görseller | Fatih |

Her notebook için **Kernel → Restart & Run All**. Çalışma dizini depo kökü olmalı
(göreli yol `data/ucus_verisi.csv` çözülsün).

Birim testler:
```bash
python -m pytest -q          # 9 test — kanonik sorgu eşdeğerlik + edge-case + zaman
```

## Sonuçlar (özet)

- **Eşdeğerlik:** Polars ve pandas sonuçları birebir eşdeğer (şekil/sütun/grup/int-tam/float-toleranslı) — **PASS ✅**
- **Performans:** 150K satırda Polars pandas'tan ~9× hızlı; ölçeklemede avantaj veri büyüdükçe artıyor (10K→2.3×, 100K→9.8×).
- Ayrıntı: [`test_raporu.md`](docs/test_raporu.md) ve [`karsilastirma_sonuclari.md`](docs/karsilastirma_sonuclari.md).

## Proje Yapısı

```
polars-vs-pandas-pipeline/
├── data/
│   └── ucus_verisi.csv              # 150.000 satırlık sentetik uçuş verisi (8 sütun)
├── notebooks/
│   ├── polars_pipeline.ipynb        # [1] Veri üretimi + Polars lazy pipeline
│   ├── pandas_karsilastirma.ipynb   # [2] Pandas kıyas + ölçekleme/benchmark
│   └── test_dogrulama.ipynb         # [3] Eşdeğerlik + edge-case + zaman doğrulaması
├── docs/
│   ├── karsilastirma_sonuclari.md   # Pandas vs Polars karşılaştırma yazısı
│   ├── test_raporu.md               # Test & doğrulama raporu
│   └── paylasim_metni.txt           # Challenge teslim notu
├── tests/
│   └── test_kanonik.py              # pytest birim testleri (9 test)
├── kanonik.py                       # Kanonik sorgu + eşdeğerlik/zaman yardımcıları (tek kaynak)
├── requirements.txt                 # Sabitlenmiş bağımlılıklar
├── LICENSE
└── README.md
```

> Not: Veri dosyası adı `ucus_verisi.csv`'dir (proje şablonundaki `sentetik_veri.csv` yerine);
> tüm notebook referansları bu adı kullanır.

## Ekip

| Kişi | Rol | Ana sorumluluk |
|---|---|---|
| Zühre | Polars Developer | Veri üretimi + Polars pipeline |
| Dilara | Pandas Analyst | Pandas kıyas + karşılaştırma yazısı |
| Fatih | Koordinatör | Dokümantasyon + test + sunum |
