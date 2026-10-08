"""
Flappy Bird - Oyun Yöneticisi ve Akışı (Game Engine & State Manager)
Eğitim Modülü: Oyun döngüsü, durum yönetimi (Başlangıç, Oynanış, Oyun Bitti), 
çarpışma tespiti, skor takibi ve kullanıcı etkileşimini kontrol eden ana sınıf.
"""

import os
import math
import random
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, PIPE_SPAWN_TIME, GROUND_HEIGHT,
    COLOR_SKY_TOP, COLOR_SKY_BOTTOM, COLOR_WHITE, COLOR_BLACK, COLOR_UI_TEXT,
    COLOR_UI_SHADOW, COLOR_BUTTON, COLOR_BUTTON_HOVER
)
from sound import SoundManager
from sprites import Bird, Pipe, Ground, BackgroundCloud, Particle


class Game:
    """Oyunun tüm akışını ve mantığını yöneten ana sınıf."""

    # Oyun Durumları (State Machine)
    STATE_START = 0
    STATE_PLAYING = 1
    STATE_GAME_OVER = 2

    def __init__(self):
        # Pygame Ekran & Pencere Başlatma
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird - Eğitim Sürümü")
        self.clock = pygame.time.Clock()

        # Fontlar
        self.font_large = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18, bold=True)

        # Ses Yöneticisi
        self.sound = SoundManager()

        # Yüksek Skor Verisi
        self.highscore_file = "highscore.txt"
        self.high_score = self._load_high_score()

        # Oyun Elemanları
        self.state = Game.STATE_START
        self.score = 0
        self.bird = None
        self.ground = None
        self.pipes = []
        self.clouds = []
        self.particles = []

        # Zamanlayıcılar ve Görsel Efektler
        self.last_pipe_spawn = 0
        self.screen_shake = 0
        self.score_pop_scale = 1.0

        # Oyunu Sıfırla
        self.reset_game()

    def _load_high_score(self):
        """En yüksek skoru dosyadan okur."""
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, "r") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def _save_high_score(self):
        """Yeni rekor kırıldığında dosyaya kaydeder."""
        try:
            with open(self.highscore_file, "w") as f:
                f.write(str(self.high_score))
        except Exception as e:
            print(f"[Dosya Hatası]: Skor kaydedilemedi: {e}")

    def reset_game(self):
        """Oyunu başlangıç durumuna getirir ve nesneleri yeniden oluşturur."""
        self.bird = Bird(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - 30)
        self.ground = Ground()
        self.pipes = []
        self.particles = []
        self.score = 0
        self.last_pipe_spawn = pygame.time.get_ticks()
        self.screen_shake = 0
        
        # Bulutları bir kez ilklendir
        if not self.clouds:
            self.clouds = [BackgroundCloud() for _ in range(5)]

    def handle_events(self):
        """Kullanıcı klavye ve fare girdi olaylarını işler."""
        for event in pygame.event.get():
            # 1. Çıkış Olayı (Pencere Kapatma)
            if event.type == pygame.QUIT:
                return False

            # 2. Klavye Tuş Basımları
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                # Sesi Aç/Kapat (M tuşu)
                if event.key == pygame.K_m:
                    self.sound.toggle_mute()

                # Zıplama / Oyunu Başlatma (Boşluk veya Yukarı Ok)
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self._on_jump_action()

                # Yeniden Başlatma (R tuşu)
                if event.key == pygame.K_r and self.state == Game.STATE_GAME_OVER:
                    self.state = Game.STATE_PLAYING
                    self.reset_game()

            # 3. Fare Tıklaması
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._on_jump_action()

        return True

    def _on_jump_action(self):
        """Tıklama veya Boşluk tuşuna basıldığında duruma göre işlem yapar."""
        if self.state == Game.STATE_START:
            self.state = Game.STATE_PLAYING
            self.bird.jump()
            self.sound.play("jump")
            self._spawn_particles(self.bird.x, self.bird.y + 15, 8)
        elif self.state == Game.STATE_PLAYING:
            self.bird.jump()
            self.sound.play("jump")
            self._spawn_particles(self.bird.x, self.bird.y + 15, 5)
        elif self.state == Game.STATE_GAME_OVER:
            self.state = Game.STATE_PLAYING
            self.reset_game()

    def _spawn_particles(self, x, y, count=5):
        """Tıklanan noktada tüyler/toz parçacıkları oluşturur."""
        for _ in range(count):
            self.particles.append(Particle(x, y))

    def _spawn_pipe(self):
        """Rastgele yükseklikte yeni bir boru çifti oluşturur."""
        min_h = 60
        max_h = SCREEN_HEIGHT - GROUND_HEIGHT - 180
        top_h = random.randint(min_h, max_h)
        self.pipes.append(Pipe(SCREEN_WIDTH, top_h))

    def check_collisions(self):
        """Çarpışmaları kontrol eder (Kuş vs Zemin, Tavan ve Borular)."""
        # a) Zemin veya Tavan Çarpışması
        if self.bird.y + self.bird.height >= SCREEN_HEIGHT - GROUND_HEIGHT:
            self.bird.y = SCREEN_HEIGHT - GROUND_HEIGHT - self.bird.height
            return True

        if self.bird.y <= 0:
            self.bird.y = 0
            self.bird.velocity_y = 0

        # Kuş Çarpışma Kutusu (Toleranslı / Eğlenceli Çarpışma için 4px daraltılmış)
        bird_rect = self.bird.rect.inflate(-6, -6)

        # b) Boru Çarpışmaları
        for pipe in self.pipes:
            top_rect, bottom_rect = pipe.get_rects()
            if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
                return True

        return False

    def update(self):
        """Her karede tüm oyun mantığını ve konumları günceller."""
        # Bulutları her zaman güncelle (Animasyonel zenginlik)
        for cloud in self.clouds:
            cloud.update()

        # Parçacık efektlerini güncelle
        for particle in self.particles[:]:
            particle.update()
            if particle.is_dead():
                self.particles.remove(particle)

        # Efekt Yumuşatmaları
        if self.screen_shake > 0:
            self.screen_shake -= 1

        if self.score_pop_scale > 1.0:
            self.score_pop_scale = max(1.0, self.score_pop_scale - 0.05)

        # ----------------------------------------------------
        # 1. BAŞLANGIÇ DURUMU (START)
        # ----------------------------------------------------
        if self.state == Game.STATE_START:
            self.ground.update()
            # Kuşun süzülme animasyonu (Sinüs dalgası ile yumuşak yukarı-aşağı)
            self.bird.anim_timer += 1
            self.bird.y = (SCREEN_HEIGHT // 2 - 30) + math.sin(self.bird.anim_timer * 0.08) * 8
            self.bird.rect.y = int(self.bird.y)

        # ----------------------------------------------------
        # 2. OYNANIŞ DURUMU (PLAYING)
        # ----------------------------------------------------
        elif self.state == Game.STATE_PLAYING:
            self.bird.update()
            self.ground.update()

            # Zamanı geldikçe yeni boru ekle
            now = pygame.time.get_ticks()
            if now - self.last_pipe_spawn > PIPE_SPAWN_TIME:
                self._spawn_pipe()
                self.last_pipe_spawn = now

            # Boruları güncelle ve skor kontrolü yap
            for pipe in self.pipes[:]:
                pipe.update()

                # Skor Kazanma Kontrolü: Kuş boruyu geçti mi?
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                    self.score_pop_scale = 1.4  # Skor büyüme efekti
                    self.sound.play("score")

                    # Rekor Güncelleme
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self._save_high_score()

                # Ekrandan çıkan boruları sil (Hafıza optimizasyonu)
                if pipe.is_offscreen():
                    self.pipes.remove(pipe)

            # Çarpışma Kontrolü
            if self.check_collisions():
                self.state = Game.STATE_GAME_OVER
                self.screen_shake = 12  # Ekran sarsıntı süresi
                self.sound.play("hit")
                self._spawn_particles(self.bird.x + 15, self.bird.y + 12, 20)

    def draw_background(self):
        """Gökyüzü gradyanı ve arka plan bulutlarını çizer."""
        # Gökyüzü Dikey Gradyanı
        for y in range(SCREEN_HEIGHT - GROUND_HEIGHT):
            ratio = y / (SCREEN_HEIGHT - GROUND_HEIGHT)
            r = int(COLOR_SKY_TOP[0] * (1 - ratio) + COLOR_SKY_BOTTOM[0] * ratio)
            g = int(COLOR_SKY_TOP[1] * (1 - ratio) + COLOR_SKY_BOTTOM[1] * ratio)
            b = int(COLOR_SKY_TOP[2] * (1 - ratio) + COLOR_SKY_BOTTOM[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Bulutlar
        for cloud in self.clouds:
            cloud.draw(self.screen)

    def draw_ui_text(self, text, font, color, center_pos, shadow=True):
        """Gölge efektli şık UI metni çizer."""
        x, y = center_pos
        if shadow:
            shadow_surf = font.render(text, True, COLOR_UI_SHADOW)
            shadow_rect = shadow_surf.get_rect(center=(x + 2, y + 2))
            self.screen.blit(shadow_surf, shadow_rect)

        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(x, y))
        self.screen.blit(text_surf, text_rect)

    def render(self):
        """Tüm grafik elemanlarını ve arayüzü ekrana çizer."""
        # Ekran Sarsıntısı Offseti
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.randint(-4, 4)
            shake_y = random.randint(-4, 4)

        # Sarsıntı varsa geçici yüzey kullan
        target_surf = self.screen

        # 1. Arka Plan
        self.draw_background()

        # 2. Borular
        for pipe in self.pipes:
            pipe.draw(target_surf)

        # 3. Zemin
        self.ground.draw(target_surf)

        # 4. Kuş
        self.bird.draw(target_surf)

        # 5. Parçacıklar
        for particle in self.particles:
            particle.draw(target_surf)

        # ----------------------------------------------------
        # UI & ARAYÜZ KATMANLARI
        # ----------------------------------------------------
        if self.state == Game.STATE_START:
            self.draw_ui_text("FLAPPY BIRD", self.font_large, COLOR_WHITE, (SCREEN_WIDTH // 2, 140))
            self.draw_ui_text("Başlamak İçin Tıkla", self.font_medium, (255, 230, 80), (SCREEN_WIDTH // 2, 220))
            self.draw_ui_text("veya [BOŞLUK] Tuşuna Bas", self.font_small, COLOR_WHITE, (SCREEN_WIDTH // 2, 260))

        elif self.state == Game.STATE_PLAYING:
            # Canlı Skor Göstergesi (Pop animasyonlu)
            score_text = str(self.score)
            if self.score_pop_scale > 1.0:
                scaled_font = pygame.font.SysFont("Arial", int(42 * self.score_pop_scale), bold=True)
                self.draw_ui_text(score_text, scaled_font, COLOR_WHITE, (SCREEN_WIDTH // 2, 70))
            else:
                self.draw_ui_text(score_text, self.font_large, COLOR_WHITE, (SCREEN_WIDTH // 2, 70))

        elif self.state == Game.STATE_GAME_OVER:
            # Yarı şeffaf koyu panel overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 110))
            self.screen.blit(overlay, (0, 0))

            # Skor Kartı Paneli
            card_w, card_h = 280, 200
            card_x = (SCREEN_WIDTH - card_w) // 2
            card_y = (SCREEN_HEIGHT - card_h) // 2 - 20
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            pygame.draw.rect(self.screen, (245, 235, 200), card_rect, border_radius=12)
            pygame.draw.rect(self.screen, (100, 70, 40), card_rect, width=3, border_radius=12)

            # Başlık ve Skorlar
            self.draw_ui_text("OYUN BİTTİ", self.font_medium, (180, 40, 40), (SCREEN_WIDTH // 2, card_y + 35), shadow=False)
            self.draw_ui_text(f"Skor: {self.score}", self.font_medium, COLOR_BLACK, (SCREEN_WIDTH // 2, card_y + 85), shadow=False)
            self.draw_ui_text(f"En Yüksek: {self.high_score}", self.font_small, (80, 80, 80), (SCREEN_WIDTH // 2, card_y + 125), shadow=False)

            # Yeniden Başlat Buton İpucu
            self.draw_ui_text("Yeniden Başlamak İçin Tıkla", self.font_small, (255, 230, 80), (SCREEN_WIDTH // 2, card_y + card_h + 35))
            self.draw_ui_text("veya [R] / [BOŞLUK] Tuşuna Bas", self.font_small, COLOR_WHITE, (SCREEN_WIDTH // 2, card_y + card_h + 60))

        # Ekranı Güncelle
        pygame.display.flip()

    def run(self):
        """Ana oyun döngüsünü çalıştırır."""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
