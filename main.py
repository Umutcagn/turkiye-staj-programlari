"""Komut satırı: validate | readme | contribution | site | links | izle | rank."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

from src import schema
from src.readme import readme_yaz

KOK = Path(__file__).resolve().parent
PUBLIC = KOK / "data" / "programs.json"
PRIVATE_DIZIN = KOK / "data" / "private"
PRIVATE = PRIVATE_DIZIN / "programs_private.json"
SABLON = KOK / "templates" / "README.header.md"
README = KOK / "README.md"


def git_private_dosyalari() -> list[str]:
    """Git'e girmiş ya da stage'e alınmış private dosyaları döndürür."""
    komutlar = (["git", "ls-files", "data/private"], ["git", "diff", "--cached", "--name-only", "--", "data/private"])
    bulunan: set[str] = set()
    for komut in komutlar:
        try:
            cikti = subprocess.run(komut, cwd=KOK, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            continue  # git yoksa ya da repo değilse kontrol edilecek bir şey yok
        bulunan.update(satir for satir in cikti.splitlines() if satir.strip())
    return sorted(bulunan)


def komut_validate(_: argparse.Namespace) -> int:
    hatalar = schema.liste_hatalari(schema.yukle(PUBLIC), public=True)
    if PRIVATE.exists():
        hatalar += [f"[private] {h}" for h in schema.liste_hatalari(schema.yukle(PRIVATE), public=False)]
    sizinti = git_private_dosyalari()
    if sizinti:
        hatalar.append(f"PRIVATE DOSYA GIT'TE: {sizinti} — `git rm --cached` ile çıkar")
    for h in hatalar:
        print("HATA:", h)
    if not hatalar:
        print(f"Tamam: {len(schema.yukle(PUBLIC))} public kayıt geçerli.")
    return 1 if hatalar else 0


def komut_readme(args: argparse.Namespace) -> int:
    bugun = date.fromisoformat(args.bugun) if args.bugun else date.today()
    degisti = readme_yaz(SABLON, README, schema.yukle(PUBLIC), bugun)
    print("README güncellendi." if degisti else "README zaten güncel.")
    return 0


def komut_contribution(args: argparse.Namespace) -> int:
    """GitHub issue olay dosyasını işler; sonucu sonuc.md'ye yazar (Action yorum olarak atar)."""
    import json
    import os

    from src.contribution import isle

    olay = json.loads(Path(args.olay).read_text(encoding="utf-8"))
    issue = olay["issue"]
    etiketler = [e["name"] for e in issue.get("labels", [])]
    try:
        kayitlar, mesaj = isle(issue.get("body") or "", etiketler, schema.yukle(PUBLIC), date.today())
        schema.kaydet(PUBLIC, kayitlar)
        kod = 0
    except ValueError as e:
        mesaj, kod = f"❌ İşlenemedi, lütfen formu düzelt:\n\n{e}", 1
    (KOK / "sonuc.md").write_text(mesaj + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"basarili={'true' if kod == 0 else 'false'}\n")
    print(mesaj)
    return kod


TARAYICI_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def _ac(url: str, dogrula: bool = True) -> int:
    """URL'yi açar, HTTP durum kodunu döndürür; ağ hatalarını yukarı fırlatır."""
    import ssl
    import urllib.error
    import urllib.request

    istek = urllib.request.Request(url, headers={"User-Agent": TARAYICI_UA, "Accept": "text/html,*/*"})
    baglam = None if dogrula else ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(istek, timeout=20, context=baglam) as yanit:
            return yanit.status
    except urllib.error.HTTPError as e:
        return e.code


def _http_sonucu(kod: int) -> tuple[str, str] | None:
    if kod < 400:
        return None
    if kod in (404, 410):
        return "kirik", f"HTTP {kod} (sayfa yok)"
    return "supheli", f"HTTP {kod} (bot engeli ya da geçici sunucu hatası olabilir)"


def link_durumu(url: str) -> tuple[str, str] | None:
    """Link açılıyorsa None; açılmıyorsa (seviye, neden). Seviye 'kirik' ya da 'supheli'.

    Türk kamu sitelerinin çoğu ara sertifikayı göndermiyor: tarayıcı bunu tamamlar,
    Python tamamlamaz. Bu yüzden SSL hatasında doğrulamasız tekrar denenir ve sonuç
    'kirik' değil 'supheli' sayılır.
    """
    import socket
    import ssl
    import urllib.error

    for _ in range(2):
        try:
            return _http_sonucu(_ac(url))
        except urllib.error.URLError as e:
            neden = e.reason
            if isinstance(neden, ssl.SSLCertVerificationError):
                try:
                    sonuc = _http_sonucu(_ac(url, dogrula=False))
                except (urllib.error.URLError, OSError):
                    return "supheli", "SSL sertifika zinciri eksik, sayfa da açılmadı"
                return sonuc or ("supheli", "SSL sertifika zinciri eksik (tarayıcıda açılıyor)")
            if isinstance(neden, socket.gaierror):
                return "kirik", "alan adı bulunamadı (DNS)"
            if not isinstance(neden, TimeoutError):
                return "supheli", f"bağlantı hatası: {neden}"
        except TimeoutError:
            pass
        except OSError as e:
            return "supheli", f"bağlantı hatası: {type(e).__name__}"
    return "supheli", "iki kez zaman aşımı (yurt dışından erişim kapalı olabilir)"


def link_raporu(sonuclar: list[tuple[dict, tuple[str, str] | None]]) -> str:
    """(kayıt, link_durumu) çiftlerinden issue gövdesi üretir."""
    def satirlar(seviye: str) -> list[str]:
        return [f"- [ ] **{k['sirket']} – {k['program']}**: {d[1]} — {k['url']}"
                for k, d in sonuclar if d and d[0] == seviye]

    kirik, supheli = satirlar("kirik"), satirlar("supheli")
    if not kirik and not supheli:
        return "Tüm linkler açıldı."
    parcalar = [f"Otomatik kontrol: {len(sonuclar)} link denendi. Bu issue her hafta güncellenir."]
    if kirik:
        parcalar += ["", "## Kırık: düzeltilmeli", "", *kirik]
    if supheli:
        parcalar += ["", "## Şüpheli: tarayıcıdan kontrol et", "",
                     "Bot engeli, eksik SSL zinciri ya da yurt dışı erişim kısıtı yüzünden "
                     "çoğu tarayıcıda açılır.", "", *supheli]
    return "\n".join(parcalar)


def komut_links(args: argparse.Namespace) -> int:
    import os

    from concurrent.futures import ThreadPoolExecutor

    aktif = [k for k in schema.yukle(PUBLIC) if k.get("aktif", True)]
    with ThreadPoolExecutor(max_workers=8) as havuz:
        durumlar = list(havuz.map(lambda k: link_durumu(k["url"]), aktif))
    sonuclar = list(zip(aktif, durumlar))
    rapor = link_raporu(sonuclar)
    sorunlu = any(durumlar)
    if args.cikti:
        Path(args.cikti).write_text(rapor + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"sorunlu={'true' if sorunlu else 'false'}\n")
    print(rapor)
    return 0


def sayfa_getir(url: str) -> str:
    """Sayfanın HTML'ini döndürür; eksik SSL zincirinde doğrulamasız tekrar dener."""
    import ssl
    import urllib.error
    import urllib.request

    istek = urllib.request.Request(url, headers={"User-Agent": TARAYICI_UA, "Accept": "text/html,*/*"})
    try:
        yanit = urllib.request.urlopen(istek, timeout=25)
    except urllib.error.URLError as e:
        if not isinstance(e.reason, ssl.SSLCertVerificationError):
            raise
        yanit = urllib.request.urlopen(istek, timeout=25, context=ssl._create_unverified_context())
    with yanit:
        return yanit.read(3_000_000).decode(yanit.headers.get_content_charset() or "utf-8", errors="replace")


def komut_izle(args: argparse.Namespace) -> int:
    import json
    import os
    from concurrent.futures import ThreadPoolExecutor

    from src import izle

    bugun = date.fromisoformat(args.bugun) if args.bugun else date.today()
    ozel = args.ozel or args.sadece_ozel
    kayitlar = ([] if args.sadece_ozel else schema.yukle(PUBLIC)) + (schema.yukle(PRIVATE) if ozel else [])
    durum_yolu = (PRIVATE_DIZIN if ozel else KOK / "data") / "izleme.json"
    eski = json.loads(durum_yolu.read_text(encoding="utf-8")) if durum_yolu.exists() else {}

    izlenen = [k for k in kayitlar if izle.izlenecek_mi(k)]

    def oku(k: dict) -> tuple[list[str] | None, str | None]:
        try:
            return izle.sayfa_metni(sayfa_getir(k["url"])), None
        except Exception as e:  # ağ hatası tek kaydı düşürür, çalışmayı değil
            return None, f"{type(e).__name__}: {e}"[:120]

    with ThreadPoolExecutor(max_workers=8) as havuz:
        sonuclar = list(havuz.map(oku, izlenen))

    yeni_durum, bulgular, hatalar = {}, [], []
    for k, (satirlar, hata) in zip(izlenen, sonuclar):
        if hata:
            hatalar.append((k, hata))
            if k["id"] in eski:
                yeni_durum[k["id"]] = eski[k["id"]]  # okunamadıysa eski durumu koru
            continue
        yil = izle.hedef_yil(k, bugun)
        imza = izle.imza(satirlar, yil)
        if imza["kisa"]:
            hatalar.append((k, "sayfa metni çok kısa (JavaScript ile çiziliyor olabilir), elle kontrol et"))
        durum = izle.durum_guncelle(k, eski.get(k["id"]), imza, izle.ornek_satirlar(satirlar, yil), bugun)
        yeni_durum[k["id"]] = durum
        if durum.get("bulgu"):
            bulgular.append((k, durum["bulgu"]["seviye"], durum["bulgu"]["ornek"]))

    if yeni_durum != eski:
        durum_yolu.write_text(json.dumps(yeni_durum, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                              encoding="utf-8")
    metin = izle.rapor(bulgular, hatalar, len(izlenen))
    if args.cikti:
        Path(args.cikti).write_text(metin + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"bulgu={'true' if bulgular else 'false'}\n")
    print(metin)
    return 0


def komut_rank(args: argparse.Namespace) -> int:
    import json

    from src.score import rapor_markdown, sirala

    profil_yolu = PRIVATE_DIZIN / "profile.json"
    if not profil_yolu.exists():
        print(f"Profil yok: {profil_yolu} — data/profile.example.json'u kopyalayıp doldur.")
        return 1
    profil = json.loads(profil_yolu.read_text(encoding="utf-8"))
    bugun = date.fromisoformat(args.bugun) if args.bugun else date.today()
    sirali, elenen = sirala(schema.yukle(PUBLIC) + schema.yukle(PRIVATE), profil, bugun)
    cikti = PRIVATE_DIZIN / "benim_siralamam.md"
    cikti.write_text(rapor_markdown(sirali, elenen, bugun), encoding="utf-8")
    for i, k in enumerate(sirali[:10], 1):
        print(f"{i:2}. {k['skor']:5.1f}  {k['sirket']} – {k['program']}")
    print(f"\n{len(sirali)} uygun, {len(elenen)} elenen → {cikti.relative_to(KOK)}")
    return 0


def komut_site(args: argparse.Namespace) -> int:
    import json

    from src.site import bolum_ayari, derle, skorla

    bolum = None
    if args.ozel:
        profil_yolu = PRIVATE_DIZIN / "profile.json"
        if not profil_yolu.exists():
            print(f"Profil yok: {profil_yolu}")
            return 1
        profil = json.loads(profil_yolu.read_text(encoding="utf-8"))
        programlar = skorla(schema.yukle(PUBLIC) + schema.yukle(PRIVATE), profil, date.today())
        bolum = bolum_ayari(profil)
        hedef = PRIVATE_DIZIN / "site"
    else:
        programlar = schema.yukle(PUBLIC)
        hedef = KOK / "_site"
    sayfa = derle(KOK / "site", hedef, programlar, ozel=args.ozel, bolum=bolum)
    print(f"{len(programlar)} program → {sayfa}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe karakterler
    ap =argparse.ArgumentParser(description=__doc__)
    alt = ap.add_subparsers(dest="komut", required=True)
    alt.add_parser("validate", help="şema + private sızıntı kontrolü").set_defaults(f=komut_validate)
    p = alt.add_parser("readme", help="README.md'yi programs.json'dan üret")
    p.add_argument("--bugun", help="test için tarih (YYYY-AA-GG)")
    p.set_defaults(f=komut_readme)
    p = alt.add_parser("contribution", help="onaylanmış issue'yu programs.json'a işle (Action)")
    p.add_argument("olay", help="GITHUB_EVENT_PATH")
    p.set_defaults(f=komut_contribution)
    p = alt.add_parser("site", help="dashboard'u derle (_site/ ya da --ozel ile data/private/site/)")
    p.add_argument("--ozel", action="store_true", help="private kayıtlar + TOPSIS skorlarıyla yerel sürüm")
    p.set_defaults(f=komut_site)
    p = alt.add_parser("links", help="public linkleri kontrol et")
    p.add_argument("--cikti", help="raporun yazılacağı dosya")
    p.set_defaults(f=komut_links)
    p = alt.add_parser("izle", help="tarihi açıklanmamış programların resmi sayfalarında yeni duyuru ara")
    p.add_argument("--ozel", action="store_true", help="private kayıtları da izle (durum data/private/'a yazılır)")
    p.add_argument("--sadece-ozel", action="store_true", help="yalnızca private kayıtları izle (private repodaki Action)")
    p.add_argument("--cikti", help="raporun yazılacağı dosya")
    p.add_argument("--bugun", help="test için tarih (YYYY-AA-GG)")
    p.set_defaults(f=komut_izle)
    p = alt.add_parser("rank", help="kişisel başvuru sıralaması (yalnızca yerel, private)")
    p.add_argument("--bugun", help="test için tarih (YYYY-AA-GG)")
    p.set_defaults(f=komut_rank)
    args =ap.parse_args(argv)
    return args.f(args)


if __name__ == "__main__":
    sys.exit(main())
