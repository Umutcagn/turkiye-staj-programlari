"""Onaylanmış issue formunu programs.json'a işler.

Issue gövdesi kullanıcı girdisidir: yalnızca bilinen başlıklar okunur, sonuç
şema doğrulamasından geçmeden hiçbir şey yazılmaz.
"""

from __future__ import annotations

import re
from datetime import date

from src import schema
from src.readme import ALAN_ETIKET, TUR_ETIKET

BOS = {"", "_No response_", "None"}

# Issue formundaki başlık → kayıt alanı
BASLIKLAR = {
    "Şirket": "sirket", "Program adı": "program", "Program türü": "tur", "Alan(lar)": "alan",
    "Bölge": "bolge", "Şehir(ler)": "sehir", "Son başvuru tarihi": "son_basvuru",
    "Başvurunun açıldığı tarih": "basvuru_acilis", "Staj/program başlangıcı": "donem_baslangic",
    "Staj/program bitişi": "donem_bitis",
    "Tarih durumu": "tarih_durumu", "Başvurabilecek sınıflar": "sinif",
    "Not ortalaması eşiği": "not_esigi", "İngilizce şartı": "ingilizce",
    "Resmi ilan linki": "url", "Not": "notlar", "Kapanan programın linki": "kapanan_url",
}
_TUR_TERS = {v: k for k, v in TUR_ETIKET.items()}
_ALAN_TERS = {v: k for k, v in ALAN_ETIKET.items()}
_DURUM_TERS = {"Kesin (bu dönem açıklandı)": "kesin", "Beklenen (geçen yılın tarihi)": "beklenen",
               "Henüz duyurulmadı": "duyurulmadi", "Sürekli açık": "surekli"}
_SINIF_TERS = {"1": 1, "2": 2, "3": 3, "4": 4, "Yeni mezun": "yeni-mezun", "Yüksek lisans": "yuksek-lisans"}


def formu_ayristir(govde: str) -> dict[str, str]:
    """'### Başlık\\n\\ndeğer' bloklarını sözlüğe çevirir."""
    alanlar: dict[str, str] = {}
    for blok in re.split(r"^### ", govde or "", flags=re.M)[1:]:
        baslik, _, deger = blok.partition("\n")
        if baslik.strip() in BASLIKLAR:
            alanlar[BASLIKLAR[baslik.strip()]] = deger.strip()
    return {k: v for k, v in alanlar.items() if v not in BOS}


def _liste(deger: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,\n]", deger) if p.strip()]


def kayit_olustur(form: dict[str, str], bugun: date) -> dict:
    k = {
        "id": schema.yeni_id(),
        "sirket": form.get("sirket", ""), "program": form.get("program", ""),
        "tur": _TUR_TERS.get(form.get("tur", ""), form.get("tur", "")),
        "alan": [_ALAN_TERS.get(a, a) for a in _liste(form.get("alan", ""))],
        "bolge": "yurt-disi" if form.get("bolge") == "Yurt dışı" else "TR",
        "sehir": _liste(form.get("sehir", "")),
        "son_basvuru": form.get("son_basvuru") or None,
        "basvuru_acilis": form.get("basvuru_acilis") or None,
        "donem_baslangic": form.get("donem_baslangic") or None,
        "donem_bitis": form.get("donem_bitis") or None,
        "tarih_durumu": _DURUM_TERS.get(form.get("tarih_durumu", ""), form.get("tarih_durumu", "")),
        "sinif": [_SINIF_TERS.get(s, s) for s in _liste(form.get("sinif", ""))],
        "not_esigi": None, "ingilizce": form.get("ingilizce") or None,
        "url": form.get("url", ""), "aktif": True,
        "eklenme": bugun.isoformat(), "guncelleme": bugun.isoformat(),
    }
    if form.get("not_esigi"):
        try:
            k["not_esigi"] = float(form["not_esigi"].replace(",", "."))
        except ValueError:
            k["not_esigi"] = form["not_esigi"]  # şema hatası olarak yakalanır
    if form.get("notlar"):
        k["notlar"] = form["notlar"][:200]
    return k


def isle(govde: str, etiketler: list[str], kayitlar: list[dict], bugun: date) -> tuple[list[dict], str]:
    """(yeni kayıt listesi, özet mesajı) döndürür; geçersizse ValueError."""
    form = formu_ayristir(govde)
    if "kapandi" in etiketler:
        url = form.get("kapanan_url", "")
        eslesen = [k for k in kayitlar if k["url"] == url and k.get("aktif", True)]
        if not eslesen:
            raise ValueError(f"Bu linkle aktif kayıt bulunamadı: {url}")
        for k in eslesen:
            k["aktif"], k["guncelleme"] = False, bugun.isoformat()
        return kayitlar, f"Kapandı olarak işaretlendi: {eslesen[0]['sirket']} – {eslesen[0]['program']}"

    yeni = kayit_olustur(form, bugun)
    if any(k["url"] == yeni["url"] and k["program"] == yeni["program"] for k in kayitlar):
        raise ValueError("Bu program zaten listede")
    hatalar = schema.liste_hatalari(kayitlar + [yeni], public=True)
    if hatalar:
        raise ValueError("Form geçersiz:\n- " + "\n- ".join(hatalar))
    return kayitlar + [yeni], f"Eklendi: {yeni['sirket']} – {yeni['program']}"
