import socket
import ssl
import urllib.error

import main


def _hata(neden):
    def _ac(url, dogrula=True):
        raise urllib.error.URLError(neden)
    return _ac


def test_404_kirik(monkeypatch):
    monkeypatch.setattr(main, "_ac", lambda url, dogrula=True: 404)
    assert main.link_durumu("https://x")[0] == "kirik"


def test_403_supheli(monkeypatch):
    monkeypatch.setattr(main, "_ac", lambda url, dogrula=True: 403)
    assert main.link_durumu("https://x")[0] == "supheli"


def test_dns_kirik(monkeypatch):
    monkeypatch.setattr(main, "_ac", _hata(socket.gaierror(11001, "yok")))
    assert main.link_durumu("https://x") == ("kirik", "alan adı bulunamadı (DNS)")


def test_ssl_zinciri_eksik_ama_sayfa_var(monkeypatch):
    def _ac(url, dogrula=True):
        if dogrula:
            raise urllib.error.URLError(ssl.SSLCertVerificationError(1, "unable to get local issuer"))
        return 200
    monkeypatch.setattr(main, "_ac", _ac)
    seviye, neden = main.link_durumu("https://x")
    assert seviye == "supheli" and "SSL" in neden


def test_zaman_asimi_bir_kez_tekrar_denenir(monkeypatch):
    cagri = []

    def _ac(url, dogrula=True):
        cagri.append(url)
        if len(cagri) == 1:
            raise urllib.error.URLError(TimeoutError("timed out"))
        return 200
    monkeypatch.setattr(main, "_ac", _ac)
    assert main.link_durumu("https://x") is None and len(cagri) == 2


def test_rapor_bolumleri(kayit):
    sonuclar = [(kayit(program="A"), ("kirik", "HTTP 404 (sayfa yok)")),
                (kayit(program="B"), ("supheli", "HTTP 403")),
                (kayit(program="C"), None)]
    rapor = main.link_raporu(sonuclar)
    assert "## Kırık" in rapor and "## Şüpheli" in rapor
    assert rapor.index("– A") < rapor.index("## Şüpheli") < rapor.index("– B")
    assert "– C" not in rapor


def test_rapor_temiz(kayit):
    assert main.link_raporu([(kayit(), None)]) == "Tüm linkler açıldı."
