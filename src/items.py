"""
Economía: monedas, ítems de cofre (HP/coins/escudo/velocidad) y cofres neón.
"""
import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.effects import FloatingText

#  MONEDA
# ══════════════════════════════════════════════
class Coin:
    def __init__(self, x, y, value=1):
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = random.uniform(-2, 2)
        self.vy    = random.uniform(-3, -1)
        self.value = value
        self.r     = 7
        self.dead  = False
        self.timer = 300  # desaparece si nadie la recoge

    def update(self, player):
        # Gravedad y fricción
        self.vy  += 0.15
        self.vx  *= 0.95
        self.x   += self.vx
        self.y   += self.vy
        if self.y > player.y + 500:   # límite inferior
            self.y = player.y + 500

        self.timer -= 1
        if self.timer <= 0:
            self.dead = True

        # Recolección
        dx = player.x - self.x
        dy = player.y - self.y
        if math.hypot(dx, dy) < 30:
            player.coins += self.value
            self.dead = True

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        r = max(3, int(self.r * camera.zoom))
        pygame.draw.circle(surface, NEON_YELLOW, (sx, sy), r)
        pygame.draw.circle(surface, WHITE, (sx, sy), r, 1)


# ══════════════════════════════════════════════
#  ÍTEM DEL COFRE
# ══════════════════════════════════════════════
ITEM_TYPES = [
    {"id": "hp",     "label": "+1 HP!",             "color": NEON_GREEN,  "shape": "circle"},
    {"id": "coins",  "label": "+50 MONEDAS!",        "color": NEON_YELLOW, "shape": "rect"},
    {"id": "shield", "label": "+10% TAMAÑO ESCUDO!", "color": NEON_CYAN,   "shape": "diamond"},
    {"id": "speed",  "label": "+10% VELOCIDAD!",     "color": NEON_PINK,   "shape": "triangle"},
]

class ChestItem:
    def __init__(self, x, y):
        self.x    = float(x)
        self.y    = float(y)
        self.data = random.choice(ITEM_TYPES)
        self.r    = 18
        self.dead = False
        self.bob  = 0.0

    def update(self, player):
        self.bob += 0.08
        dx = player.x - self.x
        dy = player.y - self.y
        if math.hypot(dx, dy) < 35:
            self.apply(player)
            self.dead = True

    def apply(self, player):
        d = self.data
        if d["id"] == "hp":
            player.hp = min(player.max_hp, player.hp + 1)
        elif d["id"] == "coins":
            player.coins += 50
        elif d["id"] == "shield":
            player.shield_radius = int(player.shield_radius * 1.10)
            player.damage = round(player.damage * 1.10, 2)   # escudo más grande → más impulso
        elif d["id"] == "speed":
            player.speed  *= 1.10
            player.defense = round(player.defense * 1.10, 2)  # más rápido → esquiva mejor
        player.floating_texts.append(
            FloatingText(d["label"], player.x, player.y - 40, d["color"], 26, 80))

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y + math.sin(self.bob) * 5)
        z = camera.zoom
        r = max(4, int(self.r * z))
        c = self.data["color"]
        sh = self.data["shape"]
        if sh == "circle":
            pygame.draw.circle(surface, c, (sx, sy), r)
            pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)
        elif sh == "rect":
            pygame.draw.rect(surface, c, (sx - r, sy - r, r*2, r*2))
            pygame.draw.rect(surface, WHITE, (sx - r, sy - r, r*2, r*2), 2)
        elif sh == "diamond":
            pts = [(sx, sy-r), (sx+r, sy), (sx, sy+r), (sx-r, sy)]
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.polygon(surface, WHITE, pts, 2)
        elif sh == "triangle":
            pts = [(sx, sy-r), (sx+r, sy+r), (sx-r, sy+r)]
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.polygon(surface, WHITE, pts, 2)


# ══════════════════════════════════════════════
#  COFRE NEÓN
# ══════════════════════════════════════════════
class Chest:
    def __init__(self, x, y):
        self.x      = float(x)
        self.y      = float(y)
        self.opened = False
        self.dead   = False
        self.bob    = 0.0
        self.glow   = 0

    def update(self, player, items, coins, camera, floating_texts):
        self.bob  += 0.06
        self.glow  = (math.sin(self.bob * 2) * 0.5 + 0.5)
        dx = player.x - self.x
        dy = player.y - self.y
        if not self.opened and math.hypot(dx, dy) < 45:
            self.opened = True
            # Disparar monedas
            for _ in range(15):
                coins.append(Coin(self.x + random.randint(-10,10),
                                  self.y + random.randint(-10,10), value=5))
            # Ítem aleatorio
            items.append(ChestItem(self.x, self.y - 50))
            floating_texts.append(
                FloatingText("¡COFRE ABIERTO!", self.x, self.y - 70,
                             NEON_YELLOW, 30, 90))
            # Zoom hacia el cofre
            camera.zoom_to(self.x, self.y, zoom_val=1.6, duration=90)
            camera.shake(8)
            self.dead = True

    def draw(self, surface, camera):
        if self.dead: return
        sx, sy = camera.world_to_screen(self.x, self.y + math.sin(self.bob)*6)
        z  = camera.zoom
        hw = max(6, int(28 * z))
        hh = max(4, int(22 * z))
        gv = int(self.glow * 200)
        glow_col = (gv, gv // 2, 0)
        # Cuerpo del cofre
        pygame.draw.rect(surface, (180, 100, 0), (sx-hw, sy-hh, hw*2, hh*2))
        pygame.draw.rect(surface, (gv, min(255,gv+100), 0), (sx-hw, sy-hh, hw*2, hh//2))
        pygame.draw.rect(surface, NEON_YELLOW, (sx-hw, sy-hh, hw*2, hh*2), 2)
        # Cerradura
        pygame.draw.circle(surface, NEON_YELLOW, (sx, sy), max(2, int(5*z)))


# ══════════════════════════════════════════════

