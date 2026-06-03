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
    """Kanonik sorgu — Polars LAZY: filter → group_by → agg → sort → collect."""
    return (
        pl.scan_csv(path)
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
