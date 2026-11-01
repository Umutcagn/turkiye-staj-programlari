import json
from datetime import date
from pathlib import Path

from src.site import derle, skorla, veri_js

KAYNAK = Path(__file__).resolve().parent.parent / "site"


def _veri(js: str) -> dict:
    assert js.startswith("window.STAJ = ") and js.rstrip().endswith(";")
    return json.loads(js[len("window.STAJ = "):].rstrip().rstrip(";"))


def test_veri_js_gecerli_json_ve_turkce_korunur(kayit):
    v = _veri(veri_js([kayit(sirket="Şişecam")], ozel=False))
    assert v["programlar"][0]["sirket"] == "Şişecam" and v["ozel"] is False


def test_public_derleme_yalnizca_verilen_kayitlari_icerir(tmp_path, kayit):
    sayfa = derle(KAYNAK, tmp_path / "out", [kayit(sirket="Public A.Ş.")], ozel=False)
    js = (sayfa.parent / "data.js").read_text(encoding="utf-8")
    assert "Public A.Ş." in js and '"ozel":false' in js
    assert "noindex" not in sayfa.read_text(encoding="utf-8")
    assert (sayfa.parent / "fonts.css").exists()  # fontlar yerelden, Google'a istek yok


def test_sayfa_ucuncu_taraf_kaynak_yuklemez():
    html = (KAYNAK / "index.html").read_text(encoding="utf-8")
    css = (KAYNAK / "fonts.css").read_text(encoding="utf-8")
    assert "googleapis" not in html and "gstatic" not in css and "http" not in css.split("*/", 1)[1]


def test_ozel_derleme_noindex_ve_skorlu(tmp_path, kayit):
    profil = {"not_ortalamasi": 2.4, "basvurabilecegi_siniflar": [3], "ingilizce": "B2",
              "tur_tercihi": {"yaz-staji": 5}, "agirliklar": {"aciliyet": 1, "hedef_uyum": 1, "statu": 1, "efor": 1}}
    programlar = skorla([kayit(id="a"), kayit(id="b", not_esigi=3.0)], profil, date(2026, 10, 21))
    elenen = next(p for p in programlar if p["id"] == "b")
    assert elenen["skor"] is None and elenen["notlar"].startswith("Elendi:")
    sayfa = derle(KAYNAK, tmp_path / "ozel", programlar, ozel=True)
    assert "noindex" in sayfa.read_text(encoding="utf-8")


def test_ozel_veride_kriter_dokumu_ve_bolum_ayari(kayit):
    from src.site import bolum_ayari
    profil = {"not_ortalamasi": 2.4, "basvurabilecegi_siniflar": [3], "ingilizce": "B2",
              "tur_tercihi": {"yaz-staji": 5}, "agirliklar": {"aciliyet": 1, "hedef_uyum": 1, "statu": 1, "efor": 1},
              "statu_puani": {"Örnek A.Ş.": 5}, "bolum": {"ad": "Endüstri"}}
    programlar = skorla([kayit(id="a"), kayit(id="b", not_esigi=3.0)], profil, date(2026, 10, 21))
    uygun = next(p for p in programlar if p["id"] == "a")
    assert set(uygun["kriterler"]) == {"aciliyet", "hedef_uyum", "statu", "efor"} and uygun["kriterler"]["statu"] == 5
    assert next(p for p in programlar if p["id"] == "b")["elenme"].startswith("not eşiği")
    bolum = bolum_ayari(profil)
    assert bolum["ad"] == "Endüstri" and bolum["hedef_basvuru"] == 25 and bolum["puanlanan"]["statu"] == ["Örnek A.Ş."]
    assert "bolum" in _veri(veri_js(programlar, ozel=True, bolum=bolum))
    assert "bolum" not in _veri(veri_js(programlar, ozel=False, bolum=bolum))  # public'e asla sızmaz
