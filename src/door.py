import pygame
import math
import random
from src.constants import *
from src.font import get_font

class Door:
    """Representa los accesos entre salas que cambian visualmente si están bloqueados o abiertos."""
    def __init__(self, world_x, world_y, side, target_room):
        self.x           = float(world_x)
        self.y           = float(world_y)
        self.side        = side
        self.target_room = target_room
        self.open        = False
        self.w, self.h   = (80, 16) if side in ('top','bottom') else (16, 80)

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x - self.w//2, self.y - self.h//2)
        z = camera.zoom
        rw = max(4, int(self.w * z))
        rh = max(4, int(self.h * z))
        col = NEON_GREEN if self.open else DARK_RED
        pygame.draw.rect(surface, col, (sx, sy, rw, rh))
        pygame.draw.rect(surface, WHITE, (sx, sy, rw, rh), 2)
        
        font = get_font(max(8, int(11*z)), bold=True)
        lbl  = "OPEN" if self.open else "LOCK"
        img  = font.render(lbl, True, WHITE)
        surface.blit(img, (sx + rw//2 - img.get_width()//2,
                           sy + rh//2 - img.get_height()//2))

    def player_crosses(self, player):
        """Detecta si el jugador colisiona con el área delimitada de la puerta una vez abierta."""
        if not self.open: return False
        if self.side in ('left', 'right'):
            return (abs(player.x - self.x) < 50 and
                    abs(player.y - self.y) < 60)
        else:
            return (abs(player.x - self.x) < 60 and
                    abs(player.y - self.y) < 50)