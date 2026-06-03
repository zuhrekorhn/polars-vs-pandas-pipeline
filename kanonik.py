"""Kanonik sorgu ve doğrulama yardımcıları (Polars lazy vs pandas eşdeğerliği)."""
import time
import polars as pl
import pandas as pd
import numpy as np

GROUP_KEYS = ["kalkis_havaalani", "havayolu"]
SONUC_SUTUNLAR = ["kalkis_havaalani", "havayolu", "toplam_gelir", "ort_gecikme_dk", "ucus_adedi"]
VERI_YOLU = "data/ucus_verisi.csv"
BEKLENEN_MD5 = "a7a4ca24173b4f4b101c0ca70bf7a9d7"


def polars_kanonik(path: str = VERI_YOLU) -> pl.DataFrame:
    """Kanonik sorgu — Polars LAZY: filter → group_by → agg → sort → collect.

    schema_overrides: boş (yalnız başlık) CSV'de Polars sayısal sütunları str tahmin eder
    ve .sum() patlar. Tipleri açıkça sabitlemek hem bu edge-case'i düzeltir hem de gerçek
    veride aynı tipler olduğu için davranışı değiştirmez (şema çıkarımına güvenmemek iyi pratik).
    """
    return (
        pl.scan_csv(path, schema_overrides={"bilet_fiyati": pl.Float64, "gecikme_dk": pl.Int64})
        .filter(
            pl.col("kalkis_tarihi").str.starts_with("2024")
            & (pl.col("ucus_tipi") == "ic_hat")
        )
        .group_by(GROUP_KEYS)
        .agg(
            pl.col("bilet_fiyati").sum().alias("toplam_gelir"),
            pl.col("gecikme_dk").mean().alias("ort_gecikme_dk"),
            pl.len().alias("ucus_adedi"),
        )
        .sort("toplam_gelir", descending=True)
        .collect()
        .select(SONUC_SUTUNLAR)
    )


def pandas_kanonik(path: str = VERI_YOLU) -> pd.DataFrame:
    """Kanonik sorgu — pandas eager: read_csv → filter → groupby → agg → sort."""
    df = pd.read_csv(path)
    mask = df["kalkis_tarihi"].str.startswith("2024", na=False) & (df["ucus_tipi"] == "ic_hat")
    g = (
        df[mask]
        .groupby(GROUP_KEYS)
        .agg(
            toplam_gelir=("bilet_fiyati", "sum"),
            ort_gecikme_dk=("gecikme_dk", "mean"),
            ucus_adedi=("ucus_no", "count"),
        )
        .reset_index()
        .sort_values("toplam_gelir", ascending=False)
        .reset_index(drop=True)
    )
    return g[SONUC_SUTUNLAR]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Karşılaştırma için kanonik forma getir: sırala, indeks sıfırla, sayaç int64.

    Polars `to_pandas()` çıktısı ile pandas çıktısını aynı satır sırasına ve aynı
    sayaç dtype'ına (Polars u32 vs pandas int64) getirir; aksi halde naif karşılaştırma
    kozmetik nedenlerle başarısız olur.
    """
    out = df[SONUC_SUTUNLAR].sort_values(GROUP_KEYS).reset_index(drop=True).copy()
    # dtype'ları kanonik forma getir: Polars u32 vs pandas int64, ve boş groupby-agg'de
    # pandas float sütunu object üretebilir → assert_allclose patlar. float64'e sabitle.
    out["ucus_adedi"] = out["ucus_adedi"].astype("int64")
    out["toplam_gelir"] = out["toplam_gelir"].astype("float64")
    out["ort_gecikme_dk"] = out["ort_gecikme_dk"].astype("float64")
    return out


def esdeger_mi(pl_df, pd_df, rtol: float = 1e-9, atol: float = 1e-6) -> dict:
    """Polars ve pandas sonuçlarının EŞDEĞER olup olmadığını kanıtla.

    Dönüş: {"gecti": bool, "detaylar": {...bool/again...}}

    KURALLAR (öğrenme noktası — bu gövdeyi SEN yazacaksın):
      - Şekil eşit mi?  -> detaylar["sekil_esit"]
      - Sütun adları eşit mi?  -> detaylar["sutunlar_esit"]
      - Grup kümesi (kalkis_havaalani, havayolu) eşit mi?  -> detaylar["grup_kumesi_esit"]
      - ucus_adedi TAM eşit mi (int)?  -> detaylar["ucus_adedi_tam_esit"]
      - toplam_gelir & ort_gecikme_dk TOLERANSLI eşit mi (float)?
            np.testing.assert_allclose(..., rtol=rtol, atol=atol)  -> detaylar["float_toleransli_esit"]
      - "gecti" = tüm bool kontrollerin AND'i
    """
    a = normalize(pl_df.to_pandas())
    b = normalize(pd_df)
    detaylar = {}

    # 1) Şekil: satır × sütun sayısı birebir aynı mı?
    detaylar["sekil_esit"] = a.shape == b.shape
    # 2) Sütun adları aynı sırada aynı mı?
    detaylar["sutunlar_esit"] = list(a.columns) == list(b.columns)
    # 3) Grup kümesi: (kalkis_havaalani, havayolu) ikilileri küme olarak eşit mi?
    #    Küme kullanıyoruz çünkü sıra değil, "aynı gruplar var mı" önemli.
    detaylar["grup_kumesi_esit"] = (
        set(zip(a["kalkis_havaalani"], a["havayolu"]))
        == set(zip(b["kalkis_havaalani"], b["havayolu"]))
    )
    # 4) Tamsayı sayacı TAM eşit (tolerans yok — sayım birebir tutmalı).
    detaylar["ucus_adedi_tam_esit"] = bool((a["ucus_adedi"] == b["ucus_adedi"]).all())
    # 5) Float sütunlar toleranslı eşit: toplama sırası farkı son bitlerde sapma yaratır,
    #    assert_allclose bunu emer. Hata fırlatırsa False + hata metnini sakla.
    try:
        np.testing.assert_allclose(a["toplam_gelir"], b["toplam_gelir"], rtol=rtol, atol=atol)
        np.testing.assert_allclose(a["ort_gecikme_dk"], b["ort_gecikme_dk"], rtol=rtol, atol=atol)
        detaylar["float_toleransli_esit"] = True
    except AssertionError as e:
        detaylar["float_toleransli_esit"] = False
        detaylar["float_hata"] = str(e)

    # "gecti" = tüm bool kontrollerin AND'i (float_hata str olduğundan bool filtreleniyor).
    detaylar["gecti"] = all(v for v in detaylar.values() if isinstance(v, bool))
    return {"gecti": detaylar["gecti"], "detaylar": detaylar}
