"""Kişisel başvuru önceliklendirmesi: uygunluk filtresi + TOPSIS.

TOPSIS, scout-dss-football-analytics/src/dss_engine.py içindeki
calculate_topsis_score'dan uyarlandı; fark: maliyet yönlü kriter desteği
(efor gibi "az olsun" istenen kriterler) ve numpy'sız saf Python.
"""

from __future__ import annotations

import math
from datetime import date

INGILIZCE_SEVIYE = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6,
                    "Orta": 3, "İyi": 4, "İleri": 5, "Akıcı": 5}

# kriter → yön. Ağırlıklar profile.json'dan gelir.
KRITERLER = {"aciliyet": "fayda", "hedef_uyum": "fayda", "statu": "fayda", "efor": "maliyet"}


def topsis(matris: list[list[float]], agirliklar: list[float], yonler: list[str]) -> list[float]:
    """Her alternatif için 0–100 arası yakınlık katsayısı döndürür."""
    if not matris:
        return []
    n = len(agirliklar)
    toplam = sum(agirliklar)
    w = [a / toplam for a in agirliklar] if toplam > 0 else [1 / n] * n

    normlar = [math.sqrt(sum(satir[j] ** 2 for satir in matris)) or 1.0 for j in range(n)]
    v = [[satir[j] / normlar[j] * w[j] for j in range(n)] for satir in matris]

    sutunlar = list(zip(*v))
    ideal = [max(s) if yon == "fayda" else min(s) for s, yon in zip(sutunlar, yonler)]
    anti = [min(s) if yon == "fayda" else max(s) for s, yon in zip(sutunlar, yonler)]

    sonuc = []
    for satir in v:
        s_arti = math.sqrt(sum((x - i) ** 2 for x, i in zip(satir, ideal)))
        s_eksi = math.sqrt(sum((x - a) ** 2 for x, a in zip(satir, anti)))
        payda = s_arti + s_eksi
        sonuc.append(round(s_eksi / payda * 100, 2) if payda else 0.0)
    return sonuc


def sonraki_tarih(k: dict, bugun: date) -> date | None:
    """Kesin tarihi aynen; beklenen tarihi bir sonraki yıla taşıyarak döndürür."""
    if not k.get("son_basvuru"):
        return None
    d = date.fromisoformat(k["son_basvuru"])
    if k["tarih_durumu"] == "beklenen":
        while d < bugun:
            d = d.replace(year=d.year + 1)
    return d


def uygunluk(k: dict, profil: dict, bugun: date) -> str | None:
    """Uygun değilse nedenini, uygunsa None döndürür."""
    if not k.get("aktif", True):
        return "pasif"
    if k["tarih_durumu"] == "kesin" and date.fromisoformat(k["son_basvuru"]) < bugun:
        return "son başvuru geçti"
    esik = k.get("not_esigi")
    if esik is not None and profil["not_ortalamasi"] < esik:
        return f"not eşiği {esik:.2f} > {profil['not_ortalamasi']:.2f}"
    if k.get("sinif") and not set(k["sinif"]) & set(profil["basvurabilecegi_siniflar"]):
        return f"sınıf şartı {k['sinif']}"
    ist = INGILIZCE_SEVIYE.get(k.get("ingilizce") or "")
    if ist and INGILIZCE_SEVIYE.get(profil["ingilizce"], 0) < ist:
        return f"İngilizce şartı ({k['ingilizce']})"
    return None


def kriter_degerleri(k: dict, profil: dict, bugun: date) -> dict[str, float]:
    tarih = sonraki_tarih(k, bugun)
    if k["tarih_durumu"] == "surekli":
        gun = profil.get("surekli_program_gun", 180)
    elif tarih is None:
        gun = profil.get("bilinmeyen_tarih_gun", 120)
    else:
        gun = (tarih - bugun).days
    return {
        # Yaklaşan son tarih öne çıksın: 0 gün → 1.0, 30 gün → 0.5, 90 gün → 0.25
        "aciliyet": 1 / (1 + max(gun, 0) / 30),
        "hedef_uyum": profil["tur_tercihi"].get(k["tur"], 1),
        "statu": profil.get("statu_puani", {}).get(k["sirket"], 3),
        "efor": profil.get("efor_puani", {}).get(k["sirket"], 3),
    }


def sirala(kayitlar: list[dict], profil: dict, bugun: date) -> tuple[list[dict], list[tuple[dict, str]]]:
    """(sıralı uygun kayıtlar, [(uygun olmayan kayıt, neden)]) döndürür."""
    uygun, elenen = [], []
    for k in kayitlar:
        neden = uygunluk(k, profil, bugun)
        (elenen.append((k, neden)) if neden else uygun.append(k))

    adlar = list(KRITERLER)
    degerler = [kriter_degerleri(k, profil, bugun) for k in uygun]
    matris = [[d[a] for a in adlar] for d in degerler]
    agirlik = [profil["agirliklar"].get(a, 0) for a in adlar]
    skorlar = topsis(matris, agirlik, [KRITERLER[a] for a in adlar])

    sonuc = [dict(k, skor=s, kriterler=d) for k, s, d in zip(uygun, skorlar, degerler)]
    sonuc.sort(key=lambda k: (-k["skor"], k["sirket"].casefold()))
    return sonuc, elenen


def rapor_markdown(sirali: list[dict], elenen: list[tuple[dict, str]], bugun: date) -> str:
    satirlar = [f"# Başvuru sıralamam ({bugun.isoformat()})", "",
                "| # | Skor | Şirket | Program | Son başvuru | Aciliyet | Hedef | Statü | Efor |",
                "|---|---|---|---|---|---|---|---|---|"]
    for i, k in enumerate(sirali, 1):
        t = sonraki_tarih(k, bugun)
        tarih = {"surekli": "sürekli", "duyurulmadi": "duyurulmadı"}.get(k["tarih_durumu"]) or \
            f"{t.isoformat()}{' (tahmin)' if k['tarih_durumu'] == 'beklenen' else ''}"
        c = k["kriterler"]
        satirlar.append(f"| {i} | {k['skor']:.1f} | {k['sirket']} | {k['program']} | {tarih} | "
                        f"{c['aciliyet']:.2f} | {c['hedef_uyum']} | {c['statu']} | {c['efor']} |")
    if elenen:
        satirlar += ["", "## Elenenler", ""] + [f"- {k['sirket']} – {k['program']}: {n}" for k, n in elenen]
    return "\n".join(satirlar) + "\n"
