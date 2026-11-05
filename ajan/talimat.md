# Günlük araştırma görevi: talimat

Bu dosya, her gün çalışan Claude Code otomatik görevinin talimatıdır. Görev
iki depoyla çalışır; mail atmaz. Genel kümede bulduklarını PR olarak açar (PR
birleşince README ve dashboard güncellenir), özel kümede bulduklarını gizli
depoya doğrudan yazar.

İki ayrı küme var, birbirine karışmaz:

| Küme | Depo | Ne girer |
|---|---|---|
| Genel (herkese açık) | `Umutcagn/turkiye-staj-programlari` → `data/programs.json`, `data/linkedin.json` | Tüm bölümler, **Endüstri Mühendisliği hariç**. `validate` endüstri etiketli kaydı reddeder. |
| Özel (yalnızca sahibi) | `Umutcagn/staj-ozel` (gizli) → `programs_private.json` | Endüstri Mühendisliği, iş/operasyon, yönetici adayı, Big4 ve `profile.json` → `bolum.ilgi_alanlari`'ndaki alanlar (ör. veri, tasarım). Kayıtlarda `"ozel": true`. |

Özel kümeden hiçbir bilgi (kayıt, profil, issue içeriği) genel depoya, PR
açıklamasına ya da commit mesajına yazılmaz.

## Kurallar (pazarlıksız)

1. **Uydurma yok.** Tarih, şart ya da link sayfada yoksa yazılmaz. Tarih yoksa
   `tarih_durumu: "duyurulmadi"`, şart yoksa alan boş kalır.
2. **Resmi link.** `programs.json`'a giren her kaydın `url`'i şirketin ya da
   kurumun kendi sayfası veya resmi başvuru platformu olmalı. LinkedIn, haber
   sitesi ya da ilan toplayıcı (Youthall, Kariyer.net vb.) yalnızca ipucudur;
   resmi sayfa bulunup açılarak doğrulanır.
3. **LinkedIn ayrı yere.** LinkedIn gönderisi ya da ilanı `data/linkedin.json`'a
   kart olarak girer. Gönderide tarih yazıyorsa `son_basvuru` doldurulur. Resmi
   sayfası da doğrulandıysa program ayrıca `programs.json`'a eklenir ve kart
   `program_id` ile bağlanır.
4. **Tekrar yok.** Eklemeden önce `programs.json` ve `linkedin.json`'da aynı
   kurum + program ya da aynı link var mı bak. Varsa yalnızca eksik bilgiyi
   güncelle (`guncelleme` tarihini bugüne çek).
5. **Kapsam.** Türkiye'deki öğrenciler ve yeni mezunlar: staj,
   uzun dönem staj, yeni mezun ve yönetici adayı programları, yarışma,
   hackathon, araştırma/burs, akademi/kamp, gençlik ve yurt dışı programları.
   Deneyim isteyen normal iş ilanları girmez.
6. **Her çalışmada sınır.** En fazla 25 yeni kayıt. Kalitesi şüpheli olanı
   eklemektense PR açıklamasında "elendi" diye nedeniyle yaz.

## Adımlar

1. Bugünün tarihini al: `TZ=Europe/Istanbul date +%F`.
2. `pip install -r requirements.txt`, sonra `python main.py validate`.
3. **Bakım:** Her iki depodaki açık "Duyuru izleyicisi" ve "Link kontrolü"
   issue'larındaki bulguları resmi sayfadan kontrol et; doğrulananları güncelle.
4. **Ek araştırma istekleri:** `Umutcagn/staj-ozel`'deki açık, başlığı
   "Ek araştırma:" ile başlayan issue'ları oku. Her biri için konuya özel en az
   5 sorgu yap; bulunanlar özel kümeye girer. Issue'ya ne bulunduğunu (eklenen,
   elenen, nedeni) yorum olarak yaz; istek karşılandıysa issue'yu kapat.
5. **Web araması** (Türkçe ve İngilizce, en az 15 sorgu), dengeli dağıt:
   - Yarışma ve hackathon: TEKNOFEST, TÜBİTAK, Coderspace, Techcareer,
     üniversite ve şirket hackathonları, vaka yarışmaları, ideathon ve
     girişimcilik yarışmaları, Türkiye'den katılınabilen online etkinlikler.
   - Staj ve yetenek programları: büyük şirketler, bankalar, Big4, savunma
     sanayi, kamu kurumları; Avrupa stajları (Erasmus+, IAESTE, AB kurumları).
     İpucu kaynakları: Youthall, Anbean, Toptalent, Kariyer.net, Coderspace.
   - Burs, araştırma, gençlik programları, ücretsiz akademi ve kamplar.
6. **LinkedIn** (zorunlu adım). LinkedIn'e giriş yapılmaz, sayfa kazınmaz:
   - Exa bağlıysa `web_search_exa` ile yalnızca `linkedin.com/posts` ve
     `linkedin.com/jobs/view` sonuçlarını, son 7 gün içinde ara (en az 6
     sorgu): "staj başvuruları açıldı", "yaz stajı 2027", "hackathon
     başvuru", "vaka yarışması", "yetenek programı", "intern Türkiye".
   - Fırsat paylaşan sayfaların son gönderilerine bak: Coderspace, Youthall,
     Anbean, Toptalent, Techcareer.net, Mühendislik Stajları.
   - Exa bağlı değilse bu adımı atla ve PR açıklamasında belirt.
7. **Ayır, doğrula ve yaz.** Her aday için resmi sayfayı aç. Endüstri
   Mühendisliği'ne ya da özel profildeki alanlara yönelikse özel kümeye, değilse
   genel kümeye ekle (`id` için `python -c "import uuid; print(uuid.uuid4())"`,
   `eklenme` ve `guncelleme` bugün). Sonra:
   `python main.py validate && python main.py readme && python -m pytest tests -q`.
   Özel kayıtları doğrulamak için `staj-ozel`'i genel deponun `data/private/`
   klasörüne kopyala (bu klasör git'e girmez) ve aynı `validate`'i çalıştır.
   Hata varsa düzelt; düzeltemiyorsan o kaydı çıkar.
8. **Gönder.**
   - Özel küme: `staj-ozel`'in `main` dalına doğrudan commit ve push.
   - Genel küme: PR aç. Dal: `ajan/GG-AA-YYYY`. Değişiklik yoksa PR açma. PR açıklaması:
   - Sayılar: sorgu sayısı, bulunan aday, eklenen program, eklenen LinkedIn
     kartı, güncellenen kayıt, elenen aday.
   - Eklenenler: kurum – program – son başvuru – resmi link.
   - Elenenler: kısa neden (resmi sayfa yok, tarih geçmiş, deneyim istiyor,
     tekrar…).
9. Son mesajında iki kümenin sayılarını ayrı ayrı tek satırda özetle.
