"""site/ şablonunu ve veriyi statik bir klasöre derler (GitHub Pages ya da yerel)."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from src.readme import ALAN_ETIKET, TUR_ETIKET

REPO = "Umutcagn/turkiye-staj-programlari"


VARSAYILAN_BOLUM = {"ad": "Endüstri Müh.", "alanlar": ["endustri", "is-operasyon", "tum-bolumler"],
                    "turler": ["yonetici-adayi"], "ilgi_alanlari": [], "hedef_basvuru": 25,
                    "ozel_repo": "Umutcagn/staj-ozel"}


def bolum_ayari(profil: dict) -> dict:
    """Özel sitedeki 'Bölümüm' sekmesinin ayarı: profile.json → bolum, eksikler varsayılandan."""
    bolum = {**VARSAYILAN_BOLUM, **profil.get("bolum", {})}
    # Ana bölümün dışında ilgilenilen alanlar (ör. veri, tasarım): sekmede ayrı filtre olur
    bolum["ilgi_alanlari"] = [a for a in bolum["ilgi_alanlari"] if a in ALAN_ETIKET and a not in bolum["alanlar"]]
    bolum["agirliklar"] = profil["agirliklar"]
    # Hangi şirketlere gerçekten puan verildi; verilmeyenler sitede "varsayılan 3" diye işaretlenir
    bolum["puanlanan"] = {"statu": sorted(profil.get("statu_puani", {})), "efor": sorted(profil.get("efor_puani", {}))}
    return bolum


def veri_js(programlar: list[dict], ozel: bool, bolum: dict | None = None,
            linkedin: list[dict] | None = None) -> str:
    veri = {"programlar": programlar, "linkedin": linkedin or [], "alanlar": ALAN_ETIKET, "turler": TUR_ETIKET,
            "repo": REPO, "ozel": ozel}
    if ozel and bolum:
        veri["bolum"] = bolum
    return "window.STAJ = " + json.dumps(veri, ensure_ascii=False, separators=(",", ":")) + ";\n"


def skorla(programlar: list[dict], profil: dict, bugun: date) -> list[dict]:
    """Uygun olanlara TOPSIS skoru, elenenlere elenme nedenini ekler."""
    from src.score import sirala

    sirali, elenen = sirala(programlar, profil, bugun)
    sonuc = [{**p, "kriterler": {a: round(d, 3) for a, d in p["kriterler"].items()}} for p in sirali]
    for p, neden in elenen:
        not_ = f"Elendi: {neden}" + (f" · {p['notlar']}" if p.get("notlar") else "")
        sonuc.append(dict(p, skor=None, notlar=not_, elenme=neden))
    return sonuc


def derle(kaynak: Path, hedef: Path, programlar: list[dict], ozel: bool, bolum: dict | None = None,
          linkedin: list[dict] | None = None) -> Path:
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(kaynak, hedef)
    (hedef / "data.js").write_text(veri_js(programlar, ozel, bolum, linkedin), encoding="utf-8")
    if ozel:
        html = hedef / "index.html"
        html.write_text(html.read_text(encoding="utf-8").replace(
            "<title>Staj Takvimi</title>", "<title>Staj Takvimi · Özel</title>\n  <meta name=\"robots\" content=\"noindex\">"),
            encoding="utf-8")
    return hedef / "index.html"
