from src.schema import kayit_hatalari, liste_hatalari


def test_gecerli_kayit(kayit):
    assert kayit_hatalari(kayit()) == []


def test_url_zorunlu_ve_https(kayit):
    assert any("'url' zorunlu" in h for h in kayit_hatalari(kayit(url="")))
    assert any("https" in h for h in kayit_hatalari(kayit(url="http://ornek.com")))


def test_gecersiz_tur_ve_alan(kayit):
    hatalar = kayit_hatalari(kayit(tur="part-time", alan=["uzay"]))
    assert any("geçersiz tur" in h for h in hatalar)
    assert any("geçersiz alan" in h for h in hatalar)


def test_kesin_tarihte_son_basvuru_gerekli(kayit):
    assert kayit_hatalari(kayit(son_basvuru=None))
    assert kayit_hatalari(kayit(tarih_durumu="surekli", son_basvuru=None)) == []
    assert kayit_hatalari(kayit(tarih_durumu="surekli"))  # sürekli + tarih çelişki
    assert kayit_hatalari(kayit(tarih_durumu="duyurulmadi", son_basvuru=None)) == []
    assert kayit_hatalari(kayit(tarih_durumu="duyurulmadi"))  # duyurulmadıysa tarih uydurulmaz


def test_gecersiz_tarih(kayit):
    assert kayit_hatalari(kayit(son_basvuru="2027-02-30"))
    assert kayit_hatalari(kayit(eklenme="21.10.2026"))


def test_not_esigi_araligi(kayit):
    assert kayit_hatalari(kayit(not_esigi=2.5)) == []
    assert kayit_hatalari(kayit(not_esigi=75))  # 100'lük sistem değil, 4'lük


def test_bilinmeyen_alan(kayit):
    assert any("bilinmeyen" in h for h in kayit_hatalari(kayit(maas=1000)))


def test_tekrarlanan_id(kayit):
    assert any("tekrarlanan" in h for h in liste_hatalari([kayit(), kayit()], public=True))


def test_ozel_kayit_public_listede_olamaz(kayit):
    assert liste_hatalari([kayit(ozel=True)], public=True)
    assert liste_hatalari([kayit(ozel=True)], public=False) == []
