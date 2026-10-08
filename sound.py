"""
Flappy Bird - Ses Yöneticisi (Sound Manager)
Eğitim Modülü: Dış dosyalara bağımlı olmadan Python math ve struct modülleri 
ile hafızada 8-bit retro ses efektleri (Zıplama, Skor, Çarpma) üretir.
"""

import math
import struct
import pygame


class SoundManager:
    """Oyun ses efektlerini prosedürel (matematiksel) olarak üreten sınıf."""

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.is_muted = False
        self.sounds = {}
        
        # Pygame mixer ilklendirmesi
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self._generate_sounds()
            self.enabled = True
        except Exception as e:
            print(f"[Ses Uyarı]: Ses sistemi başlatılamadı ({e}). Oyun sessiz çalışacak.")
            self.enabled = False

    def _create_sound_buffer(self, duration, freq_func):
        """
        Belirli bir süre ve frekans fonksiyonuna göre 16-bit PCM ses verisi üretir.
        
        Parametreler:
            duration (float): Ses süresi (saniye).
            freq_func (function): Zaman t (0.0 - duration) verildiğinde anlık frekansı ve genliği dönen fonksiyon.
        """
        n_samples = int(self.sample_rate * duration)
        buf = bytearray()
        
        for i in range(n_samples):
            t = i / self.sample_rate
            freq, amp, wave_type = freq_func(t, duration)
            
            # Dalga tipi hesaplama (Sinüs veya Kare Dalga)
            phase = 2.0 * math.pi * freq * t
            if wave_type == 'sine':
                val = math.sin(phase)
            elif wave_type == 'square':
                val = 1.0 if math.sin(phase) > 0 else -1.0
            elif wave_type == 'noise':
                # Basit psödo-rastgele gürültü
                val = math.sin(phase) * 0.5 + (math.sin(phase * 2.3) * 0.5)
            else:
                val = math.sin(phase)

            # Seste patlamayı önlemek için zarf (Envelope - Fade Out)
            envelope = 1.0 - (i / n_samples)
            sample_val = int(val * amp * envelope * 32767)
            sample_val = max(-32768, min(32767, sample_val))
            
            # 16-bit Little-Endian formatında ekleme
            buf.extend(struct.pack('<h', sample_val))
            
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _generate_sounds(self):
        """Tüm oyun ses efektlerini oluşturur."""
        
        # 1. Zıplama Sesi (Jump Sound): Frekansı yükselen retro chiptune sesi
        def jump_freq(t, duration):
            freq = 380 + (t / duration) * 520  # 380 Hz -> 900 Hz
            amp = 0.35
            return freq, amp, 'sine'
            
        # 2. Skor Sesi (Score Sound): İki tonlu melodik zil (C5 -> E5)
        def score_freq(t, duration):
            if t < duration * 0.5:
                freq = 523.25  # Do (C5)
            else:
                freq = 659.25  # Mi (E5)
            amp = 0.30
            return freq, amp, 'square'

        # 3. Çarpma Sesi (Hit/Crash Sound): Hızla düşen gürültülü frekans
        def hit_freq(t, duration):
            freq = max(40, 260 - (t / duration) * 220)  # 260 Hz -> 40 Hz
            amp = 0.50
            return freq, amp, 'noise'

        self.sounds['jump'] = self._create_sound_buffer(0.12, jump_freq)
        self.sounds['score'] = self._create_sound_buffer(0.16, score_freq)
        self.sounds['hit'] = self._create_sound_buffer(0.25, hit_freq)

    def play(self, sound_name):
        """İsmi verilen sesi çalar."""
        if self.enabled and not self.is_muted and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def toggle_mute(self):
        """Sesi açar/kapatır."""
        self.is_muted = not self.is_muted
        return self.is_muted
