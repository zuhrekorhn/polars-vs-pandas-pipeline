import polars as pl
import pandas as pd
from kanonik import (
    polars_kanonik,
    pandas_kanonik,
    normalize,
    esdeger_mi,
    sure_olc,
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


def _gecici_csv(tmp_path, satirlar):
    p = tmp_path / "mini.csv"
    baslik = "ucus_no,kalkis_havaalani,varis_havaalani,havayolu,ucus_tipi,kalkis_tarihi,bilet_fiyati,gecikme_dk"
    p.write_text("\n".join([baslik] + satirlar) + "\n")
    return str(p)


def test_edge_bos_dataframe(tmp_path):
    path = _gecici_csv(tmp_path, [])  # yalnız başlık
    pl_df = polars_kanonik(path)
    pd_df = pandas_kanonik(path)
    assert pl_df.shape[0] == 0 and pd_df.shape[0] == 0
    assert esdeger_mi(pl_df, pd_df)["gecti"] is True


def test_edge_null_filtre_disi(tmp_path):
    # ucus_tipi boş (null) tek satır → filtre eler → boş sonuç, iki motor da aynı
    path = _gecici_csv(tmp_path, ["F1,IST,ESB,THY,,2024-05-01,1000.0,10"])
    pl_df = polars_kanonik(path)
    pd_df = pandas_kanonik(path)
    assert pl_df.shape[0] == 0 and pd_df.shape[0] == 0


def test_edge_tek_satir(tmp_path):
    path = _gecici_csv(tmp_path, ["F1,IST,ESB,THY,ic_hat,2024-05-01,1000.0,10"])
    pl_df = polars_kanonik(path)
    pd_df = pandas_kanonik(path)
    assert pl_df.shape == (1, 5) and pd_df.shape == (1, 5)
    assert esdeger_mi(pl_df, pd_df)["gecti"] is True
    assert pd_df.loc[0, "ucus_adedi"] == 1
    assert pd_df.loc[0, "toplam_gelir"] == 1000.0


def test_sure_olc_pozitif_ortalama():
    ort = sure_olc(pandas_kanonik, VERI_YOLU, tekrar=2)
    assert isinstance(ort, float) and ort > 0
