# Günlük araştırma görevi: talimat

Bu dosya, her gün çalışan Claude Code otomatik görevinin talimatıdır. Görev bu
depoda çalışır; mail atmaz. Bulduklarını `data/programs.json` ve
`data/linkedin.json` dosyalarına ekleyip tek bir PR açar. PR birleşince README
ve dashboard güncellenir.

Fikir, Melih Gürevin'in kişisel kariyer ajanından (gurevinmelih5-lang/kariyer-ajani)
alındı ve bu listenin kurallarına göre yeniden yazıldı.

## Kurallar (pazarlıksız)

1. **Uydurma yok.** Tarih, şart ya da link sayfada yoksa yazılmaz. Tarih yoksa
   `tarih_durumu: "duyurulmadi"`, şart yoksa alan boş kalır.
2. **Resmi link.** `programs.json`'a giren her kaydın `url`'i şirketin ya da
   kurumun kendi sayfası veya resmi başvuru platformu olmalı. LinkedIn, haber
   sitesi ya da ilan toplayıcı (Youthall, Kariyer.net vb.) burada yalnızca
   ipucudur; resmi sayfa bulunup açılarak doğrulanır.
3. **LinkedIn ayrı yere.** LinkedIn gönderisi ya da ilanı `data/linkedin.json`'a
   kart olarak girer. Gönderide tarih yazıyorsa `son_basvuru` doldurulur. Resmi
   sayfası da doğrulandıysa program ayrıca `programs.json`'a eklenir ve kart
   `program_id` ile bağlanır.
4. **Tekrar yok.** Eklemeden önce `programs.json` ve `linkedin.json`'da aynı
   kurum + program ya da aynı link var mı bak. Varsa yalnızca eksik bilgiyi
   güncelle (`guncelleme` tarihini bugüne çek).
5. **Kapsam.** Türkiye'deki öğrenciler ve yeni mezunlar: staj, uzun dönem staj,
   yeni mezun ve yönetici adayı programları, yarışma, hackathon, araştırma/burs,
   akademi/kamp, yurt dışı programları. Deneyim isteyen normal iş ilanları
   girmez.
6. **Her çalışmada sınır.** En fazla 25 yeni kayıt. Kalitesi şüpheli olanı
   eklemektense PR açıklamasında "elendi" diye nedeniyle yaz.

## Adımlar

1. Bugünün tarihini al: `TZ=Europe/Istanbul date +%F`.
2. `pip install -r requirements.txt`, sonra `python main.py validate`.
3. **Bakım:**
   - Açık "Duyuru izleyicisi" ve "Link kontrolü" issue'larındaki bulguları
     resmi sayfadan kontrol et; doğrulananları güncelle.
   - Son başvurusu geçen `kesin` kayıtlara dokunma; README bunları kendisi
     "Kapanmış"a taşır.
4. **Web araması** (Türkçe ve İngilizce, en az 15 sorgu). Kategoriler:
   - A) Yarışma ve hackathon: TEKNOFEST, TÜBİTAK 2209-A/2242, Coderspace,
     Techcareer, üniversite ve şirket hackathonları, vaka ve iş analitiği
     yarışmaları, ideathon ve girişimcilik yarışmaları, Devpost ve MLH'deki
     Türkiye'den katılınabilen online etkinlikler.
   - B) Staj ve yetenek programları: büyük şirketlerin ve bankaların staj,
     uzun dönem staj, yönetici adayı programları; Big4; savunma sanayi;
     Avrupa stajları (Erasmus+, IAESTE, AB kurumları). İpucu kaynakları:
     Youthall, Anbean, Toptalent, Kariyer.net, Coderspace.
   - C) YBS odağı (her çalışmada ayrıca ara): iş analistliği (business
     analyst), ERP/SAP stajları ve akademileri, veri analitiği ve BI, ürün
     yönetimi, dijital dönüşüm, BT danışmanlığı, SAP/Microsoft/Google/AWS'nin
     öğrencilere açık ücretsiz program ve akademileri. Bunlara `alan`
     olarak `ybs` ekle; veri işiyse `veri`, yazılımsa `yazilim` de ekle.
   - D) Tüm bölümlere açık programlar: burslar, gençlik programları, kamu stajları.
5. **LinkedIn** (zorunlu adım). LinkedIn'e giriş yapılmaz, sayfa kazınmaz:
   - Exa bağlıysa `web_search_exa` ile yalnızca `linkedin.com/posts` ve
     `linkedin.com/jobs/view` sonuçlarını, son 7 gün içinde ara (en az 6
     sorgu): "staj başvuruları açıldı", "yaz stajı 2027", "hackathon
     başvuru", "vaka yarışması", "yetenek programı", "business analyst
     intern", "SAP stajyer".
   - Fırsat paylaşan sayfaların son gönderilerine bak: Coderspace, Youthall,
     Anbean, Toptalent, Techcareer.net, Mühendislik Stajları.
   - Exa bağlı değilse bu adımı atla ve PR açıklamasında belirt.
6. **Doğrula ve yaz.** Her aday için resmi sayfayı aç. Uyanları şemaya göre
   ekle (`id` için `python -c "import uuid; print(uuid.uuid4())"`,
   `eklenme` ve `guncelleme` bugün). Sonra:
   `python main.py validate && python main.py readme && python -m pytest tests -q`.
   Hata varsa düzelt; düzeltemiyorsan o kaydı çıkar.
7. **PR aç.** Dal: `ajan/GG-AA-YYYY`. Değişiklik yoksa PR açma. PR açıklaması:
   - Sayılar: taranan sorgu sayısı, bulunan aday, eklenen program, eklenen
     LinkedIn kartı, güncellenen kayıt, elenen aday.
   - Eklenenler: kurum – program – son başvuru – resmi link.
   - Elenenler: kısa neden (resmi sayfa yok, tarih geçmiş, deneyim istiyor,
     tekrar…).
8. Son mesajında aynı sayıları tek satırda özetle.
