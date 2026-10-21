from datetime import date

import pytest

from src.readme import BASLANGIC, BITIS, bolumler, liste_markdown, readme_uret

BUGUN = date(2026, 10, 21)


def test_tarihi_gecen_kapanmisa_duser(kayit):
    gecmis = kayit(id="1", son_basvuru="2026-10-20")
    bugun_son = kayit(id="2", son_basvuru="2026-10-21")  # son gün hâlâ açık
    b = bolumler([gecmis, bugun_son], BUGUN)
    assert [k["id"] for k in b["kapandi"]] == ["1"]
    assert [k["id"] for k in b["acik"]] == ["2"]


def test_pasif_kayit_kapanmis(kayit):
    assert bolumler([kayit(aktif=False)], BUGUN)["kapandi"]


def test_beklenen_tarih_gecse_de_kapanmaz(kayit):
    k = kayit(tarih_durumu="beklenen", son_basvuru="2026-02-15")
    assert bolumler([k], BUGUN)["beklenen"] == [k]


def test_duyurulmadi_beklenende_tarihsiz_ve_en_sonda(kayit):
    tarihsiz = kayit(id="t", tarih_durumu="duyurulmadi", son_basvuru=None, notlar="Mart'ta açılır")
    tarihli = kayit(id="d", tarih_durumu="beklenen", son_basvuru="2026-03-01")
    b = bolumler([tarihsiz, tarihli], BUGUN)
    assert [k["id"] for k in b["beklenen"]] == ["d", "t"]
    md = liste_markdown([tarihsiz], BUGUN)
    assert "Henüz duyurulmadı" in md and "Mart'ta açılır" in md


def test_ozet_sayilari_tarih_durumuna_gore(kayit):
    kayitlar = [
        kayit(id="1"),  # kesin, açık
        kayit(id="2", tarih_durumu="surekli", son_basvuru=None),
        kayit(id="3", bolge="yurt-disi", tarih_durumu="duyurulmadi", son_basvuru=None),
        kayit(id="4", son_basvuru="2026-01-01"),  # kapandı
    ]
    assert "**4 program** · 2 açık · 1 beklenen" in liste_markdown(kayitlar, BUGUN)


def test_yurt_disi_ayri_bolumde(kayit):
    k = kayit(bolge="yurt-disi", tur="yurt-disi")
    assert bolumler([k], BUGUN)["yurt_disi"] == [k]


def test_acik_programlar_tarihe_gore_sirali(kayit):
    gec = kayit(id="gec", son_basvuru="2027-03-01")
    erken = kayit(id="erken", son_basvuru="2026-11-10")
    assert [k["id"] for k in bolumler([gec, erken], BUGUN)["acik"]] == ["erken", "gec"]


def test_cikti_deterministik(kayit):
    kayitlar = [kayit(id="1"), kayit(id="2", sirket="Başka", son_basvuru="2026-12-01")]
    assert liste_markdown(kayitlar, BUGUN) == liste_markdown(list(reversed(kayitlar)), BUGUN)


def test_bilinmeyen_sart_uydurulmaz(kayit):
    md = liste_markdown([kayit(sinif=[], not_esigi=None, ingilizce=None)], BUGUN)
    assert "Belirtilmemiş" in md


def test_pipe_karakteri_tabloyu_bozmaz(kayit):
    assert "A \\| B" in liste_markdown([kayit(program="A | B")], BUGUN)


def test_sablon_disi_korunur(kayit):
    sablon = f"ÜST\n{BASLANGIC}\neski\n{BITIS}\nALT"
    cikti = readme_uret(sablon, [kayit()], BUGUN)
    assert cikti.startswith("ÜST\n") and cikti.endswith("ALT") and "eski" not in cikti


def test_isaretsiz_sablon_hata(kayit):
    with pytest.raises(ValueError):
        readme_uret("işaret yok", [kayit()], BUGUN)
