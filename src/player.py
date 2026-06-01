"""
El Macaco: movimiento por mouse, escudo orbital con 8 sprites
direccionales, reflejo de balas, XP y level-up.
"""
import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.bullet import Bullet
from src.effects import FloatingText

#  JUGADOR: EL MACACO
# ══════════════════════════════════════════════
class Player:
    def __init__(self, x, y):
        self.x      = float(x)
        self.y      = float(y)
        self.hp     = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.speed  = PLAYER_BASE_SPEED
        self.coins  = 0
        self.xp     = 0
        self.xp_to_level = 100
        self.level  = 1

        self.shield_radius = SHIELD_BASE_RADIUS
        self.shield_angle  = 0.0
        self.shield_arc    = math.radians(SHIELD_ARC_DEG)

        # ── Stats derivadas (se recalculan en update) ──
        self.damage  = 1      # daño por bala reflejada (base 1, sube con ítems)
        self.defense = 1.0    # segundos de invencibilidad al recibir daño (base=1s)

        self.invincible_timer = 0
        self.r = 12

        # Referencia a listas globales (se asigna desde Game)
        self.floating_texts = []
        self.dead = False

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.xp_to_level = int(self.xp_to_level * 1.4)
            self.level += 1
            self.floating_texts.append(
                FloatingText("LEVEL UP!", self.x, self.y - 60, NEON_YELLOW, 28, 90))

    def update(self, mouse_world_x, mouse_world_y, walls):
        # Seguir al mouse
        dx = mouse_world_x - self.x
        dy = mouse_world_y - self.y
        d  = math.hypot(dx, dy)
        if d > 2:
            move = min(self.speed, d)
            self.x += (dx / d) * move
            self.y += (dy / d) * move

        # Colisión con paredes
        for wall in walls:
            # Empuje simple (AABB vs círculo)
            nearest_x = max(wall.left, min(self.x, wall.right))
            nearest_y = max(wall.top,  min(self.y, wall.bottom))
            ddx = self.x - nearest_x
            ddy = self.y - nearest_y
            dist = math.hypot(ddx, ddy)
            if dist < self.r and dist > 0:
                self.x += (ddx / dist) * (self.r - dist)
                self.y += (ddy / dist) * (self.r - dist)

        # Ángulo del escudo = hacia el mouse
        self.shield_angle = math.atan2(
            mouse_world_y - self.y,
            mouse_world_x - self.x)

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

    def check_bullet_collision(self, bullets, particles, floating_texts, camera):
        """Revisa si balas enemigas tocan al jugador o al escudo."""
        for b in bullets:
            if b.dead or b.owner != "enemy":
                continue
            dx = b.x - self.x
            dy = b.y - self.y
            dist = math.hypot(dx, dy)

            # ¿Está dentro del radio del escudo?
            if dist < self.shield_radius + b.r:
                bullet_angle = math.atan2(b.y - self.y, b.x - self.x)
                angle_diff   = abs(((bullet_angle - self.shield_angle + math.pi) % math.tau) - math.pi)

                if angle_diff < self.shield_arc / 2:
                    # ── REFLEJO ──
                    b.vx *= -1
                    b.vy *= -1
                    b.owner = "player"
                    b.color = NEON_YELLOW
                    camera.shake(3)
                    continue

            # ¿Golpea el cuerpo?
            if dist < self.r + b.r:
                if self.invincible_timer <= 0:
                    self.hp -= 1
                    self.invincible_timer = int(self.defense * 60)
                    camera.shake(14)
                    camera.flash((255, 0, 0), 14)
                    if b.is_giant:
                        # Explosión al recibir proyectil gigante
                        for _ in range(8):
                            particles.append(BloodParticle(b.x, b.y))
                    if self.hp <= 0:
                        self.dead = True
                b.dead = True

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        r = max(4, int(self.r * z))

        # Parpadeo de invencibilidad
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return

        # ── Sprite del Macaco — 8 direcciones ───────────────────
        # Elige el sprite según el ángulo hacia el mouse (shield_angle)
        # 0° = derecha, 90° = abajo, 180° = izquierda, 270° = arriba
        # (en pygame Y crece hacia abajo)
        drawn = False
        if hasattr(camera, '_game') and camera._game:
            g = camera._game
            spr_size = max(24, int(48 * z))

            # Normalizar ángulo a [0, 360)
            ang = math.degrees(self.shield_angle) % 360

            # Mapear a 8 sectores de 45° (cada sector centrado en su dirección)
            #   0°=→  45°=↘  90°=↓  135°=↙  180°=←  225°=↖  270°=↑  315°=↗
            if   ang < 22.5  or ang >= 337.5: tex_key = "player_right"
            elif ang < 67.5:                  tex_key = "player_downright"
            elif ang < 112.5:                 tex_key = "player_down"
            elif ang < 157.5:                 tex_key = "player_downleft"
            elif ang < 202.5:                 tex_key = "player_left"
            elif ang < 247.5:                 tex_key = "player_upleft"
            elif ang < 292.5:                 tex_key = "player_up"
            else:                             tex_key = "player_upright"

            drawn = g._draw_sprite(surface, tex_key, sx, sy, spr_size, spr_size, 0)
        if not drawn:
            pygame.draw.circle(surface, NEON_ORANGE, (sx, sy), r)
            pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)

        # ── Escudo orbital ──
        sr       = max(6, int(self.shield_radius * z))
        thickness = max(3, int(8 * z))
        node_r   = max(3, int(5 * z))
        # Ángulo del escudo en grados para rotar la imagen
        shield_deg = math.degrees(self.shield_angle)

        shield_drawn = False
        if hasattr(camera, '_game') and camera._game:
            g = camera._game
            img = g.tex.get("shield")
            if img:
                # El canvas de la textura cubre el diámetro completo del escudo
                # (sr*2 × sr*2). Se rota hacia el ángulo del mouse.
                canvas = sr * 2
                scaled = pygame.transform.scale(img, (canvas, canvas))
                rotated = pygame.transform.rotate(scaled, -shield_deg)
                # Re-centrar tras la rotación
                rect = rotated.get_rect(center=(sx, sy))
                surface.blit(rotated, rect.topleft)
                shield_drawn = True

        if not shield_drawn:
            # Fallback: arco geométrico neón
            arc_start = -(self.shield_angle + self.shield_arc / 2)
            arc_end   = -(self.shield_angle - self.shield_arc / 2)
            arc_rect  = pygame.Rect(sx - sr, sy - sr, sr * 2, sr * 2)
            pygame.draw.arc(surface, NEON_CYAN, arc_rect, arc_start, arc_end, thickness)

        # Nodos brillantes en los extremos (siempre, encima de la textura)
        for sign in [-1, 1]:
            a  = self.shield_angle + sign * self.shield_arc / 2
            nx = sx + int(math.cos(a) * sr)
            ny = sy + int(math.sin(a) * sr)
            pygame.draw.circle(surface, NEON_YELLOW, (nx, ny), node_r)

    def draw_hud(self, surface, font_sm, font_md, room_name="", acto_name="", font_lg=None):
        """
        HUD lateral derecho (220px) con todas las stats del Macaco.
        La zona de juego queda en x=[0..1060], el panel en x=[1060..1280].
        """
        hx = HUD_X      # 1060
        hw = HUD_W      # 220
        hs = SCREEN_H   # 720
        pad = 12

        # ── Fondo del panel ──
        pygame.draw.rect(surface, (8, 8, 18), (hx, 0, hw, hs))
        pygame.draw.line(surface, NEON_PURPLE, (hx, 0), (hx, hs), 2)

        y = pad

        # ── TÍTULO ──
        title = font_md.render("MACACO", True, NEON_ORANGE)
        surface.blit(title, (hx + hw//2 - title.get_width()//2, y))
        y += title.get_height() + 4
        sep_col = (50, 0, 80)

        def sep():
            nonlocal y
            pygame.draw.line(surface, sep_col, (hx+pad, y), (hx+hw-pad, y), 1)
            y += 6

        sep()

        # ── HP ──
        hp_lbl = font_sm.render("VIDA", True, (180,180,180))
        surface.blit(hp_lbl, (hx+pad, y))
        y += hp_lbl.get_height() + 2
        heart_size = 16
        hearts_per_row = 5
        for i in range(self.max_hp):
            col = (220,20,60) if i < self.hp else (60,0,15)
            bx  = hx + pad + (i % hearts_per_row) * (heart_size + 4)
            by  = y + (i // hearts_per_row) * (heart_size + 4)
            pygame.draw.rect(surface, col, (bx, by, heart_size, heart_size))
            pygame.draw.rect(surface, WHITE, (bx, by, heart_size, heart_size), 1)
        rows = math.ceil(self.max_hp / hearts_per_row)
        y += rows * (heart_size + 4) + 4
        hp_num = font_sm.render(f"{self.hp} / {self.max_hp}", True, (220,20,60))
        surface.blit(hp_num, (hx + hw//2 - hp_num.get_width()//2, y))
        y += hp_num.get_height() + 6
        sep()

        # ── NIVEL ──
        lv_txt = font_md.render(f"NIVEL  {self.level}", True, NEON_YELLOW)
        surface.blit(lv_txt, (hx + hw//2 - lv_txt.get_width()//2, y))
        y += lv_txt.get_height() + 4

        # Barra XP
        bw = hw - pad*2
        xp_ratio = self.xp / max(1, self.xp_to_level)
        pygame.draw.rect(surface, (20,20,60),   (hx+pad, y, bw, 10))
        pygame.draw.rect(surface, NEON_BLUE,    (hx+pad, y, int(bw*xp_ratio), 10))
        pygame.draw.rect(surface, WHITE,         (hx+pad, y, bw, 10), 1)
        y += 14
        xp_lbl = font_sm.render(f"XP {self.xp}/{self.xp_to_level}", True, NEON_BLUE)
        surface.blit(xp_lbl, (hx + hw//2 - xp_lbl.get_width()//2, y))
        y += xp_lbl.get_height() + 6
        sep()

        # ── MONEDAS ──
        coin_lbl = font_sm.render("MONEDAS", True, (180,180,180))
        surface.blit(coin_lbl, (hx+pad, y))
        y += coin_lbl.get_height() + 2
        coin_val = font_md.render(f"$ {self.coins}", True, NEON_YELLOW)
        surface.blit(coin_val, (hx + hw//2 - coin_val.get_width()//2, y))
        y += coin_val.get_height() + 6
        sep()

        # ── ESCUDO ──
        sh_lbl = font_sm.render("ESCUDO", True, (180,180,180))
        surface.blit(sh_lbl, (hx+pad, y))
        y += sh_lbl.get_height() + 2
        # Mini visualización del arco del escudo
        mini_cx = hx + hw//2
        mini_cy = y + 28
        mini_r  = 22
        # Fondo círculo
        pygame.draw.circle(surface, (15,15,35), (mini_cx, mini_cy), mini_r+4)
        pygame.draw.circle(surface, (40,40,80), (mini_cx, mini_cy), mini_r+4, 1)
        arc_r   = pygame.Rect(mini_cx-mini_r, mini_cy-mini_r, mini_r*2, mini_r*2)
        sh_ang  = self.shield_angle
        a_start = -(sh_ang + self.shield_arc/2)
        a_end   = -(sh_ang - self.shield_arc/2)
        pygame.draw.arc(surface, NEON_CYAN, arc_r, a_start, a_end, 4)
        # Punto central (jugador)
        pygame.draw.circle(surface, NEON_ORANGE, (mini_cx, mini_cy), 4)
        y += mini_r*2 + 8
        sh_info = font_sm.render(f"Radio: {self.shield_radius}px", True, NEON_CYAN)
        surface.blit(sh_info, (hx + hw//2 - sh_info.get_width()//2, y))
        y += sh_info.get_height() + 4
        sh_arc  = font_sm.render(f"Arco:  {SHIELD_ARC_DEG}°", True, NEON_CYAN)
        surface.blit(sh_arc, (hx + hw//2 - sh_arc.get_width()//2, y))
        y += sh_arc.get_height() + 6
        sep()

        # ── VELOCIDAD ──
        spd_lbl = font_sm.render("VELOCIDAD", True, (180,180,180))
        surface.blit(spd_lbl, (hx+pad, y))
        y += spd_lbl.get_height() + 2
        spd_val = font_sm.render(f"{self.speed:.1f} px/frame", True, NEON_GREEN)
        surface.blit(spd_val, (hx + hw//2 - spd_val.get_width()//2, y))
        y += spd_val.get_height() + 6
        sep()

        # ── DAÑO ──
        dmg_lbl = font_sm.render("DAÑO", True, (180,180,180))
        surface.blit(dmg_lbl, (hx+pad, y))
        y += dmg_lbl.get_height() + 2
        # Barra de daño (base 1 → max ~3 con ítems)
        dmg_ratio = min(1.0, self.damage / 3.0)
        bw = hw - pad*2
        pygame.draw.rect(surface, (40,0,0),    (hx+pad, y, bw, 10))
        pygame.draw.rect(surface, NEON_PINK,   (hx+pad, y, int(bw*dmg_ratio), 10))
        pygame.draw.rect(surface, WHITE,        (hx+pad, y, bw, 10), 1)
        y += 12
        dmg_val = font_sm.render(f"{self.damage:.2f}x  (1 hit/bala)", True, NEON_PINK)
        surface.blit(dmg_val, (hx + hw//2 - dmg_val.get_width()//2, y))
        y += dmg_val.get_height() + 6
        sep()

        # ── DEFENSA ──
        def_lbl = font_sm.render("DEFENSA", True, (180,180,180))
        surface.blit(def_lbl, (hx+pad, y))
        y += def_lbl.get_height() + 2
        # Barra de defensa (base 1s → max ~3s)
        def_ratio = min(1.0, self.defense / 3.0)
        pygame.draw.rect(surface, (0,20,60),   (hx+pad, y, bw, 10))
        pygame.draw.rect(surface, NEON_BLUE,   (hx+pad, y, int(bw*def_ratio), 10))
        pygame.draw.rect(surface, WHITE,        (hx+pad, y, bw, 10), 1)
        y += 12
        inv_frames = int(self.defense * 60)
        def_val = font_sm.render(f"{self.defense:.2f}s  ({inv_frames}f inv.)", True, NEON_BLUE)
        surface.blit(def_val, (hx + hw//2 - def_val.get_width()//2, y))
        y += def_val.get_height() + 6
        sep()

        # ── ACTO Y SALA ──
        if acto_name:
            at = font_sm.render(acto_name, True, NEON_ORANGE)
            surface.blit(at, (hx + hw//2 - at.get_width()//2, y))
            y += at.get_height() + 4
        room_lbl = font_sm.render("SALA", True, (180,180,180))
        surface.blit(room_lbl, (hx+pad, y))
        y += room_lbl.get_height() + 2
        clean = room_name.split("–")[-1].strip() if "–" in room_name else room_name
        rt = font_sm.render(clean, True, (120,120,200))
        surface.blit(rt, (hx + hw//2 - rt.get_width()//2, y))
        y += rt.get_height() + 4
        sep()

        # ── CONTROLES (mini) ──
        controls = [("MOUSE","Mover + Escudo"),("R","Reiniciar"),("ESC","Salir")]
        ctrl_lbl = font_sm.render("CONTROLES", True, (180,180,180))
        surface.blit(ctrl_lbl, (hx+pad, y))
        y += ctrl_lbl.get_height() + 2
        for key, desc in controls:
            k_s = font_sm.render(f"[{key}]", True, NEON_YELLOW)
            d_s = font_sm.render(desc, True, (140,140,180))
            surface.blit(k_s, (hx+pad, y))
            surface.blit(d_s, (hx+pad+40, y))
            y += k_s.get_height() + 1

    def draw_minimap(self, surface, rooms, current_room_idx, font_sm):
        """Minimapa de la run actual en el HUD. Muestra el camino generado."""
        hx  = HUD_X
        hw  = HUD_W
        pad = 12
        # Dibujar desde la parte inferior del HUD
        mm_y   = SCREEN_H - 130
        mm_lbl = font_sm.render("MAPA RUN", True, (180,180,180))
        surface.blit(mm_lbl, (hx+pad, mm_y - mm_lbl.get_height() - 2))
        pygame.draw.line(surface, (50,0,80), (hx+pad, mm_y-2), (hx+hw-pad, mm_y-2), 1)

        if not rooms:
            return
        # Tamaño de celda en el minimapa
        cell = 14
        gap  = 3
        # Obtener todos los grid_pos
        positions = [r["grid_pos"] for r in rooms]
        min_gx = min(p[0] for p in positions)
        min_gy = min(p[1] for p in positions)

        for i, room in enumerate(rooms):
            gx, gy = room["grid_pos"]
            rx = hx + pad + (gx - min_gx) * (cell + gap)
            ry = mm_y    + (gy - min_gy) * (cell + gap)
            if ry + cell > SCREEN_H - 4:
                continue
            if room.get("is_boss"):
                col = NEON_PURPLE
            elif room.get("is_start"):
                col = NEON_GREEN
            elif i == current_room_idx:
                col = NEON_ORANGE
            elif i < current_room_idx:
                col = (60, 60, 80)
            else:
                col = (30, 30, 50)
            pygame.draw.rect(surface, col, (rx, ry, cell, cell))
            pygame.draw.rect(surface, WHITE, (rx, ry, cell, cell), 1)
            # Flecha de conexión hacia el siguiente
            if i < len(rooms) - 1:
                nx_gx, nx_gy = rooms[i+1]["grid_pos"]
                nx_rx = hx + pad + (nx_gx - min_gx) * (cell + gap)
                nx_ry = mm_y    + (nx_gy - min_gy) * (cell + gap)
                pygame.draw.line(surface, (100,100,120),
                                 (rx+cell//2, ry+cell//2),
                                 (nx_rx+cell//2, nx_ry+cell//2), 1)


# ══════════════════════════════════════════════════════════════════

