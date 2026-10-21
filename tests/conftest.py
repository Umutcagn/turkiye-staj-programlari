import pytest


@pytest.fixture
def kayit():
    def _yap(**degisiklik):
        k = {
            "id": "00000000-0000-0000-0000-000000000001",
            "sirket": "Örnek A.Ş.",
            "program": "Yaz Stajı",
            "tur": "yaz-staji",
            "alan": ["yazilim"],
            "bolge": "TR",
            "sehir": ["İstanbul"],
            "son_basvuru": "2027-02-15",
            "tarih_durumu": "kesin",
            "sinif": [3, 4],
            "not_esigi": None,
            "ingilizce": None,
            "url": "https://ornek.com/kariyer",
            "aktif": True,
            "eklenme": "2026-10-21",
            "guncelleme": "2026-10-21",
        }
        k.update(degisiklik)
        return k
    return _yap
