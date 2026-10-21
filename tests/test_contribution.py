from datetime import date

import pytest

from src.contribution import formu_ayristir, isle

BUGUN = date(2026, 10, 21)

FORM = """### Şirket

Örnek Teknoloji

### Program adı

Yaz Stajı 2027

### Program türü

Yaz stajı

### Alan(lar)

Yazılım, Veri

### Bölge

Türkiye

### Şehir(ler)

İstanbul

### Son başvuru tarihi

2027-03-15

### Tarih durumu

Kesin (bu dönem açıklandı)

### Başvurabilecek sınıflar

3, 4

### Not ortalaması eşiği

2,50

### İngilizce şartı

_No response_

### Resmi ilan linki

https://ornek.com/staj
"""


def test_form_ayristirilir():
    f = formu_ayristir(FORM)
    assert f["sirket"] == "Örnek Teknoloji" and "ingilizce" not in f


def test_yeni_kayit_eklenir():
    kayitlar, mesaj = isle(FORM, ["approved"], [], BUGUN)
    k = kayitlar[0]
    assert k["tur"] == "yaz-staji" and k["alan"] == ["yazilim", "veri"]
    assert k["sinif"] == [3, 4] and k["not_esigi"] == 2.5 and k["ingilizce"] is None
    assert "Eklendi" in mesaj


def test_tekrar_eklenemez():
    kayitlar, _ = isle(FORM, ["approved"], [], BUGUN)
    with pytest.raises(ValueError, match="zaten"):
        isle(FORM, ["approved"], kayitlar, BUGUN)


def test_gecersiz_form_yazilmaz():
    with pytest.raises(ValueError, match="geçersiz"):
        isle(FORM.replace("https://ornek.com/staj", "javascript:alert(1)"), ["approved"], [], BUGUN)


def test_kapandi_isaretlenir():
    kayitlar, _ = isle(FORM, ["approved"], [], BUGUN)
    govde = "### Kapanan programın linki\n\nhttps://ornek.com/staj\n"
    kayitlar, mesaj = isle(govde, ["approved", "kapandi"], kayitlar, BUGUN)
    assert kayitlar[0]["aktif"] is False and "Kapandı" in mesaj
