import pygame
import math
import random
from src.constants import *
from src.font import get_font

class Camera:
    """
    Controla la visualización del juego mediante un sistema de enfoque suave (lerp).
    Maneja efectos dinámicos como temblor (screen shake), destellos de daño (flash)
    y paneos automáticos con zoom hacia los cofres.
    """
    def __init__(self):
        self.offset_x = 0   
        self.offset_y = 0
        self.focus_x  = 640.0   
        self.focus_y  = 360.0
        self.zoom     = 1.0
        self.target_zoom = 1.0

        self.shake_intensity = 0
        self.shake_decay      = 0.85

        self.free_pan        = False
        self.free_target_x   = 0
        self.free_target_y   = 0
        self.free_timer      = 0   

        self.flash_timer  = 0
        self.flash_color  = (255, 0, 0)
        self.flash_alpha  = 0

    def update(self, player_x, player_y):
        """Aplica interpolación para suavizar el movimiento de la cámara y el zoom en cada frame."""
        self.zoom += (self.target_zoom - self.zoom) * 0.08

        if self.free_pan:
            self.free_timer -= 1
            self.focus_x += (self.free_target_x - self.focus_x) * 0.12
            self.focus_y += (self.free_target_y - self.focus_y) * 0.12
            if self.free_timer <= 0:
                self.free_pan = False
        else:
            self.focus_x += (player_x - self.focus_x) * 0.15
            self.focus_y += (player_y - self.focus_y) * 0.15

        self.shake_intensity *= self.shake_decay
        if self.shake_intensity < 0.5:
            self.shake_intensity = 0

        if self.flash_timer > 0:
            self.flash_timer -= 1
            self.flash_alpha = int(150 * (self.flash_timer / 12))

    def world_to_screen(self, wx, wy):
        """
        Transforma coordenadas reales del mundo de juego a píxeles de la pantalla.
        Centra la imagen respecto al foco de la cámara y aplica el offset del screen shake.
        """
        cx = SCREEN_W / 2
        cy = SCREEN_H / 2
        shake_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity)) if self.shake_intensity > 0 else 0
        shake_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity)) if self.shake_intensity > 0 else 0
        sx = cx + (wx - self.focus_x) * self.zoom + shake_x
        sy = cy + (wy - self.focus_y) * self.zoom + shake_y
        return int(sx), int(sy)

    def shake(self, intensity):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def flash(self, color=(255, 0, 0), duration=12):
        self.flash_color = color
        self.flash_timer = duration
        self.flash_alpha = 150

    def zoom_to(self, wx, wy, zoom_val=1.5, duration=80):
        """Fuerza a la cámara a apuntar y acercarse temporalmente a un objetivo específico del escenario."""
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
        if self.flash_alpha > 0:
            s = pygame.Surface((zone_w, SCREEN_H), pygame.SRCALPHA)
            s.fill((*self.flash_color, self.flash_alpha))
            surface.blit(s, (0, 0))