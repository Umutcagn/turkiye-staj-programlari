"""Duyuru izleyicisi: tarihi henüz açıklanmamış programların resmi sayfalarını izler.

Siteye özel kazıyıcı yok. Her sayfadan yalnızca "başvuru, son tarih, deadline"
gibi kelimeler ya da yeni dönemin yılı geçen satırlar çıkarılır; bu satırlar
değişince ya da yeni dönem yılı sayfada ilk kez görününce rapor edilir. Karar
yine insanındır: rapor, kaydı güncellemek için bir kontrol listesidir.
"""

from __future__ import annotations

import hashlib
import html
import re
from datetime import date

from src.score import sonraki_tarih

ANAHTAR = re.compile(
    r"başvuru|son tarih|son gün|açıldı|başladı|kayıt|duyuru|"
    r"deadline|apply|application|call for|registration|opens?\b|closes?\b", re.I)
_BLOK = re.compile(r"</?(p|div|li|h[1-6]|br|tr|td|section|article|span)\b[^>]*>", re.I)
_GURULTU = re.compile(r"<(script|style|noscript|svg)\b.*?</\1>", re.I | re.S)
_TELIF = re.compile(r"©|\(c\)|all rights reserved|tüm hakları", re.I)
EN_AZ_METIN = 300  # bundan kısaysa sayfa büyük ihtimalle JavaScript ile çiziliyor


def sayfa_metni(ham: str) -> list[str]:
    """HTML'den boş olmayan, tekrarsız metin satırları."""
    ham = _BLOK.sub("\n", _GURULTU.sub(" ", ham))
    metin = html.unescape(re.sub(r"<[^>]+>", " ", ham))
    satirlar = (" ".join(s.split()) for s in metin.splitlines())
    return list(dict.fromkeys(s for s in satirlar if s and not _TELIF.search(s)))


def hedef_yil(k: dict, bugun: date) -> int:
    """Beklenen bir sonraki dönemin yılı: duyuru gelince sayfada bu yıl geçer.

    İçinde bulunulan yıl sayfalarda zaten her yerde geçtiği için (haberler, tarihler)
    hedef her zaman en az gelecek yıldır: Aralık'ta kapanan bir başvuru da
    genelde ertesi yılın dönemi içindir.
    """
    tarih = sonraki_tarih(k, bugun)
    return max(tarih.year if tarih else 0, bugun.year + 1)


def imza(satirlar: list[str], yil: int) -> dict:
    yil_metni = str(yil)
    onemli = sorted(s for s in satirlar if len(s) <= 400 and (yil_metni in s or ANAHTAR.search(s)))
    return {
        "imza": hashlib.sha1("\n".join(onemli).encode("utf-8")).hexdigest()[:16],
        "yil": yil,
        "yil_sayisi": sum(s.count(yil_metni) for s in satirlar),
        "kisa": sum(map(len, satirlar)) < EN_AZ_METIN,
    }


def ornek_satirlar(satirlar: list[str], yil: int, n: int = 3) -> list[str]:
    """Raporda gösterilecek, yeni dönem yılını içeren ilk birkaç satır."""
    bulunan = [s for s in satirlar if str(yil) in s and len(s) <= 400]
    return [s if len(s) <= 220 else s[:217] + "…" for s in bulunan[:n]]


def karsilastir(eski: dict | None, yeni: dict) -> str | None:
    """Bildirilecek bir şey varsa seviyesini döndürür: 'guclu' ya da 'zayif'."""
    if yeni["kisa"]:
        return None
    if eski is None or eski.get("yil") != yeni["yil"]:
        return "guclu" if yeni["yil_sayisi"] else None  # ilk kontrol: yıl zaten geçiyorsa bildir
    if not eski.get("yil_sayisi") and yeni["yil_sayisi"]:
        return "guclu"
    if eski.get("imza") != yeni["imza"]:
        return "zayif"
    return None


def durum_guncelle(k: dict, eski: dict | None, yeni: dict, ornek: list[str], bugun: date) -> dict:
    """Kaydın yeni izleme durumu. Bulgu, kayıt elle kontrol edilip 'guncelleme'
    tarihi bulgu günü ya da sonrasına çekilene kadar her raporda kalır."""
    bulgu = (eski or {}).get("bulgu")
    seviye = karsilastir(eski, yeni)
    if seviye:
        if bulgu and bulgu["seviye"] == "guclu":
            seviye = "guclu"  # güçlü bulgu, sonraki küçük değişiklikle zayıflamaz
        bulgu = {"seviye": seviye, "ornek": ornek, "tarih": bugun.isoformat()}
    if bulgu and k.get("guncelleme", "") >= bulgu["tarih"]:
        bulgu = None
    return {**yeni, **({"bulgu": bulgu} if bulgu else {})}


def izlenecek_mi(k: dict) -> bool:
    return k.get("aktif", True) and k["tarih_durumu"] in ("beklenen", "duyurulmadi")


def rapor(bulgular: list[tuple[dict, str, list[str]]], hatalar: list[tuple[dict, str]], toplam: int) -> str:
    """bulgular: (kayıt, seviye, örnek satırlar). Issue gövdesi döndürür."""
    def blok(seviye: str) -> list[str]:
        cikti = []
        for k, sv, ornek in bulgular:
            if sv != seviye:
                continue
            cikti.append(f"- [ ] **{k['sirket']} – {k['program']}** — {k['url']}")
            cikti += [f"  > {s}" for s in ornek]
        return cikti

    guclu, zayif = blok("guclu"), blok("zayif")
    parcalar = [f"Duyuru izleyicisi: tarihi açıklanmamış {toplam} programın resmi sayfası kontrol edildi. "
                "Bu issue her çalışmada güncellenir. Tarihi resmi sayfadan doğrulayıp kaydı güncelle."]
    if guclu:
        parcalar += ["", "## Yeni dönem duyurulmuş olabilir", "", "Sayfada yeni dönemin yılı geçiyor.", "", *guclu]
    if zayif:
        parcalar += ["", "## Sayfa değişti", "", "Başvuru/tarih geçen satırlar değişti; duyuru olabilir ya da olmayabilir.",
                     "", *zayif]
    if hatalar:
        parcalar += ["", "## Okunamadı", "", *[f"- {k['sirket']} – {k['program']}: {n}" for k, n in hatalar]]
    if not guclu and not zayif:
        parcalar += ["", "Yeni bir değişiklik yok."]
    return "\n".join(parcalar)
