from datetime import date

import pytest

from src.score import sirala, sonraki_tarih, topsis, uygunluk

BUGUN = date(2026, 10, 21)


def test_topsis_elle_hesaplanan_ornek():
    # 2 alternatif, 2 eşit ağırlıklı kriter: A her ikisinde de baskın → 100, B → 0
    assert topsis([[2, 1], [1, 2]], [1, 1], ["fayda", "maliyet"]) == [100.0, 0.0]


def test_topsis_uc_alternatif_bilinen_sonuc():
    # Normalize: sütun normları √14 ve √14; ağırlık 0.5/0.5
    # C3: fayda en yüksek (3), maliyet en düşük (1) → ideal = 100
    skor = topsis([[1, 3], [2, 2], [3, 1]], [1, 1], ["fayda", "maliyet"])
    assert skor[2] == 100.0 and skor[0] == 0.0
    assert skor[1] == pytest.approx(50.0)


def test_topsis_esit_alternatifler_ve_sifir_agirlik():
    assert topsis([[1, 1], [1, 1]], [0, 0], ["fayda", "fayda"]) == [0.0, 0.0]
    assert topsis([], [1], ["fayda"]) == []


def test_beklenen_tarih_sonraki_yila_tasinir(kayit):
    k = kayit(tarih_durumu="beklenen", son_basvuru="2026-03-31")
    assert sonraki_tarih(k, BUGUN) == date(2027, 3, 31)


@pytest.fixture
def profil():
    return {
        "not_ortalamasi": 2.42, "basvurabilecegi_siniflar": [3], "ingilizce": "B2",
        "tur_tercihi": {"yaz-staji": 5, "yonetici-adayi": 2},
        "agirliklar": {"aciliyet": 0.3, "hedef_uyum": 0.3, "statu": 0.25, "efor": 0.15},
    }


def test_uygunluk_nedenleri(kayit, profil):
    assert uygunluk(kayit(), profil, BUGUN) is None
    assert "not eşiği" in uygunluk(kayit(not_esigi=2.5), profil, BUGUN)
    assert "sınıf" in uygunluk(kayit(sinif=[4]), profil, BUGUN)
    assert "İngilizce" in uygunluk(kayit(ingilizce="C1"), profil, BUGUN)
    assert "geçti" in uygunluk(kayit(son_basvuru="2026-01-01"), profil, BUGUN)


def test_sirala_eleneni_ayirir_ve_skora_gore_dizer(kayit, profil):
    yakin = kayit(id="yakin", sirket="A", son_basvuru="2026-11-01")
    uzak = kayit(id="uzak", sirket="B", son_basvuru="2027-06-01")
    elenen = kayit(id="x", sirket="C", not_esigi=3.0)
    sirali, elenenler = sirala([uzak, elenen, yakin], profil, BUGUN)
    assert [k["id"] for k in sirali] == ["yakin", "uzak"]
    assert [k["id"] for k, _ in elenenler] == ["x"]
