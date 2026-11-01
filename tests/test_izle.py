from datetime import date

from src import izle

BUGUN = date(2026, 11, 1)


def test_sayfa_metni_script_ve_etiketleri_atar():
    ham = "<html><script>var x='2027'</script><p>Başvurular&nbsp;açıldı</p><div>Son gün: 14 Aralık 2026</div></html>"
    assert izle.sayfa_metni(ham) == ["Başvurular açıldı", "Son gün: 14 Aralık 2026"]


def test_hedef_yil_beklenen_tarihi_kaydirir(kayit):
    k = kayit(tarih_durumu="beklenen", son_basvuru="2026-03-31")
    assert izle.hedef_yil(k, BUGUN) == 2027
    assert izle.hedef_yil(kayit(tarih_durumu="duyurulmadi", son_basvuru=None), BUGUN) == 2027
    # Aralık 2026'da kapanacak beklenen başvuru: yeni dönem 2027'de aranır, telif yılı 2026'da değil
    assert izle.hedef_yil(kayit(tarih_durumu="beklenen", son_basvuru="2025-12-15"), BUGUN) == 2027


def test_telif_satiri_yok_sayilir():
    assert izle.sayfa_metni("<p>Staj</p><footer><p>© 2027 Şirket. All rights reserved.</p></footer>") == ["Staj"]


def _imza(satirlar, yil=2027):
    return izle.imza(satirlar * 20, yil)  # kısa sayfa sayılmasın diye çoğalt


def test_yeni_yil_ilk_kez_gorununce_guclu():
    eski = _imza(["2026 başvuruları kapandı. Teşekkürler, görüşmek üzere."])
    yeni = _imza(["2027 başvuruları açıldı, son gün 15 Şubat 2027"])
    assert izle.karsilastir(eski, yeni) == "guclu"


def test_anahtar_satir_degisince_zayif_degismezse_sessiz():
    eski = _imza(["Başvurular yakında açılacak, takipte kalın sevgili adaylar"])
    assert izle.karsilastir(eski, _imza(["Başvurular yakında açılacak, takipte kalın sevgili adaylar"])) is None
    assert izle.karsilastir(eski, _imza(["Başvuru formu güncellendi, takipte kalın sevgili adaylar"])) == "zayif"


def test_ilk_kontrolde_yalnizca_yil_geciyorsa_bildirir():
    assert izle.karsilastir(None, _imza(["Başvurular yakında, takipte kalın sevgili adaylar"])) is None
    assert izle.karsilastir(None, _imza(["2027 dönemi başvuruları açık, takipte kalın"])) == "guclu"


def test_kisa_sayfa_bildirilmez():
    assert izle.karsilastir(None, izle.imza(["2027"], 2027)) is None


def test_bulgu_kayit_guncellenene_kadar_kalir(kayit):
    k = kayit(tarih_durumu="duyurulmadi", son_basvuru=None, guncelleme="2026-10-21")
    eski = _imza(["2026 başvuruları kapandı. Teşekkürler, görüşmek üzere."])
    yeni = _imza(["2027 başvuruları açıldı, son gün 15 Şubat 2027"])
    d1 = izle.durum_guncelle(k, eski, yeni, ["2027 başvuruları açıldı"], BUGUN)
    assert d1["bulgu"]["seviye"] == "guclu"
    d2 = izle.durum_guncelle(k, d1, yeni, [], date(2026, 11, 2))  # değişiklik yok ama bulgu sürer
    assert d2["bulgu"]["seviye"] == "guclu"
    k["guncelleme"] = "2026-11-01"  # kayıt bulgu günü elle kontrol edildi
    assert "bulgu" not in izle.durum_guncelle(k, d2, yeni, [], date(2026, 11, 3))


def test_rapor_bolumleri(kayit):
    metin = izle.rapor([(kayit(program="A"), "guclu", ["2027 başvuruları açıldı"]),
                        (kayit(program="B"), "zayif", [])], [(kayit(program="C"), "HTTP 404")], 3)
    assert metin.index("– A") < metin.index("## Sayfa değişti") < metin.index("– B") < metin.index("## Okunamadı")
    assert "> 2027 başvuruları açıldı" in metin
