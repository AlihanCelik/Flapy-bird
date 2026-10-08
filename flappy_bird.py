"""
==============================================================================
               FLAPPY BIRD - PYTHON & PYGAME EĞİTİM PROJESİ
==============================================================================
Bu proje, Python ve Pygame kütüphanesi kullanılarak 2D oyun geliştirme 
temellerini öğretmek amacıyla hazırlanmıştır.

EĞİTİM KAZANIMLARI:
  1. Nesne Yönelimli Programlama (OOP): Sınıflar (Class), Kalıtım ve Kapsülleme.
  2. Oyun Döngüsü (Game Loop): Etkinlik Dinleme, Mantık Güncelleme ve Çizim.
  3. 2D Oyun Fiziği: Yerçekimi (Gravity), İvme (Velocity) ve Eğim Açısı.
  4. Çarpışma Tespiti (Collision Detection): AABB Dikdörtgen kesişim tespiti.
  5. Prosedürel Ses Üretimi: Dış dosyalara ihtiyaç duymadan 8-bit sesler üretme.
  6. Görsel Tasarım & Animasyon: Vektörel çizimler, parçacık efektleri ve arayüz.

GEREKSİNİMLER:
  - Python 3.8+
  - Pygame veya Pygame-ce (`pip install pygame-ce`)

ÇALIŞTIRMA:
  python flappy_bird.py
==============================================================================
"""

import os
import math
import time
import random
import struct
import pygame

# ============================================================================
# 1. SABİTLER VE YAPILANDIRMA (CONSTANTS & CONFIGURATION)
# ============================================================================
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Fizik Sabitleri
GRAVITY = 0.38            # Her karede hıza eklenen dikey yerçekimi ivmesi
JUMP_STRENGTH = -7.5      # Zıplama anında dikey hıza atanan eksi değer
MAX_FALL_SPEED = 9.0      # Maksimum düşüş limiti
BIRD_ROTATION_SPEED = 4.0 # Eğim değişim hızı

# Boru ve Zemin Ayarları
PIPE_SPEED = 2.4          # Boruların ve zeminin sola kayma hızı
PIPE_GAP = 165            # Üst ve alt boru arasındaki boşluk yüksekliği (Genişletildi)
PIPE_SPAWN_TIME = 1500    # Milisaniye cinsinden yeni boru çıkış sıklığı
PIPE_WIDTH = 64           # Boru genişliği
GROUND_HEIGHT = 80        # Ekranın altındaki zemin yüksekliği

# Renk Paleti (RGB)
COLOR_SKY_TOP = (40, 150, 215)
COLOR_SKY_BOTTOM = (160, 220, 240)
COLOR_GROUND_LIGHT = (220, 205, 125)
COLOR_GROUND_DARK = (195, 175, 95)
COLOR_GRASS = (85, 185, 60)
COLOR_PIPE = (70, 180, 50)
COLOR_PIPE_DARK = (45, 130, 30)
COLOR_PIPE_LIGHT = (130, 225, 100)
COLOR_BIRD_BODY = (255, 215, 0)
COLOR_BIRD_BEAK = (255, 120, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_UI_SHADOW = (40, 40, 40)


# ============================================================================
# 2. PROSEDÜREL SES SİSTEMİ (PROCEDURAL AUDIO MANAGER)
# ============================================================================
class SoundManager:
    """Dış ses dosyası kullanmadan hafızada ses dalgası üreten sınıf."""

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.is_muted = False
        self.sounds = {}
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self._generate_sounds()
            self.enabled = True
        except Exception as e:
            print(f"[Ses Bilgi]: Ses kartı ilklendirilemedi ({e}). Oyun sessiz çalışacak.")
            self.enabled = False

    def _create_sound(self, duration, freq_func):
        n_samples = int(self.sample_rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            t = i / self.sample_rate
            freq, amp, wave_type = freq_func(t, duration)
            phase = 2.0 * math.pi * freq * t
            
            if wave_type == 'sine':
                val = math.sin(phase)
            elif wave_type == 'square':
                val = 1.0 if math.sin(phase) > 0 else -1.0
            else:
                val = math.sin(phase) * 0.5 + math.sin(phase * 2.3) * 0.5

            envelope = 1.0 - (i / n_samples)
            sample_val = max(-32768, min(32767, int(val * amp * envelope * 32767)))
            buf.extend(struct.pack('<h', sample_val))
            
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _generate_sounds(self):
        # Zıplama sesi
        self.sounds['jump'] = self._create_sound(0.12, lambda t, d: (380 + (t/d)*520, 0.35, 'sine'))
        # Skor sesi
        self.sounds['score'] = self._create_sound(0.16, lambda t, d: (523.25 if t < d*0.5 else 659.25, 0.30, 'square'))
        # Çarpma sesi
        self.sounds['hit'] = self._create_sound(0.25, lambda t, d: (max(40, 260 - (t/d)*220), 0.50, 'noise'))

    def play(self, sound_name):
        if self.enabled and not self.is_muted and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        return self.is_muted


# ============================================================================
# 3. OYUN NESNELERİ (SPRITES & GAME OBJECTS)
# ============================================================================
class Bird:
    """Kuş Nesnesi: Fiziksel hareket, açı ve çizim mantığı."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 34
        self.height = 24
        self.velocity_y = 0.0
        self.angle = 0.0
        self.wing_state = 0
        self.anim_timer = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def jump(self):
        self.velocity_y = JUMP_STRENGTH
        self.angle = 30.0

    def update(self):
        # Yerçekimi uygula
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED

        # Konum güncelle
        self.y += self.velocity_y

        # Açı eğimi (Düşerken kafayı aşağı çevir)
        if self.velocity_y > 2.0:
            self.angle = max(-80.0, self.angle - BIRD_ROTATION_SPEED * 1.5)

        self.rect.y = int(self.y)

        # Kanat çırpma animasyonu
        self.anim_timer += 1
        if self.anim_timer % 6 == 0:
            self.wing_state = (self.wing_state + 1) % 3

    def draw(self, surface):
        bird_surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        
        # Gövde
        body_rect = pygame.Rect(5, 5, self.width, self.height)
        pygame.draw.ellipse(bird_surf, COLOR_BIRD_BODY, body_rect)
        pygame.draw.ellipse(bird_surf, COLOR_BLACK, body_rect, 2)

        # Göz
        eye_center = (self.width - 4, 11)
        pygame.draw.circle(bird_surf, COLOR_WHITE, eye_center, 6)
        pygame.draw.circle(bird_surf, COLOR_BLACK, eye_center, 6, 1)
        pygame.draw.circle(bird_surf, COLOR_BLACK, (eye_center[0] + 2, eye_center[1]), 3)

        # Gaga
        beak_points = [(self.width, 14), (self.width + 12, 17), (self.width, 21)]
        pygame.draw.polygon(bird_surf, COLOR_BIRD_BEAK, beak_points)
        pygame.draw.polygon(bird_surf, COLOR_BLACK, beak_points, 1)

        # Kanat
        wing_y_offset = -4 if self.wing_state == 1 else (4 if self.wing_state == 2 else 0)
        wing_rect = pygame.Rect(8, 12 + wing_y_offset, 14, 9)
        pygame.draw.ellipse(bird_surf, (245, 185, 20), wing_rect)
        pygame.draw.ellipse(bird_surf, COLOR_BLACK, wing_rect, 1)

        # Açıya göre döndür ve bas
        rotated_surf = pygame.transform.rotate(bird_surf, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        surface.blit(rotated_surf, new_rect.topleft)


class Pipe:
    """Boru Çifti Nesnesi (Üst ve Alt Boru)."""

    def __init__(self, x, top_height):
        self.x = x
        self.top_height = top_height
        self.bottom_y = top_height + PIPE_GAP
        self.width = PIPE_WIDTH
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED

    def is_offscreen(self):
        return self.x + self.width < 0

    def get_rects(self):
        top_rect = pygame.Rect(int(self.x), 0, self.width, int(self.top_height))
        bottom_rect = pygame.Rect(
            int(self.x), int(self.bottom_y),
            self.width, SCREEN_HEIGHT - GROUND_HEIGHT - int(self.bottom_y)
        )
        return top_rect, bottom_rect

    def draw(self, surface):
        top_rect, bottom_rect = self.get_rects()

        for rect, is_top in [(top_rect, True), (bottom_rect, False)]:
            # Gövde
            pygame.draw.rect(surface, COLOR_PIPE, rect)
            pygame.draw.rect(surface, COLOR_PIPE_LIGHT, (rect.x + 3, rect.y, 6, rect.height))
            pygame.draw.rect(surface, COLOR_PIPE_DARK, (rect.x + rect.width - 10, rect.y, 8, rect.height))
            pygame.draw.rect(surface, COLOR_BLACK, rect, 2)

            # Kapak
            cap_h = 24
            cap_w = rect.width + 6
            cap_x = rect.x - 3
            cap_y = (rect.bottom - cap_h) if is_top else rect.top
            cap_rect = pygame.Rect(cap_x, cap_y, cap_w, cap_h)

            pygame.draw.rect(surface, COLOR_PIPE, cap_rect)
            pygame.draw.rect(surface, COLOR_PIPE_LIGHT, (cap_rect.x + 4, cap_rect.y, 7, cap_rect.height))
            pygame.draw.rect(surface, COLOR_PIPE_DARK, (cap_rect.x + cap_rect.width - 12, cap_rect.y, 9, cap_rect.height))
            pygame.draw.rect(surface, COLOR_BLACK, cap_rect, 2)


class Ground:
    """Parallax Kaydırmalı Zemin."""

    def __init__(self):
        self.height = GROUND_HEIGHT
        self.y = SCREEN_HEIGHT - self.height
        self.x = 0

    def update(self):
        self.x = (self.x - PIPE_SPEED) % 24

    def draw(self, surface):
        # Kum
        pygame.draw.rect(surface, COLOR_GROUND_LIGHT, (0, self.y, SCREEN_WIDTH, self.height))
        # Çizgiler
        for i in range(-24, SCREEN_WIDTH + 24, 24):
            pygame.draw.rect(surface, COLOR_GROUND_DARK, (i + self.x, self.y + 12, 12, self.height - 12))
        # Üst Çim
        pygame.draw.rect(surface, COLOR_GRASS, (0, self.y, SCREEN_WIDTH, 12))
        pygame.draw.line(surface, COLOR_BLACK, (0, self.y), (SCREEN_WIDTH, self.y), 2)


class BackgroundCloud:
    """Arka Plan Bulutu."""

    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(30, 200)
        self.speed = random.uniform(0.3, 0.7)
        self.radius = random.randint(18, 28)

    def update(self):
        self.x -= self.speed
        if self.x + self.radius * 3 < 0:
            self.x = SCREEN_WIDTH + random.randint(10, 40)
            self.y = random.randint(30, 200)

    def draw(self, surface):
        cloud_surf = pygame.Surface((self.radius * 4, self.radius * 2), pygame.SRCALPHA)
        color = (255, 255, 255, 180)
        r = self.radius
        pygame.draw.circle(cloud_surf, color, (r, r), r)
        pygame.draw.circle(cloud_surf, color, (int(r * 2), int(r * 0.8)), int(r * 0.85))
        pygame.draw.circle(cloud_surf, color, (int(r * 2.8), r), int(r * 0.7))
        surface.blit(cloud_surf, (self.x, self.y))


class Particle:
    """Zıplama/Çarpma parçacık efekti."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-3.5, 1.0)
        self.radius = random.uniform(3, 5)
        self.life = 255

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 10
        self.radius = max(0.5, self.radius - 0.1)

    def draw(self, surface):
        if self.life > 0:
            p_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (255, 255, 255, max(0, self.life)), (self.radius, self.radius), self.radius)
            surface.blit(p_surf, (self.x - self.radius, self.y - self.radius))


# ============================================================================
# 4. OYUN YÖNETİCİSİ VE DÖNGÜ (GAME ENGINE)
# ============================================================================
class Game:
    """Oyun akışını, durumlarını ve grafik işleme mantığını birleştiren ana sınıf."""

    STATE_START = 0
    STATE_PLAYING = 1
    STATE_GAME_OVER = 2

    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird - Python Eğitim Sürümü")
        self.clock = pygame.time.Clock()

        # Yazı Tipleri
        self.font_large = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18, bold=True)

        self.sound = SoundManager()
        self.highscore_file = "highscore.txt"
        self.high_score = self._load_high_score()

        self.state = Game.STATE_START
        self.score = 0
        self.bird = None
        self.ground = None
        self.pipes = []
        self.clouds = [BackgroundCloud() for _ in range(5)]
        self.particles = []
        
        self.last_pipe_spawn = 0
        self.screen_shake = 0
        self.score_pop_scale = 1.0

        self.reset_game()

    def _load_high_score(self):
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, "r") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def _save_high_score(self):
        try:
            with open(self.highscore_file, "w") as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    def reset_game(self):
        self.bird = Bird(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - 30)
        self.ground = Ground()
        self.pipes = []
        self.particles = []
        self.score = 0
        self.last_pipe_spawn = pygame.time.get_ticks()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_m:
                    self.sound.toggle_mute()
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self._on_jump()
                if event.key == pygame.K_r and self.state == Game.STATE_GAME_OVER:
                    self.state = Game.STATE_PLAYING
                    self.reset_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._on_jump()

        return True

    def _on_jump(self):
        if self.state in (Game.STATE_START, Game.STATE_GAME_OVER):
            self.state = Game.STATE_PLAYING
            self.reset_game()
            self.bird.jump()
            self.sound.play("jump")
        elif self.state == Game.STATE_PLAYING:
            self.bird.jump()
            self.sound.play("jump")
            for _ in range(5):
                self.particles.append(Particle(self.bird.x, self.bird.y + 15))

    def update(self):
        for cloud in self.clouds:
            cloud.update()

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        if self.score_pop_scale > 1.0:
            self.score_pop_scale = max(1.0, self.score_pop_scale - 0.05)

        if self.state == Game.STATE_START:
            self.ground.update()
            self.bird.anim_timer += 1
            self.bird.y = (SCREEN_HEIGHT // 2 - 30) + math.sin(self.bird.anim_timer * 0.08) * 8
            self.bird.rect.y = int(self.bird.y)

        elif self.state == Game.STATE_PLAYING:
            self.bird.update()
            self.ground.update()

            now = pygame.time.get_ticks()
            if now - self.last_pipe_spawn > PIPE_SPAWN_TIME:
                top_h = random.randint(60, SCREEN_HEIGHT - GROUND_HEIGHT - 180)
                self.pipes.append(Pipe(SCREEN_WIDTH, top_h))
                self.last_pipe_spawn = now

            for pipe in self.pipes[:]:
                pipe.update()

                # Skor tespiti
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                    self.score_pop_scale = 1.4
                    self.sound.play("score")
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self._save_high_score()

                if pipe.is_offscreen():
                    self.pipes.remove(pipe)

            # Çarpışma kontrolü
            if self._check_collision():
                self.state = Game.STATE_GAME_OVER
                self.sound.play("hit")

    def _check_collision(self):
        if self.bird.y + self.bird.height >= SCREEN_HEIGHT - GROUND_HEIGHT or self.bird.y <= 0:
            return True

        bird_rect = self.bird.rect.inflate(-6, -6)
        for pipe in self.pipes:
            top_rect, bottom_rect = pipe.get_rects()
            if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
                return True

        return False

    def draw_text(self, text, font, color, center_pos, shadow=True):
        x, y = center_pos
        if shadow:
            s_surf = font.render(text, True, COLOR_UI_SHADOW)
            self.screen.blit(s_surf, s_surf.get_rect(center=(x + 2, y + 2)))
        t_surf = font.render(text, True, color)
        self.screen.blit(t_surf, t_surf.get_rect(center=(x, y)))

    def render(self):
        # Arka Plan Gradyanı
        for y in range(SCREEN_HEIGHT - GROUND_HEIGHT):
            ratio = y / (SCREEN_HEIGHT - GROUND_HEIGHT)
            r = int(COLOR_SKY_TOP[0] * (1 - ratio) + COLOR_SKY_BOTTOM[0] * ratio)
            g = int(COLOR_SKY_TOP[1] * (1 - ratio) + COLOR_SKY_BOTTOM[1] * ratio)
            b = int(COLOR_SKY_TOP[2] * (1 - ratio) + COLOR_SKY_BOTTOM[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        for cloud in self.clouds:
            cloud.draw(self.screen)

        for pipe in self.pipes:
            pipe.draw(self.screen)

        self.ground.draw(self.screen)
        self.bird.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)

        # UI Katmanı
        if self.state == Game.STATE_START:
            self.draw_text("FLAPPY BIRD", self.font_large, COLOR_WHITE, (SCREEN_WIDTH // 2, 140))
            self.draw_text("Başlamak İçin Tıkla", self.font_medium, (255, 230, 80), (SCREEN_WIDTH // 2, 220))
            self.draw_text("veya [BOŞLUK] Tuşuna Bas", self.font_small, COLOR_WHITE, (SCREEN_WIDTH // 2, 260))

        elif self.state == Game.STATE_PLAYING:
            font = pygame.font.SysFont("Arial", int(42 * self.score_pop_scale), bold=True) if self.score_pop_scale > 1.0 else self.font_large
            self.draw_text(str(self.score), font, COLOR_WHITE, (SCREEN_WIDTH // 2, 70))

        elif self.state == Game.STATE_GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 110))
            self.screen.blit(overlay, (0, 0))

            card_w, card_h = 280, 190
            card_x = (SCREEN_WIDTH - card_w) // 2
            card_y = (SCREEN_HEIGHT - card_h) // 2 - 20
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            pygame.draw.rect(self.screen, (245, 235, 200), card_rect, border_radius=12)
            pygame.draw.rect(self.screen, (100, 70, 40), card_rect, width=3, border_radius=12)

            self.draw_text("OYUN BİTTİ", self.font_medium, (180, 40, 40), (SCREEN_WIDTH // 2, card_y + 35), shadow=False)
            self.draw_text(f"Skor: {self.score}", self.font_medium, COLOR_BLACK, (SCREEN_WIDTH // 2, card_y + 80), shadow=False)
            self.draw_text(f"En Yüksek: {self.high_score}", self.font_small, (80, 80, 80), (SCREEN_WIDTH // 2, card_y + 120), shadow=False)

            self.draw_text("Yeniden Başlamak İçin Tıkla", self.font_small, (255, 230, 80), (SCREEN_WIDTH // 2, card_y + card_h + 35))
            self.draw_text("veya [R] / [BOŞLUK] Tuşuna Bas", self.font_small, COLOR_WHITE, (SCREEN_WIDTH // 2, card_y + card_h + 60))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
