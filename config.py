"""
Flappy Bird - Yapılandırma ve Sabitler (Configuration & Constants)
Eğitim Modülü: Oyun sabitleri, renk tanımlamaları ve fizik parametreleri.
"""

# Ekran Boyutları (Screen Dimensions)
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Fizik Parametreleri (Physics Constants)
GRAVITY = 0.38            # Yerçekimi ivmesi (Hafifletilmiş dikey düşüş)
JUMP_STRENGTH = -7.5      # Zıplama gücü (Daha rahat ve yumuşak zıplama kontrolü)
MAX_FALL_SPEED = 9.0      # Maksimum düşüş hızı
BIRD_ROTATION_SPEED = 4.0 # Kuşun açısal dönüş hızı

# Boru Ayarları (Pipe Settings)
PIPE_SPEED = 2.4          # Boruların sola kayma hızı (piksel/kare)
PIPE_GAP = 165            # Üst ve alt boru arasındaki dikey boşluk (Daha rahat geçiş için genişletildi)
PIPE_SPAWN_TIME = 1500    # Yeni boru oluşturma sıklığı (milisaniye)
PIPE_WIDTH = 64           # Boru genişliği

# Zemin Ayarları (Ground Settings)
GROUND_HEIGHT = 80        # Zeminin yüksekliği

# Renk Tanımlamaları (RGB Tuple Formadı)
COLOR_SKY_TOP = (40, 150, 215)      # Gökyüzü üst gradyan rengi (Açık Mavi)
COLOR_SKY_BOTTOM = (160, 220, 240)  # Gökyüzü alt gradyan rengi
COLOR_GROUND_LIGHT = (220, 205, 125) # Kum/Toprak açık sarı
COLOR_GROUND_DARK = (195, 175, 95)  # Kum/Toprak koyu sarı
COLOR_GRASS = (85, 185, 60)         # Çim yeşili
COLOR_PIPE = (70, 180, 50)          # Boru ana yeşili
COLOR_PIPE_DARK = (45, 130, 30)     # Boru gölge yeşili
COLOR_PIPE_LIGHT = (130, 225, 100)  # Boru parlama yeşili
COLOR_BIRD_BODY = (255, 215, 0)     # Kuş gövdesi (Altın sarısı)
COLOR_BIRD_BEAK = (255, 120, 0)     # Kuş gagası (Turuncu)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_UI_TEXT = (255, 255, 255)
COLOR_UI_SHADOW = (40, 40, 40)
COLOR_BUTTON = (240, 130, 40)
COLOR_BUTTON_HOVER = (255, 150, 60)
