# Katkı rehberi

## En kolay yol: issue formu
Kod bilmene gerek yok.
- [Program ekle](../../issues/new?template=yeni-program.yml)
- [Düzeltme bildir](../../issues/new?template=duzenle.yml)
- [Kapandı bildir](../../issues/new?template=kapandi.yml)

Bir moderatör kontrol edip `approved` etiketini koyunca GitHub Actions kaydı `data/programs.json`'a ekler, README'yi günceller ve issue'yu kapatır.

## Kurallar
1. **Resmi link şart.** Şirketin kendi kariyer sayfası ya da resmi başvuru platformu olmalı. Sosyal medya gönderisi veya haber sitesi kabul edilmez.
2. **Tahmin yok.** Not eşiği, İngilizce şartı veya tarih ilanda yazmıyorsa boş bırak.
3. **Tarih durumu doğru seçilmeli:**
   - `Kesin`: bu dönemin tarihi açıklandı.
   - `Beklenen`: geçen yılın tarihi biliniyor, bu yıl henüz açıklanmadı.
   - `Henüz duyurulmadı`: tarih bilinmiyor.
   - `Sürekli açık`: yıl boyu başvuru alınıyor.
4. Kayıtlar silinmez, kapanınca `aktif: false` yapılır. Böylece geçmiş yılların takvimi korunur.

## Doğrudan PR (geliştiriciler için)
```bash
pip install -r requirements.txt
# data/programs.json'u düzenle (README'yi elle düzenleme)
python main.py validate        # şema kontrolü
python main.py readme          # README'yi üret
python -m pytest tests -q
```
Yeni kayıt için `id` alanına bir UUID ver: `python -c "import uuid; print(uuid.uuid4())"`.

## Yerel kullanım: kişisel sıralama
`data/private/` klasörü git'e girmez. `data/profile.example.json` dosyasını `data/private/profile.json` olarak kopyala ve not ortalamanı, sınıfını, ağırlıklarını gir. Sonra `python main.py rank` komutunu çalıştır. Uygunluk filtresi ve TOPSIS ile kişisel bir başvuru sıralaması üretilir, sonuç `data/private/benim_siralamam.md` dosyasına yazılır. İstersen kendi kayıtlarını `data/private/programs_private.json` dosyasına ekleyebilirsin.

Pre-commit koruması için: `git config core.hooksPath .githooks`
