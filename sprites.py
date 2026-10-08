"""
Flappy Bird - Oyun Nesneleri (Sprites Module)
Eğitim Modülü: Nesne Yönelimli Programlama (OOP) ilkeleriyle Kuş, Boru, Zemin 
ve Parçacık sınıflarını içerir. Her sınıf kendi çizim, fizik ve durum güncellemelerinden sorumludur.
"""

import math
import random
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, JUMP_STRENGTH, MAX_FALL_SPEED,
    BIRD_ROTATION_SPEED, PIPE_SPEED, PIPE_GAP, PIPE_WIDTH, GROUND_HEIGHT,
    COLOR_BIRD_BODY, COLOR_BIRD_BEAK, COLOR_PIPE, COLOR_PIPE_DARK, COLOR_PIPE_LIGHT,
    COLOR_GROUND_LIGHT, COLOR_GROUND_DARK, COLOR_GRASS, COLOR_WHITE, COLOR_BLACK
)


class Bird:
    """
    Kuş Sınıfı (Bird Class)
    Kuşun konumunu, fiziksel hareketini (hız, yerçekimi), açısını, kanat animasyonunu 
    ve çizimini yönetir.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 34
        self.height = 24
        
        # Fizik Değişkenleri
        self.velocity_y = 0.0     # Dikey hız (piksel/kare)
        self.angle = 0.0          # Kuşun eğim açısı (derece)
        self.is_alive = True
        
        # Animasyon Değişkenleri
        self.wing_state = 0       # Kanat pozisyonu (0: Düz, 1: Yukarı, 2: Aşağı)
        self.anim_timer = 0
        
        # Çarpışma Kutusu (Hitbox)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def jump(self):
        """Kuşun yukarı zıplamasını sağlar (Dikey hızı eksi yönde değiştirir)."""
        if self.is_alive:
            self.velocity_y = JUMP_STRENGTH
            self.angle = 30.0  # Zıpladığında kafasını yukarı kaldırır

    def update(self):
        """Her karede kuşun fiziğini ve animasyonunu günceller."""
        # 1. Yerçekimi Uygulama: Hıza ivme ekle
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED

        # 2. Konum Güncelleme: Dikey hıza göre Y pozisyonunu değiştir
        self.y += self.velocity_y

        # 3. Açı (Eğim) Hesaplama: Düşerken aşağı doğru dön (Maksimum -90 derece)
        if self.velocity_y > 2.0:
            self.angle -= BIRD_ROTATION_SPEED * 1.5
            if self.angle < -80.0:
                self.angle = -80.0

        # 4. Çarpışma kutusunu güncelle
        self.rect.y = int(self.y)

        # 5. Kanat Animasyonu
        self.anim_timer += 1
        if self.anim_timer % 6 == 0:
            self.wing_state = (self.wing_state + 1) % 3

    def draw(self, surface):
        """Kuşu vektörel grafiklerle dinamik olarak ekrana çizer."""
        # Kuş yüzeyi (Dönüş efektleri için ayrı bir Surface)
        bird_surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        center_x = (self.width + 10) // 2
        center_y = (self.height + 10) // 2

        # a) Gövde (Oval)
        body_rect = pygame.Rect(5, 5, self.width, self.height)
        pygame.draw.ellipse(bird_surf, COLOR_BIRD_BODY, body_rect)
        pygame.draw.ellipse(bird_surf, COLOR_BLACK, body_rect, 2)  # Siyah dış hat

        # b) Göbek Parlaklığı
        belly_rect = pygame.Rect(8, 14, 18, 12)
        pygame.draw.ellipse(bird_surf, (255, 240, 150), belly_rect)

        # c) Göz ve Göz Bebeği
        eye_center = (self.width - 4, 11)
        pygame.draw.circle(bird_surf, COLOR_WHITE, eye_center, 6)
        pygame.draw.circle(bird_surf, COLOR_BLACK, eye_center, 6, 1)
        pygame.draw.circle(bird_surf, COLOR_BLACK, (eye_center[0] + 2, eye_center[1]), 3) # Göz bebeği
        pygame.draw.circle(bird_surf, COLOR_WHITE, (eye_center[0] + 3, eye_center[1] - 1), 1) # Işık yansıması

        # d) Gaga
        beak_points = [
            (self.width, 14),
            (self.width + 12, 17),
            (self.width, 21)
        ]
        pygame.draw.polygon(bird_surf, COLOR_BIRD_BEAK, beak_points)
        pygame.draw.polygon(bird_surf, COLOR_BLACK, beak_points, 1)

        # e) Kanat (Animasyonlu)
        wing_y_offset = 0
        if self.wing_state == 1:
            wing_y_offset = -4  # Yukarı kanat
        elif self.wing_state == 2:
            wing_y_offset = 4   # Aşağı kanat

        wing_rect = pygame.Rect(8, 12 + wing_y_offset, 14, 9)
        pygame.draw.ellipse(bird_surf, (245, 185, 20), wing_rect)
        pygame.draw.ellipse(bird_surf, COLOR_BLACK, wing_rect, 1)

        # Kuş yüzeyini mevcut açıya göre döndür
        rotated_surf = pygame.transform.rotate(bird_surf, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))

        # Ekrana bas
        surface.blit(rotated_surf, new_rect.topleft)


class Pipe:
    """
    Boru Sınıfı (Pipe Class)
    Birbirine bağlı üst ve alt boru çiftini yönetir.
    Sola kayma, skor geçiş kontrolü ve engel çizimi yapar.
    """

    def __init__(self, x, top_height):
        self.x = x
        self.top_height = top_height
        self.bottom_y = top_height + PIPE_GAP
        self.width = PIPE_WIDTH
        self.passed = False  # Kuş bu boruyu geçti mi? (Skor için)

    def update(self):
        """Boruyu sola doğru sabit hızla hareket ettirir."""
        self.x -= PIPE_SPEED

    def is_offscreen(self):
        """Boru tamamen ekranın solundan çıktı mı?"""
        return self.x + self.width < 0

    def get_rects(self):
        """Çarpışma tespiti için üst ve alt borunun dikdörtgen alanlarını (Rect) döndürür."""
        top_rect = pygame.Rect(int(self.x), 0, self.width, int(self.top_height))
        bottom_rect = pygame.Rect(
            int(self.x),
            int(self.bottom_y),
            self.width,
            SCREEN_HEIGHT - GROUND_HEIGHT - int(self.bottom_y)
        )
        return top_rect, bottom_rect

    def draw(self, surface):
        """Üst ve alt boruları şık gölgelendirmeler ve kapak detaylarıyla çizer."""
        top_rect, bottom_rect = self.get_rects()

        for rect, is_top in [(top_rect, True), (bottom_rect, False)]:
            # 1. Boru Ana Gövde
            pygame.draw.rect(surface, COLOR_PIPE, rect)

            # 2. Gölge ve Parlama Çizgileri (Derinlik efekti)
            # Sol taraf açık yeşil parlama
            pygame.draw.rect(surface, COLOR_PIPE_LIGHT, (rect.x + 3, rect.y, 6, rect.height))
            # Sağ taraf koyu yeşil gölge
            pygame.draw.rect(surface, COLOR_PIPE_DARK, (rect.x + rect.width - 10, rect.y, 8, rect.height))
            # Dış Siyah Hat
            pygame.draw.rect(surface, COLOR_BLACK, rect, 2)

            # 3. Boru Şapkası / Kapağı (Pipe Cap)
            cap_height = 24
            cap_extra = 6
            cap_x = rect.x - cap_extra // 2
            cap_width = rect.width + cap_extra

            if is_top:
                cap_y = rect.bottom - cap_height
            else:
                cap_y = rect.top

            cap_rect = pygame.Rect(cap_x, cap_y, cap_width, cap_height)

            # Kapak Çizimi
            pygame.draw.rect(surface, COLOR_PIPE, cap_rect)
            pygame.draw.rect(surface, COLOR_PIPE_LIGHT, (cap_rect.x + 4, cap_rect.y, 7, cap_rect.height))
            pygame.draw.rect(surface, COLOR_PIPE_DARK, (cap_rect.x + cap_rect.width - 12, cap_rect.y, 9, cap_rect.height))
            pygame.draw.rect(surface, COLOR_BLACK, cap_rect, 2)


class Ground:
    """
    Zemin Sınıfı (Ground Class)
    Sonsuz kayan zemin (Parallax Scrolling) illüzyonu oluşturur.
    """

    def __init__(self):
        self.height = GROUND_HEIGHT
        self.y = SCREEN_HEIGHT - self.height
        self.x = 0
        self.speed = PIPE_SPEED

    def update(self):
        """Zemini sola kaydırır. Örüntü genişliğini aşınca sıfırlar."""
        self.x = (self.x - self.speed) % 24  # 24 pikselde bir tekrarlar

    def draw(self, surface):
        """Zemini çim ve çizgili kum desenleriyle çizer."""
        # 1. Alt Kum Alanı
        ground_rect = pygame.Rect(0, self.y, SCREEN_WIDTH, self.height)
        pygame.draw.rect(surface, COLOR_GROUND_LIGHT, ground_rect)

        # 2. Çizgili Desenler (Hareket Hissi)
        for i in range(-24, SCREEN_WIDTH + 24, 24):
            stripe_rect = pygame.Rect(i + self.x, self.y + 12, 12, self.height - 12)
            pygame.draw.rect(surface, COLOR_GROUND_DARK, stripe_rect)

        # 3. Üst Çim Çizgisi
        grass_rect = pygame.Rect(0, self.y, SCREEN_WIDTH, 12)
        pygame.draw.rect(surface, COLOR_GRASS, grass_rect)
        pygame.draw.line(surface, COLOR_BLACK, (0, self.y), (SCREEN_WIDTH, self.y), 2)
        pygame.draw.line(surface, COLOR_BLACK, (0, self.y + 12), (SCREEN_WIDTH, self.y + 12), 1)


class BackgroundCloud:
    """Arka planda yavaşça süzülen bulutlar."""

    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(30, 220)
        self.speed = random.uniform(0.3, 0.7)
        self.radius = random.randint(18, 30)

    def update(self):
        self.x -= self.speed
        if self.x + self.radius * 3 < 0:
            self.x = SCREEN_WIDTH + random.randint(10, 50)
            self.y = random.randint(30, 220)

    def draw(self, surface):
        # Yumuşak şeffaf bulut
        cloud_surf = pygame.Surface((self.radius * 4, self.radius * 2), pygame.SRCALPHA)
        color = (255, 255, 255, 180)
        
        r = self.radius
        pygame.draw.circle(cloud_surf, color, (r, r), r)
        pygame.draw.circle(cloud_surf, color, (int(r * 2), int(r * 0.8)), int(r * 0.85))
        pygame.draw.circle(cloud_surf, color, (int(r * 2.8), r), int(r * 0.7))
        
        surface.blit(cloud_surf, (self.x, self.y))


class Particle:
    """Zıplama veya çarpma esnasında oluşan şık görsel parçacık efekti."""

    def __init__(self, x, y, color=COLOR_WHITE):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-3.5, 1.0)
        self.radius = random.uniform(3, 6)
        self.life = 255  # Opaklık/Ömür
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # Parçacık yerçekimi
        self.life -= 10
        self.radius = max(0.5, self.radius - 0.1)

    def is_dead(self):
        return self.life <= 0

    def draw(self, surface):
        if self.life > 0:
            p_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            r, g, b = self.color
            pygame.draw.circle(p_surf, (r, g, b, max(0, self.life)), (self.radius, self.radius), self.radius)
            surface.blit(p_surf, (self.x - self.radius, self.y - self.radius))
