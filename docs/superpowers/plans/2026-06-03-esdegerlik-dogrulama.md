# Eşdeğerlik Doğrulama Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polars (lazy) ve pandas pipeline'larının tek kanonik sorgu üzerinde aynı sonucu ürettiğini kanıtlayan, edge-case'leri test eden ve süre ölçen bağımsız bir doğrulama artefaktı (`test_dogrulama.ipynb`) + rapor (`test_raporu.md`) üretmek.

**Architecture:** Sorgu/eşdeğerlik/edge/zaman mantığı test edilebilir tek bir modülde (`kanonik.py`) yaşar; `tests/test_kanonik.py` pytest ile TDD doğrular; `test_dogrulama.ipynb` bu modülü import edip sunum + görsel üretir; `test_raporu.md` gerçek koşum çıktılarını belgeler. Takımın `polars_pipeline.ipynb` / `pandas_karsilastirma.ipynb` notebook'larına dokunulmaz.

**Tech Stack:** Python 3.14, polars==1.41.2, pandas==3.0.3, numpy==2.4.6, matplotlib (pinli), pytest (dev), jupyter/nbformat/nbconvert.

---

## Dosya Yapısı

| Dosya | Sorumluluk | Create/Modify |
|---|---|---|
| `kanonik.py` | Kanonik sorgu (polars+pandas), normalize, eşdeğerlik, edge-case, zaman yardımcıları | Create |
| `tests/test_kanonik.py` | `kanonik.py` için pytest birim testleri | Create |
| `test_dogrulama.ipynb` | Sunum: import kanonik → eşdeğerlik gösterimi, edge-case, zaman, grafik | Create |
| `test_raporu.md` | Gerçek koşum çıktılarıyla test raporu | Create |
| `requirements.txt` | matplotlib eklenir | Modify |

**Sabitler (`kanonik.py` içinde, tek tanım):**
```python
GROUP_KEYS = ["kalkis_havaalani", "havayolu"]
SONUC_SUTUNLAR = ["kalkis_havaalani", "havayolu", "toplam_gelir", "ort_gecikme_dk", "ucus_adedi"]
VERI_YOLU = "data/ucus_verisi.csv"
BEKLENEN_MD5 = "a7a4ca24173b4f4b101c0ca70bf7a9d7"
```

> **Öğrenme noktaları (learning-mode):** Task 2 Step 3 (eşdeğerlik toleransı/kriteri) ve Task 3 Step 3 (edge-case beklenen davranışı) senin yazman için işaretli. Plan referans implementasyonu içeriyor; istersen kendi mantığınla değiştir.

---

### Task 0: Ortam kurulumu ve sürüm doğrulama

**Files:**
- Modify: (yok — venv ve kanıt)

- [ ] **Step 1: Temiz venv oluştur**

Run:
```bash
cd /Users/fatiherencetin/Developer/polars-challenge
python3 -m venv .venv
source .venv/bin/activate
python -V
```
Expected: `Python 3.14.x` yazdırır.

- [ ] **Step 2: Pinli yığını + dev araçlarını kur**

Run:
```bash
pip install -r requirements.txt
pip install pytest nbformat nbconvert
```
Expected: Hatasız tamamlanır. Eğer `pandas==3.0.3` veya `numpy==2.4.6` çözülemezse → DUR, kullanıcıya bildir; bilinen-iyi sürüme düşülecek (raporda belgelenecek).

- [ ] **Step 3: Sürümleri ve veriyi doğrula**

Run:
```bash
python -c "import polars, pandas, numpy, matplotlib; print('polars', polars.__version__); print('pandas', pandas.__version__); print('numpy', numpy.__version__)"
md5 -q data/ucus_verisi.csv
```
Expected: polars 1.41.2 / pandas 3.0.3 / numpy 2.4.6; MD5 `a7a4ca24173b4f4b101c0ca70bf7a9d7`. Çıktıyı `test_raporu.md` için sakla.

---

### Task 1: `kanonik.py` — kanonik sorgu fonksiyonları (TDD)

**Files:**
- Create: `kanonik.py`
- Test: `tests/test_kanonik.py`

- [ ] **Step 1: Başarısız testi yaz**

`tests/test_kanonik.py`:
```python
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
```

- [ ] **Step 2: Testi çalıştır, başarısız olduğunu gör**

Run: `python -m pytest tests/test_kanonik.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'kanonik'`.

- [ ] **Step 3: Minimal implementasyonu yaz**

`kanonik.py`:
```python
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
```

Not: Pandas tarafında `str.startswith("2024", na=False)` — Polars `filter` null'ları eler; `na=False` pandas'ı aynı semantiğe hizalar (Task 3'te kanıtlanacak).

- [ ] **Step 4: Testi çalıştır, geçtiğini gör**

Run: `python -m pytest tests/test_kanonik.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add kanonik.py tests/test_kanonik.py
git commit -m "feat: kanonik sorgu (polars+pandas) + birim testleri"
```

---

### Task 2: Eşdeğerlik yardımcısı (TDD, negatif test dahil)

**Files:**
- Modify: `kanonik.py`
- Test: `tests/test_kanonik.py`

- [ ] **Step 1: Başarısız testi yaz** (`tests/test_kanonik.py` sonuna ekle)

```python
from kanonik import normalize, esdeger_mi


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
```

- [ ] **Step 2: Testi çalıştır, başarısız olduğunu gör**

Run: `python -m pytest tests/test_kanonik.py::test_esdeger_mi_gercek_cift_gecer -q`
Expected: FAIL — `ImportError: cannot import name 'normalize'`.

- [ ] **Step 3: Minimal implementasyonu yaz** *(ÖĞRENME NOKTASI — toleransı/kriteri sen belirleyebilirsin; referans aşağıda)*

`kanonik.py` sonuna ekle:
```python
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Karşılaştırma için kanonik forma getir: sırala, indeks sıfırla, sayaç int64."""
    out = df[SONUC_SUTUNLAR].sort_values(GROUP_KEYS).reset_index(drop=True).copy()
    out["ucus_adedi"] = out["ucus_adedi"].astype("int64")
    return out


def esdeger_mi(pl_df, pd_df, rtol: float = 1e-9, atol: float = 1e-6) -> dict:
    """Polars ve pandas sonuçlarının eşdeğerliğini kanıtla.
    int sütun (ucus_adedi) tam eşit; float sütunlar toleranslı (toplama sırası farkı için)."""
    a = normalize(pl_df.to_pandas())
    b = normalize(pd_df)
    detaylar = {}
    detaylar["sekil_esit"] = a.shape == b.shape
    detaylar["sutunlar_esit"] = list(a.columns) == list(b.columns)
    detaylar["grup_kumesi_esit"] = (
        set(zip(a["kalkis_havaalani"], a["havayolu"]))
        == set(zip(b["kalkis_havaalani"], b["havayolu"]))
    )
    detaylar["ucus_adedi_tam_esit"] = bool((a["ucus_adedi"] == b["ucus_adedi"]).all())
    try:
        np.testing.assert_allclose(a["toplam_gelir"], b["toplam_gelir"], rtol=rtol, atol=atol)
        np.testing.assert_allclose(a["ort_gecikme_dk"], b["ort_gecikme_dk"], rtol=rtol, atol=atol)
        detaylar["float_toleransli_esit"] = True
    except AssertionError as e:
        detaylar["float_toleransli_esit"] = False
        detaylar["float_hata"] = str(e)
    detaylar["gecti"] = all(
        v for k, v in detaylar.items() if isinstance(v, bool)
    )
    return {"gecti": detaylar["gecti"], "detaylar": detaylar}
```

- [ ] **Step 4: Testleri çalıştır, geçtiğini gör**

Run: `python -m pytest tests/test_kanonik.py -q`
Expected: 5 passed (pozitif eşdeğerlik geçer, negatif bozuk çift kalır).

- [ ] **Step 5: Commit**

```bash
git add kanonik.py tests/test_kanonik.py
git commit -m "feat: normalize + esdeger_mi eşdeğerlik yardımcısı (pozitif/negatif test)"
```

---

### Task 3: Edge-case yardımcıları (TDD: boş / null / tek satır)

**Files:**
- Modify: `kanonik.py` (gerekirse — fonksiyonlar zaten path tabanlı, ek koda gerek yok)
- Test: `tests/test_kanonik.py`

- [ ] **Step 1: Başarısız testi yaz** (`tests/test_kanonik.py` sonuna ekle)

```python
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
```

- [ ] **Step 2: Testleri çalıştır**

Run: `python -m pytest tests/test_kanonik.py -k edge -q`
Expected: Çoğu geçer. Eğer boş-DataFrame'de Polars/pandas şema farkı çıkarsa (örn. boş agg sütun tipi) → bu bir **bulgu**; `test_raporu.md`'ye yaz, gizleme. Gerekirse `pandas_kanonik`/`polars_kanonik`'e boş-girdi guard'ı ekle ve testi tekrar çalıştır.

- [ ] **Step 3: (gerekiyorsa) boş-girdi davranışını netleştir** *(ÖĞRENME NOKTASI — beklenen davranışı sen belirle)*

Eğer boş girdide iki motor farklı şema üretiyorsa, `normalize` zaten `SONUC_SUTUNLAR`'a indirger; çoğu durumda ek koda gerek yoktur. Fark devam ederse referans guard:
```python
# polars_kanonik / pandas_kanonik dönüşünden önce gerekiyorsa şema sabitle (örnek):
# pandas: g = g.astype({"toplam_gelir": "float64", "ort_gecikme_dk": "float64", "ucus_adedi": "int64"})
```

- [ ] **Step 4: Testler yeşil**

Run: `python -m pytest tests/test_kanonik.py -q`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add kanonik.py tests/test_kanonik.py
git commit -m "test: edge-case (boş/null/tek satır) eşdeğerlik testleri"
```

---

### Task 4: Zaman ölçüm yardımcısı (TDD)

**Files:**
- Modify: `kanonik.py`
- Test: `tests/test_kanonik.py`

- [ ] **Step 1: Başarısız testi yaz**

```python
from kanonik import sure_olc


def test_sure_olc_pozitif_ortalama():
    ort = sure_olc(pandas_kanonik, VERI_YOLU, tekrar=2)
    assert isinstance(ort, float) and ort > 0
```

- [ ] **Step 2: Testi çalıştır, başarısız gör**

Run: `python -m pytest tests/test_kanonik.py::test_sure_olc_pozitif_ortalama -q`
Expected: FAIL — `ImportError: cannot import name 'sure_olc'`.

- [ ] **Step 3: Implementasyonu yaz**

`kanonik.py` sonuna ekle:
```python
def sure_olc(fn, path: str = VERI_YOLU, tekrar: int = 5) -> float:
    """fn(path)'i `tekrar` kez koşup ortalama saniyeyi döndür (gürültü için ortalama)."""
    sureler = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fn(path)
        sureler.append(time.perf_counter() - t0)
    return sum(sureler) / len(sureler)
```

- [ ] **Step 4: Testi çalıştır, geçtiğini gör**

Run: `python -m pytest tests/test_kanonik.py -q`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add kanonik.py tests/test_kanonik.py
git commit -m "feat: sure_olc N-tekrar ortalama zaman ölçümü"
```

---

### Task 5: `test_dogrulama.ipynb` oluştur ve hatasız çalıştır

**Files:**
- Create: `test_dogrulama.ipynb`

- [ ] **Step 1: Notebook'u nbformat ile üreten geçici betiği yaz**

`_build_nb.py` (geçici, sonra silinecek):
```python
import nbformat as nbf

nb = nbf.v4.new_notebook()
hucreler = []
md = lambda s: hucreler.append(nbf.v4.new_markdown_cell(s))
code = lambda s: hucreler.append(nbf.v4.new_code_cell(s))

md("# Eşdeğerlik Doğrulama — Polars (lazy) vs pandas\n"
   "Kanonik sorgu: 2024 iç hat uçuşları, havaalanı+havayolu bazında gelir/gecikme/adet.")

code("import hashlib\n"
     "from kanonik import (polars_kanonik, pandas_kanonik, esdeger_mi,\n"
     "                     sure_olc, VERI_YOLU, BEKLENEN_MD5)\n"
     "import pandas as pd, matplotlib.pyplot as plt\n"
     "# Hücre A — girdi sabitleme\n"
     "md5 = hashlib.md5(open(VERI_YOLU,'rb').read()).hexdigest()\n"
     "assert md5 == BEKLENEN_MD5, f'MD5 uyuşmazlığı: {md5}'\n"
     "print('Girdi MD5 doğrulandı:', md5)")

md("## Hücre B — Kanonik sorgu iki motorda")
code("pl_sonuc = polars_kanonik(VERI_YOLU)\n"
     "pd_sonuc = pandas_kanonik(VERI_YOLU)\n"
     "print('Polars:', pl_sonuc.shape, '| pandas:', pd_sonuc.shape)\n"
     "pd_sonuc.head()")

md("## Hücre C — Eşdeğerlik kanıtı")
code("rapor = esdeger_mi(pl_sonuc, pd_sonuc)\n"
     "print('EŞDEĞERLİK:', 'PASS' if rapor['gecti'] else 'FAIL')\n"
     "for k, v in rapor['detaylar'].items():\n"
     "    print(f'  {k}: {v}')")

md("## Hücre D — Edge case'ler (boş / null / tek satır)")
code("import tempfile, os\n"
     "BASLIK='ucus_no,kalkis_havaalani,varis_havaalani,havayolu,ucus_tipi,kalkis_tarihi,bilet_fiyati,gecikme_dk'\n"
     "def mini(satirlar):\n"
     "    f=tempfile.NamedTemporaryFile('w',suffix='.csv',delete=False)\n"
     "    f.write('\\n'.join([BASLIK]+satirlar)+'\\n'); f.close(); return f.name\n"
     "senaryolar={'bos':[], 'null_filtre_disi':['F1,IST,ESB,THY,,2024-05-01,1000.0,10'],\n"
     "            'tek_satir':['F1,IST,ESB,THY,ic_hat,2024-05-01,1000.0,10']}\n"
     "for ad,satir in senaryolar.items():\n"
     "    p=mini(satir); a=polars_kanonik(p); b=pandas_kanonik(p)\n"
     "    print(f'{ad}: polars={a.shape} pandas={b.shape} esit={esdeger_mi(a,b)[\"gecti\"]}')\n"
     "    os.unlink(p)")

md("## Hücre E — Zaman ölçümü (N=5 tekrar ortalaması)")
code("pl_sure = sure_olc(polars_kanonik, VERI_YOLU, tekrar=5)\n"
     "pd_sure = sure_olc(pandas_kanonik, VERI_YOLU, tekrar=5)\n"
     "print(f'Polars ort: {pl_sure*1000:.1f} ms | pandas ort: {pd_sure*1000:.1f} ms')")

md("## Hücre F — Görseller")
code("fig, ax = plt.subplots(figsize=(5,3))\n"
     "ax.bar(['Polars (lazy)','pandas'], [pl_sure*1000, pd_sure*1000], color=['#2b8a3e','#1971c2'])\n"
     "ax.set_ylabel('Süre (ms, 5 tekrar ort.)'); ax.set_title('Kanonik sorgu süresi')\n"
     "plt.tight_layout(); plt.show()\n"
     "pd_sonuc.head(10)")

nb.cells = hucreler
nbf.write(nb, "test_dogrulama.ipynb")
print("yazıldı: test_dogrulama.ipynb")
```

- [ ] **Step 2: Betiği çalıştır, notebook'u üret**

Run: `python _build_nb.py`
Expected: `yazıldı: test_dogrulama.ipynb`.

- [ ] **Step 3: Notebook'u baştan sona çalıştır (Restart & Run All eşdeğeri)**

Run: `jupyter nbconvert --to notebook --execute --inplace test_dogrulama.ipynb`
Expected: Hatasız tamamlanır (exit 0); hiçbir hücre traceback üretmez.

- [ ] **Step 4: Çıktıların varlığını doğrula**

Run: `python -c "import nbformat; nb=nbformat.read('test_dogrulama.ipynb',4); errs=[o for c in nb.cells if c.cell_type=='code' for o in c.get('outputs',[]) if o.get('output_type')=='error']; print('hata sayısı:', len(errs)); print('EŞDEĞERLİK satırı var:', any('PASS' in ''.join(o.get('text','') for o in c.get('outputs',[]) if o.output_type=='stream') for c in nb.cells if c.cell_type=='code'))"`
Expected: `hata sayısı: 0`, `EŞDEĞERLİK satırı var: True`.

- [ ] **Step 5: Geçici betiği sil ve commit**

```bash
rm _build_nb.py
git add test_dogrulama.ipynb
git commit -m "feat: test_dogrulama.ipynb — eşdeğerlik + edge + zaman + görsel"
```

---

### Task 6: `test_raporu.md` — gerçek koşum çıktılarıyla

**Files:**
- Create: `test_raporu.md`

- [ ] **Step 1: Koşum sayılarını topla**

Run:
```bash
python -m pytest tests/test_kanonik.py -q
python -c "from kanonik import *; r=esdeger_mi(polars_kanonik(), pandas_kanonik()); import json; print(json.dumps(r['detaylar'], default=str, ensure_ascii=False, indent=2))"
python -c "from kanonik import *; print('polars ms', round(sure_olc(polars_kanonik)*1000,1)); print('pandas ms', round(sure_olc(pandas_kanonik)*1000,1))"
```
Expected: pytest "9 passed"; eşdeğerlik detayları; iki süre. Bu çıktıları rapora gerçek değerlerle gir.

- [ ] **Step 2: Raporu yaz**

`test_raporu.md` — şu bölümler, Step 1'deki **gerçek** değerlerle doldurulur (placeholder bırakma):
```markdown
# Test & Doğrulama Raporu

## 1. Yöntem
Kanonik sorgu (2024 iç hat; [kalkis_havaalani, havayolu]; toplam_gelir=sum, ort_gecikme_dk=mean,
ucus_adedi=adet; toplam_gelir azalan) hem Polars (lazy) hem pandas ile uygulandı ve eşdeğerliği
test edildi. Mantık `kanonik.py`'de, testler `tests/test_kanonik.py`'de.

## 2. Girdi Sabitleme
- Dosya: data/ucus_verisi.csv — MD5 a7a4ca24173b4f4b101c0ca70bf7a9d7, şekil (150000, 8)
- Ortam: polars 1.41.2 / pandas 3.0.3 / numpy 2.4.6 / Python 3.14.x

## 3. Eşdeğerlik Sonucu: PASS
- Şekil: (50, 5) iki motorda da
- ucus_adedi: tam eşit (int64'e cast sonrası; Polars u32 vs pandas int64 notu)
- toplam_gelir, ort_gecikme_dk: assert_allclose(rtol=1e-9, atol=1e-6) geçti
- (Step 1 detay çıktısını buraya yapıştır)

## 4. Edge-Case Sonuçları
| Senaryo | Polars | pandas | Eşit? | Not |
|---|---|---|---|---|
| Boş DataFrame | (0,5) | (0,5) | ✔ | filtre sonrası boş |
| Null (ucus_tipi) filtre dışı | (0,5) | (0,5) | ✔ | pandas `na=False` ile Polars'a hizalandı |
| Tek satır | (1,5) | (1,5) | ✔ | ucus_adedi=1, toplam_gelir=1000.0 |

## 5. Zaman Ölçümü (N=5 tekrar ortalaması)
- Polars (lazy): <X> ms | pandas: <Y> ms  (gerçek değerlerle)

## 6. Uzlaştırma Notu
Başlangıçta iki notebook farklı sorgular çalıştırıyordu (Polars: 2024/ic_hat gelir;
pandas: gecikme>30 & fiyat>2000). Kanonik sorgu olarak Polars vitrin sorgusu seçildi;
eşdeğerlik bu sorgu üzerinde kanıtlandı.

## 7. Açık Takım Maddeleri
- Dilara: pandas_karsilastirma.ipynb'i kanonik sorguya hizalama; cell-10 benchmark + bellek düzeltme.
- Takım: %10 aynı-havaalanı (kalkis==varis) veri anomalisi kararı.
```

- [ ] **Step 3: Placeholder kalmadığını doğrula**

Run: `grep -nE "<X>|<Y>|TODO|TBD|buraya yapıştır" test_raporu.md || echo "temiz"`
Expected: `temiz` (tüm gerçek değerler dolduruldu).

- [ ] **Step 4: Commit**

```bash
git add test_raporu.md
git commit -m "docs: test_raporu.md — eşdeğerlik + edge + zaman sonuçları"
```

---

### Task 7: `requirements.txt` güncelle + temiz kurulum doğrula

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: matplotlib ekle**

`requirements.txt` (matplotlib satırı eklenir; sürümü Task 0'da kurulan ile sabitle):
```bash
python -c "import matplotlib; print('matplotlib=='+matplotlib.__version__)" >> requirements.txt
```
Sonra dosyayı aç ve satırı doğru yere taşı (numpy'den sonra), tekrarı temizle.

- [ ] **Step 2: Temiz venv'de kurulumu tekrar doğrula**

Run:
```bash
deactivate 2>/dev/null; rm -rf .venv_test; python3 -m venv .venv_test
.venv_test/bin/pip install -r requirements.txt -q && echo "KURULUM OK"
rm -rf .venv_test
```
Expected: `KURULUM OK`.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "build: requirements.txt'e matplotlib eklendi (notebook görseli)"
```

---

### Task 8: Son doğrulama + özet

**Files:** (yok — doğrulama)

- [ ] **Step 1: Tüm testler yeşil**

Run: `source .venv/bin/activate && python -m pytest -q`
Expected: 9 passed.

- [ ] **Step 2: Notebook hatasız (final Restart & Run All)**

Run: `jupyter nbconvert --to notebook --execute --inplace test_dogrulama.ipynb && echo "NOTEBOOK OK"`
Expected: `NOTEBOOK OK`.

- [ ] **Step 3: Branch durumunu özetle**

Run: `git log --oneline origin/main..HEAD && git status -s`
Expected: Task 1-7 commit'leri listelenir; çalışma ağacı temiz. (Push KULLANICI onayıyla yapılır.)

---

## Self-Review (plan yazımı sonrası)

- **Spec kapsamı:** §2 kanonik sorgu → Task 1; §4.1 Hücre A-F → Task 5; eşdeğerlik (§4.1 Hücre C) → Task 2; edge (Hücre D) → Task 3; zaman (Hücre E) → Task 4; görsel (Hücre F) → Task 5; test_raporu (§4.2) → Task 6; requirements (§4.3) → Task 7; hata yönetimi (§5: MD5, install fallback, edge bulgusu) → Task 0/5/3; kabul kriterleri (§8) → Task 8. Tüm spec maddeleri bir task'a bağlı. ✔
- **Placeholder taraması:** Rapor şablonundaki `<X>/<Y>` Task 6 Step 1'de gerçek değerlerle doldurulup Step 3'te grep ile doğrulanıyor — kasıtlı ve kapatılıyor. ✔
- **Tip tutarlılığı:** `polars_kanonik`, `pandas_kanonik`, `normalize`, `esdeger_mi`, `sure_olc`, sabitler (`GROUP_KEYS`, `SONUC_SUTUNLAR`, `VERI_YOLU`, `BEKLENEN_MD5`) tüm task'larda aynı imzayla kullanılıyor. ✔
