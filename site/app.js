// Staj takvimi: data.js (main.py site) içindeki window.STAJ verisini çizer.
// Kalan gün ve "kapandı" durumu tarayıcıda hesaplanır; sayfa her gün yeniden üretilmez.
(function () {
  "use strict";

  const VERI = window.STAJ || { programlar: [], linkedin: [], alanlar: {}, turler: {}, repo: "", ozel: false };
  const AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
  const AYLAR_UZUN = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  const GUN_MS = 86400000;
  const ACIL_GUN = 14;

  const bugun = (() => { const d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); })();
  const $ = (id) => document.getElementById(id);

  // ---- yardımcılar -------------------------------------------------------
  function el(etiket, ozellik, ...cocuklar) {
    const d = document.createElement(etiket);
    for (const [k, v] of Object.entries(ozellik || {})) {
      if (v == null || v === false) continue;
      if (k === "class") d.className = v;
      else if (k.startsWith("on")) d.addEventListener(k.slice(2), v);
      else d.setAttribute(k, v === true ? "" : v);
    }
    for (const c of cocuklar.flat(Infinity)) if (c != null && c !== false) d.append(c);
    return d;
  }
  const tarihOku = (s) => { const [y, a, g] = s.split("-").map(Number); return new Date(y, a - 1, g); };
  const tarihYaz = (d) => `${d.getDate()} ${AYLAR_UZUN[d.getMonth()]} ${d.getFullYear()}`;
  const kucult = (s) => (s || "").toLocaleLowerCase("tr");
  const guvenliUrl = (u) => (/^https:\/\//.test(u || "") ? u : null);
  const linkedinUrl = (u) => (/^https:\/\/([a-z]{2,3}\.|www\.)?linkedin\.com\//.test(u || "") ? u : null);
  const linkedinButon = (k) => {
    const u = linkedinUrl(k.linkedin);
    return u ? el("a", { class: "buton ikincil", href: u, target: "_blank", rel: "noopener noreferrer" }, "LinkedIn ↗") : null;
  };

  // ---- tarih durumu ------------------------------------------------------
  // Beklenen kayıtlarda tüm tarihler (açılış, son gün, dönem) aynı yıl kadar ileri kaydırılır.
  function hazirla(k) {
    let tarih = null, kaydir = 0;
    if (k.son_basvuru && (k.tarih_durumu === "kesin" || k.tarih_durumu === "beklenen")) {
      tarih = tarihOku(k.son_basvuru);
      if (k.tarih_durumu === "beklenen") {
        while (tarih < bugun) { tarih = new Date(tarih.getFullYear() + 1, tarih.getMonth(), tarih.getDate()); kaydir++; }
      }
    }
    const tasi = (s) => { if (!s) return null; const d = tarihOku(s); return new Date(d.getFullYear() + kaydir, d.getMonth(), d.getDate()); };
    const acilis = tasi(k.basvuru_acilis);
    const kapandi = k.aktif === false || (k.tarih_durumu === "kesin" && tarih < bugun);
    const gun = tarih ? Math.round((tarih - bugun) / GUN_MS) : null;
    let durum = k.tarih_durumu === "duyurulmadi" ? "bilinmiyor" : "beklenen";
    if (kapandi) durum = "kapandi";
    else if (k.tarih_durumu === "kesin") durum = acilis && acilis > bugun ? "yakinda" : "acik";
    else if (k.tarih_durumu === "surekli") durum = "acik";
    return { ...k, _tarih: tarih, _acilis: acilis, _donemBas: tasi(k.donem_baslangic), _donemBit: tasi(k.donem_bitis),
             _gun: gun, _acilisGun: acilis ? Math.round((acilis - bugun) / GUN_MS) : null, _durum: durum,
             _acil: durum === "acik" && gun != null && gun <= ACIL_GUN };
  }

  const programlar = VERI.programlar.map(hazirla);

  function siraAnahtari(k) {
    const grup = { acik: 0, yakinda: 1, beklenen: 2, bilinmiyor: 3, kapandi: 4 }[k._durum] + (k.tarih_durumu === "surekli" ? 2.5 : 0);
    const zaman = k._durum === "kapandi" ? -(k._tarih || 0)
      : k._durum === "yakinda" ? +k._acilis
      : (k._tarih ? +k._tarih : Infinity);
    return [grup, zaman];
  }
  function sirala(liste) {
    if (VERI.ozel) return liste.sort((a, b) => (b.skor ?? -1) - (a.skor ?? -1));
    return liste.sort((a, b) => {
      const [g1, z1] = siraAnahtari(a), [g2, z2] = siraAnahtari(b);
      return g1 - g2 || z1 - z2 || a.sirket.localeCompare(b.sirket, "tr");
    });
  }

  // ---- filtreler (URL'de saklanır, paylaşılabilir) ----------------------
  const DURUMLAR = [["", "Hepsi"], ["acik", "Şu an açık"], ["yakinda", "Yakında açılıyor"],
                    ["beklenen", "Tahmini tarihli"], ["bilinmiyor", "Tarih bekleniyor"]];
  let durumSecili = "";
  const filtreAlanlari = ["ara", "durum", "alan", "tur", "bolge", "kapali"];
  function filtreOku() {
    return {
      ara: $("ara").value.trim(), durum: durumSecili, alan: $("alan").value, tur: $("tur").value,
      bolge: $("bolge").value, kapali: $("kapali").checked,
    };
  }
  function durumlariCiz() {
    const aktif = programlar.filter((k) => k._durum !== "kapandi");
    $("durumlar").replaceChildren(...DURUMLAR.map(([ad, etiket]) => {
      const sayi = ad ? aktif.filter((k) => k._durum === ad).length : aktif.length;
      return el("button", {
        type: "button", role: "radio", class: `durum d-${ad || "hepsi"}`, "aria-checked": String(ad === durumSecili),
        disabled: ad && !sayi, onclick: () => { durumSecili = ad; durumlariCiz(); guncelle(); },
      }, etiket, el("span", { class: "sayi" }, String(sayi)));
    }));
  }
  function filtreUrldenYukle() {
    const p = new URLSearchParams(location.search);
    for (const ad of filtreAlanlari) {
      if (!p.has(ad)) continue;
      if (ad === "kapali") $("kapali").checked = p.get(ad) === "1";
      else if (ad === "durum") durumSecili = DURUMLAR.some(([d]) => d === p.get(ad)) ? p.get(ad) : "";
      else $(ad).value = p.get(ad);
    }
  }
  function filtreUrleYaz(f) {
    const p = new URLSearchParams();
    for (const ad of filtreAlanlari) {
      if (ad === "kapali") { if (f.kapali) p.set(ad, "1"); }
      else if (f[ad]) p.set(ad, f[ad]);
    }
    const q = p.toString();
    history.replaceState(null, "", (q ? `?${q}` : location.pathname) + location.hash);
  }
  function uyuyor(k, f) {
    if (!f.kapali && k._durum === "kapandi") return false;
    if (f.durum && k._durum !== f.durum) return false;
    if (f.alan && !k.alan.includes(f.alan) && !k.alan.includes("tum-bolumler")) return false;
    if (f.tur && k.tur !== f.tur) return false;
    if (f.bolge && k.bolge !== f.bolge) return false;
    if (f.ara) {
      const metin = kucult(`${k.sirket} ${k.program} ${(k.sehir || []).join(" ")}`);
      if (!kucult(f.ara).split(/\s+/).every((p) => metin.includes(p))) return false;
    }
    return true;
  }

  // ---- takvim dosyası (.ics) --------------------------------------------
  function icsIndir(k) {
    const ymd = (d) => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
    const kacis = (s) => s.replace(/([,;\\])/g, "\\$1").replace(/\n/g, "\\n");
    const tahmini = k.tarih_durumu === "beklenen" ? " (tahmini, geçen yılın tarihi)" : "";
    const etkinlik = (gun, baslik, alarm) => [
      "BEGIN:VEVENT",
      `UID:${k.id}-${ymd(gun)}@staj-takvimi`,
      `DTSTAMP:${ymd(new Date())}T000000Z`,
      `DTSTART;VALUE=DATE:${ymd(gun)}`,
      `DTEND;VALUE=DATE:${ymd(new Date(gun.getTime() + GUN_MS))}`,
      `SUMMARY:${kacis(`${baslik}: ${k.sirket} – ${k.program}${tahmini}`)}`,
      `DESCRIPTION:${kacis(`Resmi ilan: ${k.url}\nTarihi başvurmadan önce resmi sayfadan doğrula.`)}`,
      `URL:${k.url}`,
      ...(alarm ? ["BEGIN:VALARM", `TRIGGER:${alarm[0]}`, "ACTION:DISPLAY", `DESCRIPTION:${kacis(alarm[1])}`, "END:VALARM"] : []),
      "END:VEVENT",
    ];
    const satirlar = [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//staj-takvimi//TR", "CALSCALE:GREGORIAN",
      ...(k._acilis && k._acilis > bugun ? etkinlik(k._acilis, "Başvuru açılıyor", ["PT9H", `${k.sirket}: başvuru bugün açılıyor`]) : []),
      ...etkinlik(k._tarih, "Son başvuru", ["-P7D", `${k.sirket}: başvuruya 7 gün kaldı`]),
      "END:VCALENDAR",
    ];
    const blob = new Blob([satirlar.join("\r\n")], { type: "text/calendar;charset=utf-8" });
    const a = el("a", { href: URL.createObjectURL(blob), download: `${kucult(k.sirket).replace(/[^a-z0-9ğüşıöç]+/g, "-")}-son-basvuru.ics` });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---- çizim: liste ------------------------------------------------------
  function sayac(k) {
    if (k._durum === "kapandi") return el("div", { class: "sayac belirsiz" }, el("span", { class: "gun" }, "—"), el("span", { class: "birim" }, "kapandı"));
    if (k.tarih_durumu === "surekli") return el("div", { class: "sayac acik" }, el("span", { class: "gun" }, "∞"), el("span", { class: "birim" }, "sürekli açık"));
    if (k._gun == null) return el("div", { class: "sayac belirsiz" }, el("span", { class: "gun" }, "?"), el("span", { class: "birim" }, "duyurulmadı"));
    if (k._durum === "yakinda") return el("div", { class: "sayac yakinda" }, el("span", { class: "gun" }, String(k._acilisGun)), el("span", { class: "birim" }, "gün sonra açılıyor"));
    const sinif = k._durum === "beklenen" ? "belirsiz" : k._acil ? "acil" : "acik";
    const gunMetni = k._gun === 0 ? "bugün" : String(k._gun);
    const birim = k._gun === 0 ? "son gün" : k._durum === "beklenen" ? "gün (tahmini)" : "gün kaldı";
    return el("div", { class: `sayac ${sinif}` }, el("span", { class: "gun" }, (k._durum === "beklenen" ? "~" : "") + gunMetni), el("span", { class: "birim" }, birim));
  }

  function sartlar(k) {
    const p = [];
    if (k.sinif && k.sinif.length) p.push("Sınıf: " + k.sinif.map((s) => s === "yeni-mezun" ? "yeni mezun" : s === "yuksek-lisans" ? "YL" : s).join(", "));
    if (k.not_esigi != null) p.push(`Ort. ≥ ${Number(k.not_esigi).toFixed(2)}`);
    if (k.ingilizce) p.push(`İng.: ${k.ingilizce}`);
    return p;
  }

  const aralikYaz = (bas, bit) => {
    if (!bas) return tarihYaz(bit);
    const ayniYil = bas.getFullYear() === bit.getFullYear();
    return `${bas.getDate()} ${AYLAR_UZUN[bas.getMonth()]}${ayniYil ? "" : " " + bas.getFullYear()} – ${tarihYaz(bit)}`;
  };

  // Başvuru penceresi ve staj dönemi; beklenenlerde geçen yılın tarihleri olduğu açıkça yazılır
  function zamanSatirlari(k) {
    const satirlar = [];
    const gecen = k.tarih_durumu === "beklenen";
    const orijinal = (s) => (s ? tarihOku(s) : null);
    if (k._tarih) {
      const [bas, bit] = gecen ? [orijinal(k.basvuru_acilis), orijinal(k.son_basvuru)] : [k._acilis, k._tarih];
      satirlar.push([gecen ? "Başvuru (geçen yıl)" : "Başvuru", bas ? aralikYaz(bas, bit) : `son gün ${tarihYaz(bit)}`]);
    }
    if (k.donem_baslangic || k.donem_bitis) {
      const bas = orijinal(k.donem_baslangic), bit = orijinal(k.donem_bitis);
      satirlar.push([gecen ? "Dönem (geçen yıl)" : "Staj/program dönemi", bas && bit ? aralikYaz(bas, bit) : tarihYaz(bas || bit)]);
    }
    return satirlar;
  }

  function kayitCiz(k) {
    const zaman = zamanSatirlari(k);
    const url = guvenliUrl(k.url);
    return el("li", { class: `kayit${k._durum === "kapandi" ? " kapandi" : ""}`, id: `k-${k.id}` },
      sayac(k),
      el("div", { class: "bilgi" },
        el("h3", { class: "sirket" }, k.sirket),
        el("p", { class: "program" }, k.program),
        el("ul", { class: "etiketler" },
          k.bolge === "yurt-disi" ? el("li", { class: "dis" }, "🌍 Yurt dışı") : null,
          k.tur !== "yurt-disi" ? el("li", {}, VERI.turler[k.tur] || k.tur) : null,
          k.alan.map((a) => el("li", {}, VERI.alanlar[a] || a)),
          (k.sehir || []).length ? el("li", {}, k.sehir.join(", ")) : null,
          sartlar(k).map((s) => el("li", {}, s)),
        ),
        zaman.length ? el("dl", { class: "zaman" }, zaman.map(([d, t]) => [el("dt", {}, d), el("dd", {}, t)])) : null,
        k.notlar ? el("p", { class: "not" }, k.notlar) : null,
        k.guncelleme ? el("p", { class: "kontrol" }, `Bilgi kontrolü: ${tarihYaz(tarihOku(k.guncelleme))}`) : null,
      ),
      el("div", { class: "eylem" },
        VERI.ozel && k.skor != null ? el("span", { class: "skor", title: "TOPSIS skoru" }, `skor ${k.skor.toFixed(1)}`) : null,
        url ? el("a", { class: "buton", href: url, target: "_blank", rel: "noopener noreferrer" }, "Resmi ilan ↗") : null,
        linkedinButon(k),
        k._tarih && k._durum !== "kapandi"
          ? el("button", { class: "buton ikincil", type: "button", onclick: () => icsIndir(k),
                           title: k._durum === "yakinda" ? "Açılış ve son gün takvimine eklenir" : "Son gün takvimine eklenir" }, "Takvime ekle")
          : null,
      ),
    );
  }

  function listeCiz(liste) {
    const ol = $("liste");
    ol.replaceChildren();
    $("sonuc-sayisi").textContent = `${liste.length} program gösteriliyor`;
    if (!liste.length) {
      ol.append(el("li", { class: "bos" },
        el("p", {}, "Bu filtrelere uyan program yok."),
        el("button", { class: "buton ikincil", type: "button", onclick: filtreleriTemizle }, "Filtreleri temizle")));
      return;
    }
    ol.append(...liste.map(kayitCiz));
  }

  // ---- çizim: 12 aylık şerit --------------------------------------------
  function seritCiz(liste) {
    const serit = $("serit");
    serit.replaceChildren();
    const bas = new Date(bugun.getFullYear(), bugun.getMonth(), 1);
    const son = new Date(bas.getFullYear(), bas.getMonth() + 12, 1);
    const oran = (d) => (d - bas) / (son - bas);

    for (let i = 0; i < 12; i++) {
      const ay = new Date(bas.getFullYear(), bas.getMonth() + i, 1);
      serit.append(el("div", { class: "ay", "aria-hidden": "true" }, AYLAR[ay.getMonth()],
        (i === 0 || ay.getMonth() === 0) ? el("span", { class: "yil" }, String(ay.getFullYear())) : null));
    }
    serit.append(el("div", { class: "bugun", style: `left:${(oran(bugun) * 100).toFixed(2)}%`, "aria-hidden": "true" }));

    const noktalar = liste.filter((k) => k._tarih && k._durum !== "kapandi" && k._tarih < son)
      .sort((a, b) => a._tarih - b._tarih);
    // Her nokta yanında şirket adıyla çizilir; etiketler çakışırsa bir alt satıra iner.
    const genislik = serit.clientWidth || 1000;
    const satirSonu = [];  // her satırda son etiketin bittiği x (px)
    const SATIR = 26, UST = 50;
    for (const k of noktalar) {
      const xPx = oran(k._tarih) * genislik;
      const sagda = xPx < genislik * 0.78;
      const etiketPx = Math.min(k.sirket.length * 7.2 + 30, 170);
      // Başvuru penceresi biliniyorsa açılıştan son güne bir çubuk çizilir
      const pencereBas = k._acilis ? Math.max(0, oran(k._acilis)) : null;
      const pencerePx = pencereBas != null ? pencereBas * genislik : xPx;
      const [bas, bit] = sagda ? [Math.min(pencerePx, xPx) - 8, xPx + etiketPx] : [Math.min(pencerePx, xPx - etiketPx), xPx + 8];
      let satir = satirSonu.findIndex((s) => s < bas);
      if (satir === -1) { satir = satirSonu.length; satirSonu.push(0); }
      satirSonu[satir] = bit + 6;
      const pencereMetni = k._acilis ? `başvuru ${aralikYaz(k._acilis, k._tarih)}` : `son gün ${tarihYaz(k._tarih)}`;
      const etiket = `${k.sirket} – ${k.program}: ${pencereMetni}${k.tarih_durumu === "beklenen" ? " (tahmini)" : ""}`;
      if (pencereBas != null && pencereBas < oran(k._tarih)) {
        serit.append(el("div", {
          class: `pencere${k.tarih_durumu === "beklenen" ? " beklenen" : ""}${k._durum === "acik" ? " acik" : ""}`,
          style: `left:${(pencereBas * 100).toFixed(2)}%;width:${((oran(k._tarih) - pencereBas) * 100).toFixed(2)}%;top:${UST + satir * SATIR}px`,
          "aria-hidden": "true",
        }));
      }
      serit.append(el("button", {
        type: "button", role: "listitem",
        class: `isaret${sagda ? "" : " solda"}${k.tarih_durumu === "beklenen" ? " beklenen" : ""}${k._acil ? " acil" : ""}`,
        style: `left:${(oran(k._tarih) * 100).toFixed(2)}%;top:${UST + satir * SATIR}px`,
        "aria-label": etiket, title: etiket,
        onclick: (e) => noktaSec(k, etiket, e.currentTarget),
        onmouseenter: () => { $("serit-not").textContent = etiket; },
      }, el("span", { class: "nokta", "aria-hidden": "true" }), el("span", { class: "ad" }, k.sirket)));
    }
    serit.style.minHeight = `${Math.max(132, UST + satirSonu.length * SATIR + 28)}px`;
    $("serit-not").textContent = noktalar.length
      ? "Bir noktaya tıkla, program listede açılsın."
      : "Bu filtrelerde önümüzdeki 12 ay için tarihi bilinen program yok.";
  }

  function noktaSec(k, etiket, dugme) {
    document.querySelectorAll(".isaret.secili, .kayit.vurgu").forEach((d) => d.classList.remove("secili", "vurgu"));
    dugme.classList.add("secili");
    $("serit-not").textContent = etiket;
    const kart = $(`k-${k.id}`);
    if (kart) {
      kart.classList.add("vurgu");
      kart.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
    }
  }

  // ---- LinkedIn'den ------------------------------------------------------
  // data/linkedin.json: LinkedIn gönderisi/ilanı bağlantıları. Son başvurusu geçen ya da
  // (son başvurusu yazmıyorsa) 45 günden eski gönderi gösterilmez.
  const AKIS_OMUR_GUN = 45;
  const AKIS_ILK = 6;
  const akis = (VERI.linkedin || [])
    .map((g) => {
      const son = g.son_basvuru ? tarihOku(g.son_basvuru) : null;
      const paylasim = tarihOku(g.paylasim || g.eklenme);
      return { ...g, _son: son, _paylasim: paylasim, _gun: son ? Math.round((son - bugun) / GUN_MS) : null };
    })
    .filter((g) => linkedinUrl(g.url) && (g._son ? g._son >= bugun : (bugun - g._paylasim) / GUN_MS <= AKIS_OMUR_GUN))
    .sort((a, b) => (a._son && b._son ? a._son - b._son : a._son ? -1 : b._son ? 1 : b._paylasim - a._paylasim));
  let akisTumu = false;

  // Her zaman çalışan kısayollar: LinkedIn'in kendi aramasını Türkiye + son bir hafta filtresiyle açar.
  // İş ilanı aramaları girişsiz de açılır; gönderi (duyuru) aramaları LinkedIn hesabı ister.
  const LI_IS = "https://www.linkedin.com/jobs/search/?location=T%C3%BCrkiye&f_TPR=r604800&keywords=";
  const LI_GONDERI = "https://www.linkedin.com/search/results/content/?sortBy=%22date_posted%22&keywords=";
  const KISAYOLLAR = [
    ["Staj ilanları", LI_IS + "staj&f_E=1"],
    ["Internship ilanları", LI_IS + "intern&f_E=1"],
    ["Yeni mezun ilanları", LI_IS + "yeni%20mezun&f_E=2"],
    ["Staj duyuruları", LI_GONDERI + "staj%20ba%C5%9Fvurular%C4%B1%20a%C3%A7%C4%B1ld%C4%B1"],
    ["Hackathon duyuruları", LI_GONDERI + "hackathon%20ba%C5%9Fvuru"],
    ["Yarışma duyuruları", LI_GONDERI + "yar%C4%B1%C5%9Fma%20ba%C5%9Fvuru%20%C3%B6%C4%9Frenci"],
  ];

  function akisKart(g) {
    const program = g.program_id ? programlar.find((k) => k.id === g.program_id) : null;
    const zaman = g._son
      ? (g._gun === 0 ? "Son gün bugün" : `Son gün ${tarihYaz(g._son)} · ${g._gun} gün`)
      : `Paylaşıldı: ${tarihYaz(g._paylasim)}`;
    return el("li", { class: `li-kart${g._gun != null && g._gun <= ACIL_GUN ? " acil" : ""}` },
      el("p", { class: "li-kurum" }, g.kurum),
      el("a", { class: "li-baslik", href: g.url, target: "_blank", rel: "noopener noreferrer" }, g.baslik),
      el("ul", { class: "etiketler" },
        el("li", {}, VERI.turler[g.tur] || g.tur),
        el("li", { class: "tarih" }, zaman)),
      g.notlar ? el("p", { class: "not" }, g.notlar) : null,
      el("div", { class: "li-eylem" },
        el("a", { class: "buton", href: g.url, target: "_blank", rel: "noopener noreferrer" }, "LinkedIn'de aç ↗"),
        program ? el("a", { class: "li-resmi", href: `#k-${program.id}`,
                            onclick: () => setTimeout(() => $(`k-${program.id}`)?.classList.add("vurgu"), 0) },
                     "Listede gör (resmi ilan)") : null));
  }

  function akisCiz() {
    $("linkedin-kisayol").replaceChildren(el("span", { class: "etiket" }, "LinkedIn'de ara · son 7 gün"),
      ...KISAYOLLAR.map(([ad, url]) => el("a", { class: "buton ikincil", href: url, target: "_blank", rel: "noopener noreferrer" }, `${ad} ↗`)));
    if (!akis.length) {
      $("linkedin-ozet").textContent = "";
      $("linkedin-liste").replaceChildren();
      $("linkedin-tumu").hidden = true;
      return;
    }
    const kapaniyor = akis.filter((g) => g._gun != null && g._gun <= ACIL_GUN).length;
    $("linkedin-ozet").textContent = `${akis.length} gönderi` + (kapaniyor ? ` · ${kapaniyor} tanesi ${ACIL_GUN} gün içinde kapanıyor` : "");
    const gosterilen = akisTumu ? akis : akis.slice(0, AKIS_ILK);
    $("linkedin-liste").replaceChildren(...gosterilen.map(akisKart));
    const dugme = $("linkedin-tumu");
    dugme.hidden = akis.length <= AKIS_ILK;
    dugme.textContent = akisTumu ? "Daha az göster" : `Tümünü göster (${akis.length})`;
  }

  // ---- özet --------------------------------------------------------------
  function ozetCiz() {
    const aktif = programlar.filter((k) => k._durum !== "kapandi");
    const say = (d) => aktif.filter((k) => k._durum === d).length;
    const kapaniyor = aktif.filter((k) => k._durum === "acik" && k._gun != null && k._gun <= 30).length;
    const ozet = $("ozet");
    ozet.replaceChildren(`${aktif.length} program · ${say("acik")} başvuruya açık · ${say("yakinda")} yakında açılıyor · ` +
      `${say("beklenen")} tahmini tarihli · ${say("bilinmiyor")} tarih bekleniyor`);
    if (kapaniyor) ozet.append(" · ", el("b", {}, `${kapaniyor} tanesi 30 gün içinde kapanıyor`));
    if (VERI.ozel) ozet.append(" · ", el("b", {}, "özel görünüm: TOPSIS sıralaması"));
    const son = VERI.programlar.reduce((m, k) => (k.guncelleme > m ? k.guncelleme : m), "");
    if (son) $("guncelleme").textContent = `Verinin son güncellemesi: ${tarihYaz(tarihOku(son))}`;
  }

  // ---- özel: bölüm sekmesi (yalnızca main.py site --ozel) ---------------
  // Başvuru takibi bu bilgisayardaki tarayıcıda (localStorage) tutulur; yedek için CSV indirilir.
  const TAKIP_ANAHTAR = "staj-takip-v1";
  const TAKIP_DURUM = [["", "—"], ["ilgi", "İlgileniyorum"], ["hazirlik", "Hazırlanıyorum"], ["basvurdum", "Başvurdum"],
                       ["mulakat", "Test / mülakat"], ["teklif", "Teklif"], ["red", "Red"], ["vazgectim", "Vazgeçtim"]];
  const BASVURULMUS = new Set(["basvurdum", "mulakat", "teklif", "red"]);
  const KRITER = [["aciliyet", "Aciliyet", 1], ["hedef_uyum", "Hedef uyumu", 5], ["statu", "Statü", 5], ["efor", "Efor", 5]];

  function takipOku() {
    try { return JSON.parse(localStorage.getItem(TAKIP_ANAHTAR)) || {}; } catch { return {}; }
  }
  function takipYaz(id, alan, deger) {
    const t = takipOku();
    const kayit = { ...(t[id] || {}), [alan]: deger };
    if (alan === "durum" && BASVURULMUS.has(deger) && !kayit.tarih) kayit.tarih = new Date().toISOString().slice(0, 10);
    t[id] = kayit;
    try { localStorage.setItem(TAKIP_ANAHTAR, JSON.stringify(t)); } catch { /* özel pencere: kaydedilemez */ }
    return kayit;
  }

  // Bölümüm: ana bölüm (alanlar + türler), ilgi alanları ve tüm bölümlere açık programlar.
  const anaBolumden = (k, b) => k.ozel || b.turler.includes(k.tur) || k.alan.some((a) => a !== "tum-bolumler" && b.alanlar.includes(a));
  const bolumdenMi = (k, b) => anaBolumden(k, b) || k.alan.some((a) => b.alanlar.includes(a) || (b.ilgi_alanlari || []).includes(a));
  function odaklar(b) {
    return [
      ["", "Hepsi", () => true],
      ["ana", `${b.ad} (ana)`, (k) => anaBolumden(k, b)],
      ...(b.ilgi_alanlari || []).map((a) => [a, VERI.alanlar[a] || a, (k) => k.alan.includes(a)]),
      ["tum", "Tüm bölümlere açık", (k) => k.alan.includes("tum-bolumler")],
    ];
  }
  function arastirmaLinki(b, etiket) {
    const konu = etiket === "Hepsi" ? `${b.ad} ve ilgi alanlarım` : etiket;
    const govde = [
      `Konu: ${konu}`,
      "",
      "Ne arıyorum (staj, yarışma, yeni mezun, şirket adı, şehir…):",
      "",
      "",
      "Günlük araştırma görevi bu issue'yu okur, bulduklarını yalnızca bu özel depoya ekler ve sonucu buraya yazar.",
    ].join("\n");
    return `https://github.com/${b.ozel_repo}/issues/new?labels=arastirma&title=${encodeURIComponent(`Ek araştırma: ${konu}`)}` +
           `&body=${encodeURIComponent(govde)}`;
  }

  function kriterCubuk(k, [ad, etiket, ust], b) {
    const deger = k.kriterler[ad];
    const varsayilan = (ad === "statu" || ad === "efor") && !(b.puanlanan[ad] || []).includes(k.sirket);
    const oran = ad === "aciliyet" ? deger : (deger - 1) / (ust - 1);
    const yazi = ad === "aciliyet" ? deger.toFixed(2) : `${deger}/5`;
    return el("div", { class: `kriter${ad === "efor" ? " maliyet" : ""}`, title: varsayilan ? "profile.json'da puan yok, 3 varsayıldı" : null },
      el("span", { class: "k-ad" }, etiket, ad === "efor" ? " ↓" : ""),
      el("span", { class: "k-cubuk" }, el("i", { style: `width:${Math.max(4, oran * 100).toFixed(0)}%` })),
      el("span", { class: "k-deger" }, yazi, varsayilan ? el("sup", {}, "v") : null));
  }

  function bolumKart(k, sira, b) {
    const t = takipOku()[k.id] || {};
    const url = guvenliUrl(k.url);
    const zaman = zamanSatirlari(k);
    return el("li", { class: `bk${k.skor == null ? " elenen" : ""}${t.durum ? ` t-${t.durum}` : ""}` },
      el("div", { class: "bk-sira" }, k.skor == null ? "—" : `#${sira}`,
        el("span", { class: "bk-skor" }, k.skor == null ? "elendi" : `skor ${k.skor.toFixed(1)}`)),
      el("div", { class: "bk-govde" },
        el("h3", { class: "sirket" }, k.sirket, k.ozel ? el("span", { class: "rozet" }, "özel") : null),
        el("p", { class: "program" }, k.program),
        k.elenme ? el("p", { class: "elenme" }, `Elendi: ${k.elenme}`) : null,
        el("ul", { class: "etiketler" },
          el("li", {}, VERI.turler[k.tur] || k.tur),
          k.alan.map((a) => el("li", {}, VERI.alanlar[a] || a)),
          sartlar(k).map((s) => el("li", {}, s))),
        zaman.length ? el("dl", { class: "zaman" }, zaman.map(([d, z]) => [el("dt", {}, d), el("dd", {}, z)])) : null,
        k.notlar && !k.elenme ? el("p", { class: "not" }, k.notlar) : null,
        k.kriterler ? el("div", { class: "kriterler" }, KRITER.map((kr) => kriterCubuk(k, kr, b))) : null),
      el("div", { class: "bk-takip" },
        sayac(k),
        el("label", {}, el("span", { class: "etiket" }, "Takip"),
          el("select", { onchange: (e) => { takipYaz(k.id, "durum", e.target.value); bolumCiz(); } },
            TAKIP_DURUM.map(([d, ad]) => el("option", { value: d, selected: (t.durum || "") === d }, ad)))),
        t.tarih ? el("span", { class: "kucuk" }, `başvuru: ${t.tarih}`) : null,
        el("textarea", { rows: "2", placeholder: "Not: kime yazdım, hangi belge eksik…", "aria-label": `${k.sirket} notu`,
                         onchange: (e) => takipYaz(k.id, "not", e.target.value) }, t.not || ""),
        url ? el("a", { class: "buton", href: url, target: "_blank", rel: "noopener noreferrer" }, "Resmi ilan ↗") : null,
        linkedinButon(k)));
  }

  function takipCsv(liste) {
    const t = takipOku();
    const hucre = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const satirlar = [["sirket", "program", "skor", "takip", "basvuru_tarihi", "not", "url"].join(",")];
    for (const k of liste) {
      const x = t[k.id] || {};
      const durum = (TAKIP_DURUM.find(([d]) => d === (x.durum || "")) || ["", ""])[1];
      satirlar.push([k.sirket, k.program, k.skor?.toFixed(1), durum, x.tarih, x.not, k.url].map(hucre).join(","));
    }
    const blob = new Blob(["﻿" + satirlar.join("\r\n")], { type: "text/csv;charset=utf-8" });
    const a = el("a", { href: URL.createObjectURL(blob), download: "applications.csv" });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  let odak = "";
  function bolumCiz() {
    const b = VERI.bolum;
    const hepsi = programlar.filter((k) => k._durum !== "kapandi" && bolumdenMi(k, b));
    const secenekler = odaklar(b);
    const [, odakEtiket, odakFiltre] = secenekler.find(([ad]) => ad === odak) || secenekler[0];
    const liste = hepsi
      .filter(odakFiltre)
      .sort((x, y) => (x.skor == null) - (y.skor == null) || (y.skor ?? 0) - (x.skor ?? 0));
    const takip = Object.values(takipOku());
    const say = (d) => takip.filter((x) => x.durum === d).length;
    const basvuru = takip.filter((x) => BASVURULMUS.has(x.durum)).length;
    const uygun = hepsi.filter((k) => k.skor != null).length;
    const toplamW = Object.values(b.agirliklar).reduce((a, x) => a + x, 0) || 1;
    const metrik = (deger, etiket, ...ek) => el("div", { class: "metrik" }, el("b", {}, String(deger)), el("span", {}, etiket), ...ek);
    let sira = 0;
    $("bolum").replaceChildren(
      el("div", { class: "bolum-baslik" },
        el("h2", {}, `Bölümüm: ${b.ad}`),
        el("p", { class: "lejant" }, "Uygunluk (ortalama, sınıf, İngilizce) skordan önce kontrol edilir; şartı tutmayanlar en altta.")),
      el("div", { class: "metrikler" },
        metrik(uygun, "uygun program"),
        metrik(hepsi.length - uygun, "şartı tutmuyor"),
        metrik(`${basvuru}/${b.hedef_basvuru}`, "başvuru hedefi",
          el("span", { class: "ilerleme", role: "progressbar", "aria-label": "Başvuru hedefi",
                       "aria-valuemin": "0", "aria-valuemax": String(b.hedef_basvuru), "aria-valuenow": String(basvuru) },
            el("i", { style: `width:${Math.min(100, basvuru / b.hedef_basvuru * 100).toFixed(0)}%` }))),
        metrik(say("mulakat"), "test / mülakat"),
        metrik(say("teklif"), "teklif")),
      el("p", { class: "agirliklar" }, el("span", { class: "etiket" }, "Ağırlıklar"),
        KRITER.map(([ad, etiket]) => el("span", {}, `${etiket} %${Math.round((b.agirliklar[ad] || 0) / toplamW * 100)}`)),
        el("span", { class: "soluk" }, "v: puan verilmemiş, 3 varsayıldı · efor ↓: az olan iyi")),
      el("div", { class: "durumlar", role: "radiogroup", "aria-label": "İlgi alanına göre daralt" },
        secenekler.map(([ad, etiket, f]) => el("button", {
          class: "durum", type: "button", role: "radio", "aria-checked": String(ad === odak),
          onclick: () => { odak = ad; bolumCiz(); } }, etiket, " ", el("span", { class: "sayi" }, String(hepsi.filter(f).length))))),
      el("div", { class: "bolum-arac" },
        el("span", { class: "kucuk" }, `${liste.length} program · ${odakEtiket}`),
        el("span", { class: "bolum-dugmeler" },
          b.ozel_repo ? el("a", { class: "buton ikincil", href: arastirmaLinki(b, odakEtiket), target: "_blank", rel: "noopener noreferrer",
                                   title: "Özel depoda bir issue açar; günlük görev bu konuyu ayrıca araştırır" },
                           `Ek araştırma iste: ${odakEtiket === "Hepsi" ? b.ad : odakEtiket} ↗`) : null,
          el("button", { class: "buton ikincil", type: "button", onclick: () => takipCsv(liste) }, "Takibi CSV indir"))),
      el("ol", { class: "bolum-liste" }, liste.map((k) => bolumKart(k, k.skor == null ? 0 : ++sira, b))));
  }

  function sekmeSec(ad) {
    const bolum = ad === "bolum";
    $("genel").hidden = bolum; $("bolum").hidden = !bolum;
    $("sekme-genel").setAttribute("aria-selected", String(!bolum));
    $("sekme-bolum").setAttribute("aria-selected", String(bolum));
    history.replaceState(null, "", location.pathname + location.search + (bolum ? "#bolum" : ""));
    if (bolum) bolumCiz(); else guncelle();
  }

  // ---- akış --------------------------------------------------------------
  function guncelle() {
    const f = filtreOku();
    filtreUrleYaz(f);
    const liste = sirala(programlar.filter((k) => uyuyor(k, f)));
    seritCiz(liste);
    listeCiz(liste);
  }
  function filtreleriTemizle() {
    $("ara").value = ""; $("alan").value = ""; $("tur").value = ""; $("bolge").value = ""; $("kapali").checked = false;
    durumSecili = ""; durumlariCiz();
    guncelle();
  }

  function secenekleriDoldur() {
    const kullanilan = (alan) => new Set(programlar.flatMap((k) => [].concat(k[alan])));
    const alanlar = kullanilan("alan"); alanlar.delete("tum-bolumler");
    for (const [ad, etiket] of Object.entries(VERI.alanlar)) if (alanlar.has(ad)) $("alan").append(el("option", { value: ad }, etiket));
    const turler = kullanilan("tur");
    for (const [ad, etiket] of Object.entries(VERI.turler)) if (turler.has(ad)) $("tur").append(el("option", { value: ad }, etiket));
  }

  if (VERI.repo) $("katki").href = `https://github.com/${VERI.repo}/issues/new?template=yeni-program.yml`;
  secenekleriDoldur();
  filtreUrldenYukle();
  durumlariCiz();
  ozetCiz();
  akisCiz();
  $("linkedin-tumu").addEventListener("click", () => { akisTumu = !akisTumu; akisCiz(); });
  let zamanlayici;
  $("ara").addEventListener("input", () => { clearTimeout(zamanlayici); zamanlayici = setTimeout(guncelle, 120); });
  for (const id of ["alan", "tur", "bolge", "kapali"]) $(id).addEventListener("change", guncelle);
  if (VERI.ozel && VERI.bolum) {
    $("sekmeler").hidden = false;
    $("sekme-bolum").textContent = `Bölümüm: ${VERI.bolum.ad}`;
    $("sekme-genel").addEventListener("click", () => sekmeSec("genel"));
    $("sekme-bolum").addEventListener("click", () => sekmeSec("bolum"));
    sekmeSec(location.hash === "#bolum" ? "bolum" : "genel");
  } else {
    guncelle();
  }
})();
