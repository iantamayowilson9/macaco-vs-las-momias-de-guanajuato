"""
Cámara: seguimiento del jugador, screen shake y zoom dinámico.
"""
import pygame
import math
import random
from src.constants import *
from src.font import get_font

#  CÁMARA CON SCREEN SHAKE Y ZOOM DINÁMICO
# ══════════════════════════════════════════════
class Camera:
    def __init__(self):
        self.offset_x = 0   # legacy (no usado en render, pero se conserva)
        self.offset_y = 0
        self.focus_x  = 640.0   # punto del mundo centrado en pantalla
        self.focus_y  = 360.0
        self.zoom     = 1.0
        self.target_zoom = 1.0

        # screen shake
        self.shake_intensity = 0
        self.shake_decay      = 0.85

        # paneo libre (para cofre)
        self.free_pan        = False
        self.free_target_x   = 0
        self.free_target_y   = 0
        self.free_timer      = 0   # frames que dura el paneo

        # flash de pantalla
        self.flash_timer  = 0
        self.flash_color  = (255, 0, 0)
        self.flash_alpha  = 0

    # ── Actualizar cada frame ──
    def update(self, player_x, player_y):
        # Zoom suave
        self.zoom += (self.target_zoom - self.zoom) * 0.08

        # El offset representa el punto del mundo que queremos centrar en pantalla.
        # Paneo libre (zoom al cofre)
        if self.free_pan:
            self.free_timer -= 1
            self.focus_x += (self.free_target_x - self.focus_x) * 0.12
            self.focus_y += (self.free_target_y - self.focus_y) * 0.12
            if self.free_timer <= 0:
                self.free_pan = False
        else:
            # Seguir al jugador suavemente
            self.focus_x += (player_x - self.focus_x) * 0.15
            self.focus_y += (player_y - self.focus_y) * 0.15

        # Screen shake
        self.shake_intensity *= self.shake_decay
        if self.shake_intensity < 0.5:
            self.shake_intensity = 0

        # Flash
        if self.flash_timer > 0:
            self.flash_timer -= 1
            self.flash_alpha = int(150 * (self.flash_timer / 12))

    def world_to_screen(self, wx, wy):
        """
        Convierte mundo → pantalla.
        El punto self.focus_x/y del mundo aparece en el centro de la pantalla,
        escalado desde ese mismo centro. Así el zoom nunca desplaza al jugador.
        """
        cx = SCREEN_W / 2
        cy = SCREEN_H / 2
        shake_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity)) if self.shake_intensity > 0 else 0
        shake_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity)) if self.shake_intensity > 0 else 0
        sx = cx + (wx - self.focus_x) * self.zoom + shake_x
        sy = cy + (wy - self.focus_y) * self.zoom + shake_y
        return int(sx), int(sy)

    # ── Disparadores de efectos ──
    def shake(self, intensity):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def flash(self, color=(255, 0, 0), duration=12):
        self.flash_color = color
        self.flash_timer = duration
        self.flash_alpha = 150

    def zoom_to(self, wx, wy, zoom_val=1.5, duration=80):
        """Paneo + zoom hacia un punto del mundo."""
        self.free_pan      = True
        self.free_target_x = wx
        self.free_target_y = wy
        self.free_timer    = duration
        self.target_zoom   = zoom_val

    def reset_zoom(self):
        self.target_zoom = 1.0

    def draw_flash(self, surface):
        if self.flash_alpha > 0:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            s.fill((*self.flash_color, self.flash_alpha))
            surface.blit(s, (0, 0))

    def draw_flash_zone(self, surface, zone_w):
        """Flash solo sobre la zona de juego (no el HUD)."""
        if self.flash_alpha > 0:
            s = pygame.Surface((zone_w, SCREEN_H), pygame.SRCALPHA)
            s.fill((*self.flash_color, self.flash_alpha))
            surface.blit(s, (0, 0))


# ══════════════════════════════════════════════

