from datetime import date

from src.schema import akis_hatalari, akista_gorunur

BUGUN = date(2026, 11, 5)


def gonderi(**d):
    g = {"id": "g1", "kurum": "Örnek A.Ş.", "baslik": "2027 Yaz Stajı başvuruları açıldı", "tur": "yaz-staji",
         "url": "https://www.linkedin.com/posts/ornek_staj-activity-7390000000000000000-abcd", "eklenme": "2026-11-05"}
    g.update(d)
    return g


def test_gecerli_gonderi():
    assert akis_hatalari([gonderi()]) == []
    assert akis_hatalari([gonderi(url="https://www.linkedin.com/jobs/view/4300000000", son_basvuru="2027-01-15")]) == []


def test_linkedin_disi_link_reddedilir():
    assert any("LinkedIn" in h for h in akis_hatalari([gonderi(url="https://ornek.com/staj")]))


def test_zorunlu_alan_ve_tur():
    hatalar = akis_hatalari([gonderi(kurum="", tur="part-time")])
    assert any("'kurum' zorunlu" in h for h in hatalar) and any("geçersiz tur" in h for h in hatalar)


def test_ayni_gonderi_iki_kez_eklenemez():
    assert any("iki kez" in h for h in akis_hatalari([gonderi(), gonderi(id="g2")]))


def test_program_id_var_olmali():
    assert akis_hatalari([gonderi(program_id="p1")], {"p1"}) == []
    assert any("program_id" in h for h in akis_hatalari([gonderi(program_id="yok")], {"p1"}))


def test_gorunurluk():
    assert akista_gorunur(gonderi(son_basvuru="2026-11-05"), BUGUN)  # son gün bugün
    assert not akista_gorunur(gonderi(son_basvuru="2026-11-04"), BUGUN)
    assert akista_gorunur(gonderi(paylasim="2026-10-01"), BUGUN)  # 35 gün
    assert not akista_gorunur(gonderi(paylasim="2026-09-01"), BUGUN)  # 65 gün
