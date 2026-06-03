import polars as pl
import pandas as pd
from kanonik import (
    polars_kanonik,
    pandas_kanonik,
    normalize,
    esdeger_mi,
    SONUC_SUTUNLAR,
    VERI_YOLU,
)


def test_polars_kanonik_sekil_ve_sutunlar():
    df = polars_kanonik(VERI_YOLU)
    assert df.shape == (50, 5)
    assert df.columns == SONUC_SUTUNLAR


def test_pandas_kanonik_sekil_ve_sutunlar():
    df = pandas_kanonik(VERI_YOLU)
    assert df.shape == (50, 5)
    assert list(df.columns) == SONUC_SUTUNLAR


def test_iki_motor_ayni_grup_kumesi():
    pl_df = polars_kanonik(VERI_YOLU).to_pandas()
    pd_df = pandas_kanonik(VERI_YOLU)
    pl_gruplar = set(zip(pl_df["kalkis_havaalani"], pl_df["havayolu"]))
    pd_gruplar = set(zip(pd_df["kalkis_havaalani"], pd_df["havayolu"]))
    assert pl_gruplar == pd_gruplar


def test_esdeger_mi_gercek_cift_gecer():
    pl_df = polars_kanonik(VERI_YOLU)
    pd_df = pandas_kanonik(VERI_YOLU)
    sonuc = esdeger_mi(pl_df, pd_df)
    assert sonuc["gecti"] is True, sonuc["detaylar"]


def test_esdeger_mi_bozuk_cift_kalir():
    pl_df = polars_kanonik(VERI_YOLU)
    pd_df = pandas_kanonik(VERI_YOLU).copy()
    pd_df.loc[0, "toplam_gelir"] = pd_df.loc[0, "toplam_gelir"] + 1000.0  # kasıtlı bozma
    sonuc = esdeger_mi(pl_df, pd_df)
    assert sonuc["gecti"] is False
