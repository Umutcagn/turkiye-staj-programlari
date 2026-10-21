"""Komut satırı: validate | readme | contribution | links | rank."""

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


def link_durumu(url: str) -> str | None:
    """Link açılıyorsa None, açılmıyorsa kısa bir neden döndürür."""
    import urllib.error
    import urllib.request

    istek = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link-check)"})
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit:
            return None if yanit.status < 400 else f"HTTP {yanit.status}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return type(e).__name__


def komut_links(args: argparse.Namespace) -> int:
    import os

    from concurrent.futures import ThreadPoolExecutor

    aktif = [k for k in schema.yukle(PUBLIC) if k.get("aktif", True)]
    with ThreadPoolExecutor(max_workers=8) as havuz:
        nedenler = list(havuz.map(lambda k: link_durumu(k["url"]), aktif))
    sorunlu = [f"- [ ] **{k['sirket']} – {k['program']}**: {n} — {k['url']}"
               for k, n in zip(aktif, nedenler) if n]
    rapor = ("Aşağıdaki linkler otomatik kontrolde açılmadı. Bazı siteler botları engeller; "
             "tarayıcıdan kontrol edip gerekirse düzelt.\n\n" + "\n".join(sorunlu)) if sorunlu else "Tüm linkler açıldı."
    if args.cikti:
        Path(args.cikti).write_text(rapor + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"sorunlu={'true' if sorunlu else 'false'}\n")
    print(rapor)
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
    p = alt.add_parser("links", help="public linkleri kontrol et")
    p.add_argument("--cikti", help="raporun yazılacağı dosya")
    p.set_defaults(f=komut_links)
    p = alt.add_parser("rank", help="kişisel başvuru sıralaması (yalnızca yerel, private)")
    p.add_argument("--bugun", help="test için tarih (YYYY-AA-GG)")
    p.set_defaults(f=komut_rank)
    args =ap.parse_args(argv)
    return args.f(args)


if __name__ == "__main__":
    sys.exit(main())
