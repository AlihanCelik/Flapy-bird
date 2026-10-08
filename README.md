# 🎮 Flappy Bird - Python & Pygame Eğitim Projesi

Bu proje, Python programlama dilini ve **Pygame** kütüphanesini kullanarak **2D oyun geliştirme** mantığını öğretmek amacıyla tasarlanmış açık ve anlaşılır bir **Flappy Bird** uyarlamasıdır.

Dış resim veya ses dosyalarına ihtiyaç duymadan (bağımsız ve tak-çalıştır biçimde) çalışır. Bütün görseller ve 8-bit retro ses efektleri Python kodları ile **dinamik (prosedürel)** olarak üretilir.

---

## 📸 Oyun Görselleri ve Özellikleri

- **Kanat Animasyonlu ve Eğilmeli Kuş:** Zıplarken yukarı bakan, düşerken aşağı süzülen animasyonlu kuş fiziği.
- **Parallax Kaydırmalı Arka Plan:** Gökyüzü gradyanı, süzülen bulutlar ve sürekli kayan çizgili zemin.
- **Detaylı Boru Kapakları ve Gölgelendirme:** Vektörel boru grafikleri.
- **Efektler:** Zıplama parçacıkları (tüy/toz efekti), skor artışında büyüme animasyonu ve çarpışmada ekran sarsıntısı.
- **Prosedürel Sesler:** Matematiksel dalgalarla üretilmiş Zıplama, Skor ve Çarpma sesleri.
- **Rekor Takibi:** En yüksek skorun `highscore.txt` dosyasına otomatik kaydedilmesi.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Hazır Sanal Ortam (Virtual Environment) ile Çalıştırma

Projeye özel sanal ortam hazırlanmıştır. Terminalde proje dizinine gidip aşağıdaki komutu çalıştırabilirsiniz:

```bash
# Modüler mimaride çalıştırma:
./venv/bin/python main.py

# VEYA tek dosyalık eğitim sürümünde çalıştırma:
./venv/bin/python flappy_bird.py
```

### 2. Sıfırdan Kendi Ortamınızda Çalıştırma

Eğer kendi Python ortamınızda çalıştırmak isterseniz:

```bash
# Pygame Community Edition kütüphanesini yükleyin
pip install pygame-ce

# Oyunu başlatın
python main.py
```

---

## 🎓 Eğitim Dökümanı & Ders Konuları

Bu proje derslerde aşağıdaki konuları öğretmek için birebirdir:

### 1. Oyun Döngüsü (Game Loop)
Oyunlar bir sonsuz döngü içerisinde çalışır:
```
[ Olay İşleme (Events) ] ➔ [ Mantık Güncelleme (Update) ] ➔ [ Ekrana Çizim (Render) ] ➔ [ FPS Sınırlama (Clock.tick) ]
```
- `handle_events()`: Klavyeden veya fareden gelen zıplama ve kapatma isteklerini dinler.
- `update()`: Konumları, yerçekimini ve boru hareketlerini günceller.
- `render()`: Tüm nesneleri ekrana çizer ve `pygame.display.flip()` ile görüntüyü tazeler.

---

### 2. Nesne Yönelimli Programlama (OOP)

Oyun mantığı modüler sınıflara bölünmüştür:

| Sınıf | Dosya | Sorumluluğu |
| :--- | :--- | :--- |
| `Bird` | `sprites.py` | Kuşun konumu, dikey hızı, ivmesi, eğim açısı ve kanat çırpma animasyonu. |
| `Pipe` | `sprites.py` | Üst ve alt boru çiftinin hareketi, ekrandan çıkma tespiti ve çizimi. |
| `Ground` | `sprites.py` | Kayan zemin ve çim kaplaması. |
| `SoundManager` | `sound.py` | `struct` ve `math` modülleri ile 8-bit ses sentezleme. |
| `Game` | `game.py` | Oyun durumları (Başlangıç, Oynanış, Oyun Bitti), skor ve çarpışma kontrolü. |

---

### 3. Oyun Fiziği (Physics)

Kuşun hareketi ivmeli fizik denklemlerine dayanır:

1. **Yerçekimi (Gravity):** Her karede dikey hıza eklenir.
   $$\text{velocity\_y} = \text{velocity\_y} + \text{GRAVITY}$$
2. **Zıplama (Impulse):** Boşluk tuşuna basıldığında dikey hıza negatif (yukarı yönlü) ani ivme verilir.
   $$\text{velocity\_y} = \text{JUMP\_STRENGTH} \quad (-8.5)$$
3. **Konum Güncelleme:**
   $$\text{y} = \text{y} + \text{velocity\_y}$$

---

### 4. Çarpışma Tespiti (Collision Detection)

Çarpışmalar Pygame'in `pygame.Rect.colliderect()` metodu ile tespit edilir:
- Kuşun etrafındaki dikdörtgen alan (`Rect`), boruların dikdörtgen alanları ile kesiştiğinde çarpışma gerçekleşir.
- **Eğlenceli Oyun Deneyimi İpucu:** Kuşun kutusu `bird.rect.inflate(-6, -6)` ile 6 piksel küçültülmüştür. Bu sayede milimetrik teğet geçişlerde oyuncu haksız yere yanmaz!

---

## 📁 Dosya Yapısı

```text
flapy bird/
├── config.py       # Renkler, boyutlar ve fizik sabitleri
├── sound.py        # Prosedürel ses efekti üreticisi
├── sprites.py      # Kuş, Boru, Zemin, Bulut ve Parçacık sınıfları
├── game.py         # Oyun motoru, durum yönetimi ve arayüz
├── main.py         # Modüler projeyi başlatan giriş dosyası
├── flappy_bird.py  # Tüm kodların tek dosyada toplandığı alternatif eğitim scripti
└── highscore.txt   # Kaydedilen en yüksek skor
```

---

## 🚀 Öğrenciler İçin Geliştirme Ödevleri / Fikirleri

Öğrencilerin kodla pratik yapması için ekleyebilecekleri özellikler:

1. **Zorluk Seviyeleri:** Skor arttıkça boruların hızını (`PIPE_SPEED`) ve boru aralığını (`PIPE_GAP`) dinamik olarak değiştirmek.
2. **Madalya Sistemi:** Oyun bitti ekranında skora göre Bronz (5+), Gümüş (15+), Altın (30+) madalya rozeti çizmek.
3. **Gece / Gündüz Modu:** Belirli bir skora ulaşınca gökyüzü renklerini gece moduna dönüştürmek ve yıldızlar eklemek.
4. **Çift Oyunculu Mod (Local 2-Player):** İkinci bir kuş ekleyip biri `BOŞLUK`, diğeri `W` tuşu ile kontrol edilecek şekilde rekabetçi mod yapmak.
# Flapy-bird
# Flapy-bird
