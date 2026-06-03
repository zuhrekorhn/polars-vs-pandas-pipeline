import polars as pl
import pandas as pd
from kanonik import polars_kanonik, pandas_kanonik, SONUC_SUTUNLAR, VERI_YOLU


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
