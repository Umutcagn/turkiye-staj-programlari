"""programs.json → README.md tabloları.

Çıktı yalnızca veriye ve verilen güne bağlıdır; aynı girdi her zaman aynı
README'yi üretir. Kalan gün gibi her gün değişen bilgiler bilerek yazılmaz.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

ALAN_ETIKET = {
    "yazilim": "Yazılım", "veri": "Veri", "finans": "Finans", "pazarlama": "Pazarlama",
    "insan-kaynaklari": "İK", "hukuk": "Hukuk", "makine": "Makine",
    "elektrik-elektronik": "Elektrik-Elektronik", "insaat": "İnşaat", "kimya": "Kimya",
    "endustri": "Endüstri", "is-operasyon": "İş/Operasyon", "tasarim": "Tasarım",
    "tum-bolumler": "Tüm bölümler",
}
TUR_ETIKET = {
    "yonetici-adayi": "Yönetici adayı", "yaz-staji": "Yaz stajı", "uzun-donem": "Uzun dönem staj",
    "yeni-mezun": "Yeni mezun", "erasmus": "Erasmus+", "yurt-disi": "Yurt dışı",
}
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

BASLANGIC = "<!-- LISTE:BASLANGIC -->"
BITIS = "<!-- LISTE:BITIS -->"


def kapandi_mi(k: dict, bugun: date) -> bool:
    if not k.get("aktif", True):
        return True
    return k["tarih_durumu"] == "kesin" and date.fromisoformat(k["son_basvuru"]) < bugun


def _tarih_metni(k: dict) -> str:
    if k["tarih_durumu"] == "surekli":
        return "Sürekli açık"
    if k["tarih_durumu"] == "duyurulmadi":
        return "_Henüz duyurulmadı_" + (f"<br><sub>{_hucre(k['notlar'])}</sub>" if k.get("notlar") else "")
    d = date.fromisoformat(k["son_basvuru"])
    if k["tarih_durumu"] == "beklenen":
        return f"_~{AYLAR[d.month - 1]} (geçen yıl {d.day} {AYLAR[d.month - 1]})_"
    return f"{d.day} {AYLAR[d.month - 1]} {d.year}"


def _sartlar(k: dict) -> str:
    parcalar = []
    if k.get("sinif"):
        parcalar.append("Sınıf: " + ", ".join("Yeni mezun" if s == "yeni-mezun" else
                                              "YL" if s == "yuksek-lisans" else str(s)
                                              for s in k["sinif"]))
    if k.get("not_esigi") is not None:
        parcalar.append(f"Ort. ≥ {k['not_esigi']:.2f}")
    if k.get("ingilizce"):
        parcalar.append(f"İng.: {k['ingilizce']}")
    return "<br>".join(parcalar) or "Belirtilmemiş"


def _hucre(metin: str) -> str:
    return metin.replace("|", "\\|")


def _tablo(kayitlar: list[dict]) -> str:
    satirlar = [
        "| Şirket | Program | Alan | Şehir | Son başvuru | Şartlar | |",
        "|---|---|---|---|---|---|---|",
    ]
    for k in kayitlar:
        satirlar.append("| " + " | ".join([
            f"**{_hucre(k['sirket'])}**",
            _hucre(k["program"]) + f"<br><sub>{TUR_ETIKET[k['tur']]}</sub>",
            ", ".join(ALAN_ETIKET[a] for a in k["alan"]),
            _hucre(", ".join(k.get("sehir") or [])) or "—",
            _tarih_metni(k),
            _sartlar(k),
            f"[Başvur]({k['url']})",
        ]) + " |")
    return "\n".join(satirlar)


def _sirala(kayitlar: list[dict]) -> list[dict]:
    def anahtar(k: dict):
        son = k.get("son_basvuru") or "9999-12-31"  # tarihsizler en sonda
        if k["tarih_durumu"] == "beklenen":
            son = "0000" + son[4:]  # beklenenleri yıl yerine ay-güne göre sırala
        return (son, k["sirket"].casefold(), k["program"].casefold())
    return sorted(kayitlar, key=anahtar)


def bolumler(kayitlar: list[dict], bugun: date) -> dict[str, list[dict]]:
    sonuc: dict[str, list[dict]] = {"acik": [], "beklenen": [], "surekli": [], "yurt_disi": [], "kapandi": []}
    for k in kayitlar:
        if kapandi_mi(k, bugun):
            sonuc["kapandi"].append(k)
        elif k["bolge"] == "yurt-disi":
            sonuc["yurt_disi"].append(k)
        elif k["tarih_durumu"] == "kesin":
            sonuc["acik"].append(k)
        elif k["tarih_durumu"] in ("beklenen", "duyurulmadi"):
            sonuc["beklenen"].append(k)
        else:
            sonuc["surekli"].append(k)
    for ad in sonuc:
        sonuc[ad] = _sirala(sonuc[ad])
    sonuc["kapandi"].reverse()  # en son kapanan en üstte
    return sonuc


def liste_markdown(kayitlar: list[dict], bugun: date) -> str:
    b = bolumler(kayitlar, bugun)
    son_guncelleme = max((k["guncelleme"] for k in kayitlar), default="—")
    acik_degil = [k for k in kayitlar if not kapandi_mi(k, bugun)]
    acik_sayi = sum(k["tarih_durumu"] in ("kesin", "surekli") for k in acik_degil)
    beklenen_sayi = len(acik_degil) - acik_sayi
    parcalar = [
        f"**{len(kayitlar)} program** · {acik_sayi} açık · {beklenen_sayi} beklenen · "
        f"son veri güncellemesi: {son_guncelleme}",
    ]

    def bolum(baslik: str, aciklama: str, liste: list[dict]) -> None:
        parcalar.append(f"## {baslik}\n\n{aciklama}\n\n" + (_tablo(liste) if liste else "_Şu an kayıt yok._"))

    bolum("🟢 Başvurusu açık", "Son başvuru tarihi kesin olan programlar, yaklaşan tarihe göre sıralı.", b["acik"])
    bolum("🕒 Beklenen", "Bu dönem için henüz duyurulmamış. Tarih varsa geçen yılın takviminden; "
          "yoksa uydurulmaz. Yaklaşınca resmi sayfayı kontrol et.", b["beklenen"])
    bolum("♾️ Sürekli açık", "Belirli bir son tarihi olmayan, yıl boyu başvuru alan programlar.", b["surekli"])
    bolum("🌍 Yurt dışı ve Erasmus+", "Türkiye'den başvurulabilen yurt dışı programları.", b["yurt_disi"])
    kapali = _tablo(b["kapandi"]) if b["kapandi"] else "_Şu an kayıt yok._"
    parcalar.append(f"<details>\n<summary>🔒 Kapanmış ({len(b['kapandi'])})</summary>\n\n{kapali}\n\n</details>")
    return "\n\n".join(parcalar)


def readme_uret(sablon: str, kayitlar: list[dict], bugun: date) -> str:
    if BASLANGIC not in sablon or BITIS not in sablon:
        raise ValueError("Şablonda liste işaretleri yok")
    once, kalan = sablon.split(BASLANGIC, 1)
    _, sonra = kalan.split(BITIS, 1)
    return f"{once}{BASLANGIC}\n{liste_markdown(kayitlar, bugun)}\n{BITIS}{sonra}"


def readme_yaz(sablon_yolu: Path, cikti_yolu: Path, kayitlar: list[dict], bugun: date) -> bool:
    """README'yi yazar; içerik değiştiyse True döner."""
    yeni = readme_uret(sablon_yolu.read_text(encoding="utf-8"), kayitlar, bugun)
    eski = cikti_yolu.read_text(encoding="utf-8") if cikti_yolu.exists() else None
    if yeni == eski:
        return False
    cikti_yolu.write_text(yeni, encoding="utf-8")
    return True
