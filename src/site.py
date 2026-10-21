"""site/ şablonunu ve veriyi statik bir klasöre derler (GitHub Pages ya da yerel)."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from src.readme import ALAN_ETIKET, TUR_ETIKET

REPO = "Umutcagn/turkiye-staj-programlari"


def veri_js(programlar: list[dict], ozel: bool) -> str:
    veri = {"programlar": programlar, "alanlar": ALAN_ETIKET, "turler": TUR_ETIKET, "repo": REPO, "ozel": ozel}
    return "window.STAJ = " + json.dumps(veri, ensure_ascii=False, separators=(",", ":")) + ";\n"


def skorla(programlar: list[dict], profil: dict, bugun: date) -> list[dict]:
    """Uygun olanlara TOPSIS skoru, elenenlere elenme nedenini ekler."""
    from src.score import sirala

    sirali, elenen = sirala(programlar, profil, bugun)
    sonuc = [{k: v for k, v in p.items() if k != "kriterler"} for p in sirali]
    for p, neden in elenen:
        not_ = f"Elendi: {neden}" + (f" · {p['notlar']}" if p.get("notlar") else "")
        sonuc.append(dict(p, skor=None, notlar=not_))
    return sonuc


def derle(kaynak: Path, hedef: Path, programlar: list[dict], ozel: bool) -> Path:
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(kaynak, hedef)
    (hedef / "data.js").write_text(veri_js(programlar, ozel), encoding="utf-8")
    if ozel:
        html = hedef / "index.html"
        html.write_text(html.read_text(encoding="utf-8").replace(
            "<title>Staj Takvimi</title>", "<title>Staj Takvimi · Özel</title>\n  <meta name=\"robots\" content=\"noindex\">"),
            encoding="utf-8")
    return hedef / "index.html"
