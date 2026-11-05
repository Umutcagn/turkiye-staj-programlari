"""Program kaydı şeması ve doğrulama kuralları."""

from __future__ import annotations

import json
import re
import uuid
from datetime import date
from pathlib import Path

TURLER = {"yonetici-adayi", "yaz-staji", "uzun-donem", "yeni-mezun", "erasmus", "yurt-disi",
          "arastirma", "akademi", "yarisma", "hackathon", "genclik"}
ALANLAR = {
    # mühendislik ve teknoloji
    "yazilim", "veri", "makine", "elektrik-elektronik", "insaat", "kimya", "endustri",
    "havacilik-uzay", "cevre-enerji",
    # yönetim bilişim sistemleri: iş analizi, ERP/SAP, BT danışmanlığı, dijital dönüşüm
    "ybs",
    # iş ve ekonomi
    "finans", "pazarlama", "insan-kaynaklari", "is-operasyon",
    # diğer alanlar
    "hukuk", "saglik", "egitim", "sosyal-bilimler", "iletisim-medya", "kamu-uluslararasi",
    "mimarlik", "tasarim", "sanat-kultur", "fen-bilimleri", "ziraat-gida", "turizm",
    "tum-bolumler",
}
BOLGELER = {"TR", "yurt-disi"}
# kesin: bu dönemin tarihi açıklandı · beklenen: geçen yılın tarihi biliniyor
# duyurulmadi: tarih bilinmiyor, uydurulmaz · surekli: yıl boyu başvuru
TARIH_DURUMLARI = {"kesin", "beklenen", "duyurulmadi", "surekli"}
SINIFLAR = {1, 2, 3, 4, "yeni-mezun", "yuksek-lisans"}

ZORUNLU = ("id", "sirket", "program", "tur", "alan", "bolge", "tarih_durumu", "url", "aktif", "eklenme", "guncelleme")
OPSIYONEL = ("sehir", "son_basvuru", "basvuru_acilis", "donem_baslangic", "donem_bitis",
             "sinif", "not_esigi", "ingilizce", "notlar", "linkedin", "ozel")

_TARIH = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# LinkedIn ilanı ya da şirket sayfası: resmi linkin yerine geçmez, yanında durur
LINKEDIN = re.compile(r"^https://([a-z]{2,3}\.|www\.)?linkedin\.com/(jobs|company|posts|feed|school|showcase)/\S+$")


def yeni_id() -> str:
    return str(uuid.uuid4())


def _tarih_mi(deger: object) -> bool:
    if not isinstance(deger, str) or not _TARIH.match(deger):
        return False
    try:
        date.fromisoformat(deger)
    except ValueError:
        return False
    return True


def kayit_hatalari(kayit: dict) -> list[str]:
    """Bir kaydın hatalarını döndürür; boş liste geçerli demektir."""
    hatalar: list[str] = []
    etiket = kayit.get("sirket") or kayit.get("id") or "?"

    for alan in ZORUNLU:
        if alan not in kayit or kayit[alan] in (None, "", []):
            hatalar.append(f"{etiket}: '{alan}' zorunlu")
    bilinmeyen = set(kayit) - set(ZORUNLU) - set(OPSIYONEL)
    if bilinmeyen:
        hatalar.append(f"{etiket}: bilinmeyen alan(lar) {sorted(bilinmeyen)}")

    if kayit.get("tur") and kayit["tur"] not in TURLER:
        hatalar.append(f"{etiket}: geçersiz tur '{kayit['tur']}'")
    for a in kayit.get("alan") or []:
        if a not in ALANLAR:
            hatalar.append(f"{etiket}: geçersiz alan '{a}'")
    if kayit.get("bolge") and kayit["bolge"] not in BOLGELER:
        hatalar.append(f"{etiket}: geçersiz bolge '{kayit['bolge']}'")
    if kayit.get("tarih_durumu") and kayit["tarih_durumu"] not in TARIH_DURUMLARI:
        hatalar.append(f"{etiket}: geçersiz tarih_durumu '{kayit['tarih_durumu']}'")
    for s in kayit.get("sinif") or []:
        if s not in SINIFLAR:
            hatalar.append(f"{etiket}: geçersiz sinif '{s}'")

    url = kayit.get("url")
    if url and not str(url).startswith("https://"):
        hatalar.append(f"{etiket}: url resmi ilan linki olmalı (https://)")
    elif url and LINKEDIN.match(str(url)):
        hatalar.append(f"{etiket}: url resmi sayfa olmalı; LinkedIn linkini 'linkedin' alanına yaz")
    li = kayit.get("linkedin")
    if li is not None and not (isinstance(li, str) and LINKEDIN.match(li)):
        hatalar.append(f"{etiket}: linkedin https://www.linkedin.com/jobs|company|posts/... biçiminde olmalı")

    for alan in ("eklenme", "guncelleme"):
        if kayit.get(alan) and not _tarih_mi(kayit[alan]):
            hatalar.append(f"{etiket}: '{alan}' YYYY-AA-GG olmalı")

    son = kayit.get("son_basvuru")
    durum = kayit.get("tarih_durumu")
    if son is not None and not _tarih_mi(son):
        hatalar.append(f"{etiket}: 'son_basvuru' YYYY-AA-GG olmalı")
    if durum in ("kesin", "beklenen") and son is None:
        hatalar.append(f"{etiket}: '{durum}' tarih durumunda son_basvuru gerekli")
    if durum in ("surekli", "duyurulmadi") and son is not None:
        hatalar.append(f"{etiket}: '{durum}' programda son_basvuru boş olmalı")

    # Başvuru penceresi ve staj dönemi: beklenen kayıtlarda bunlar da geçen yılın tarihleri
    for alan in ("basvuru_acilis", "donem_baslangic", "donem_bitis"):
        if kayit.get(alan) is not None and not _tarih_mi(kayit[alan]):
            hatalar.append(f"{etiket}: '{alan}' YYYY-AA-GG olmalı")
    acilis = kayit.get("basvuru_acilis")
    if acilis and _tarih_mi(acilis) and son and _tarih_mi(son) and acilis > son:
        hatalar.append(f"{etiket}: basvuru_acilis son_basvuru'dan sonra olamaz")
    d_bas, d_bit = kayit.get("donem_baslangic"), kayit.get("donem_bitis")
    if d_bas and d_bit and _tarih_mi(d_bas) and _tarih_mi(d_bit) and d_bas > d_bit:
        hatalar.append(f"{etiket}: donem_baslangic donem_bitis'ten sonra olamaz")

    esik = kayit.get("not_esigi")
    if esik is not None and not (isinstance(esik, (int, float)) and 0 < esik <= 4):
        hatalar.append(f"{etiket}: not_esigi 0–4 arası olmalı (bilinmiyorsa null)")

    if not isinstance(kayit.get("aktif", True), bool):
        hatalar.append(f"{etiket}: aktif true/false olmalı")
    return hatalar


AKIS_ZORUNLU = ("id", "kurum", "baslik", "tur", "url", "eklenme")
AKIS_OPSIYONEL = ("paylasim", "son_basvuru", "notlar", "program_id")
AKIS_OMUR_GUN = 45  # son başvurusu yazmayan gönderi bu kadar gün sonra panodan düşer


def akis_hatalari(akis: list[dict], program_idleri: set[str] | None = None) -> list[str]:
    """data/linkedin.json: dashboard'daki 'LinkedIn'den' bölümünün kayıtları.

    Bunlar LinkedIn gönderisi ya da ilanına giden bağlantılardır; resmi ilan yerine
    geçmez. Resmi sayfası doğrulanan fırsat programs.json'a ayrıca eklenir ve
    program_id ile bağlanır.
    """
    hatalar: list[str] = []
    gorulen_id: set[str] = set()
    gorulen_url: set[str] = set()
    for g in akis:
        etiket = g.get("baslik") or g.get("id") or "?"
        for alan in AKIS_ZORUNLU:
            if g.get(alan) in (None, "", []):
                hatalar.append(f"[linkedin] {etiket}: '{alan}' zorunlu")
        bilinmeyen = set(g) - set(AKIS_ZORUNLU) - set(AKIS_OPSIYONEL)
        if bilinmeyen:
            hatalar.append(f"[linkedin] {etiket}: bilinmeyen alan(lar) {sorted(bilinmeyen)}")
        if g.get("tur") and g["tur"] not in TURLER:
            hatalar.append(f"[linkedin] {etiket}: geçersiz tur '{g['tur']}'")
        if g.get("url") and not LINKEDIN.match(str(g["url"])):
            hatalar.append(f"[linkedin] {etiket}: url bir LinkedIn ilanı ya da gönderisi olmalı")
        for alan in ("eklenme", "paylasim", "son_basvuru"):
            if g.get(alan) is not None and not _tarih_mi(g[alan]):
                hatalar.append(f"[linkedin] {etiket}: '{alan}' YYYY-AA-GG olmalı")
        if program_idleri is not None and g.get("program_id") and g["program_id"] not in program_idleri:
            hatalar.append(f"[linkedin] {etiket}: program_id programs.json'da yok")
        if g.get("id") in gorulen_id:
            hatalar.append(f"[linkedin] tekrarlanan id {g['id']}")
        if g.get("url") in gorulen_url:
            hatalar.append(f"[linkedin] {etiket}: aynı gönderi iki kez eklenmiş")
        gorulen_id.add(g.get("id"))
        gorulen_url.add(g.get("url"))
    return hatalar


def akista_gorunur(g: dict, bugun: date) -> bool:
    """Son başvurusu geçmemiş; son başvurusu yoksa AKIS_OMUR_GUN günden yeni gönderi."""
    if g.get("son_basvuru"):
        return date.fromisoformat(g["son_basvuru"]) >= bugun
    tarih = g.get("paylasim") or g["eklenme"]
    return (bugun - date.fromisoformat(tarih)).days <= AKIS_OMUR_GUN


def liste_hatalari(kayitlar: list[dict], public: bool) -> list[str]:
    hatalar: list[str] = []
    gorulen: set[str] = set()
    for k in kayitlar:
        hatalar.extend(kayit_hatalari(k))
        kid = k.get("id")
        if kid in gorulen:
            hatalar.append(f"tekrarlanan id {kid}")
        gorulen.add(kid)
        if public and k.get("ozel"):
            hatalar.append(f"{k.get('sirket')}: 'ozel' kayıt public listede olamaz")
    return hatalar


def yukle(yol: Path) -> list[dict]:
    if not yol.exists():
        return []
    return json.loads(yol.read_text(encoding="utf-8"))


def kaydet(yol: Path, kayitlar: list[dict]) -> None:
    kayitlar = sorted(kayitlar, key=lambda k: (k["sirket"].casefold(), k["program"].casefold()))
    yol.write_text(json.dumps(kayitlar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
