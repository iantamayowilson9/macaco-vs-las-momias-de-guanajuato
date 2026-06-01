"""
Bestiario:
  EnemyBase, Momia, Zombi, PescadoMutante,
  EsqueletoRumbero, CthulhuDJ (Jefe 1).
"""
import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.bullet import Bullet
from src.effects import BloodParticle

#  ENEMIGOS BASE
# ══════════════════════════════════════════════
class EnemyBase:
    NAME = "Enemigo"   # cada subclase sobreescribe esto
    def __init__(self, x, y, hp, speed, xp, color, r=14):
        self.x     = float(x)
        self.y     = float(y)
        self.hp    = hp
        self.max_hp= hp
        self.speed = speed
        self.xp    = xp
        self.color = color
        self.r     = r
        self.dead  = False
        self.shoot_timer = 0
        self.shoot_cd    = 120   # frames entre disparos
        self.stun_timer  = 0
        self._name_font  = None  # se inicializa al primer draw para evitar init pre-pygame

    def _dir_key(self, tex_prefix, target_x, target_y):
        """
        Devuelve la clave de textura direccional (tex_prefix + _up/down/left/etc.)
        según el ángulo desde este enemigo hacia el objetivo (jugador).
        Si esa clave no existe en tex, devuelve tex_prefix como fallback.
        """
        ang = math.degrees(math.atan2(target_y - self.y, target_x - self.x)) % 360
        # Misma lógica que el jugador: 8 sectores de 45°
        if   ang < 22.5  or ang >= 337.5: suffix = "_right"
        elif ang < 67.5:                  suffix = "_downright"
        elif ang < 112.5:                 suffix = "_down"
        elif ang < 157.5:                 suffix = "_downleft"
        elif ang < 202.5:                 suffix = "_left"
        elif ang < 247.5:                 suffix = "_upleft"
        elif ang < 292.5:                 suffix = "_up"
        else:                             suffix = "_upright"
        return tex_prefix + suffix

    def _draw_tex_or_circle(self, surface, camera, tex_prefix, color, r_world,
                             target_x=None, target_y=None):
        """
        Dibuja el sprite del enemigo eligiendo la dirección correcta.
        tex_prefix: base del nombre, ej. "momia" → busca "momia_up", "momia_down", etc.
        Si no hay ninguna textura direccional, dibuja círculo neón.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        r = max(4, int(r_world * z))
        spr = max(r*2, int(48 * z))   # sprite siempre al menos 48px×zoom
        drawn = False
        if hasattr(camera, '_game') and camera._game:
            g = camera._game
            # Elegir dirección si hay coordenada objetivo
            if target_x is not None and target_y is not None:
                key = self._dir_key(tex_prefix, target_x, target_y)
            else:
                key = tex_prefix + "_down"   # fallback estático
            img = g.tex.get(key)
            # Si no tiene esa dirección, intentar con el prefijo solo
            if img is None:
                img = g.tex.get(tex_prefix)
            if img:
                scaled = pygame.transform.scale(img, (spr, spr))
                surface.blit(scaled, (sx - spr//2, sy - spr//2))
                drawn = True
        if not drawn:
            pygame.draw.circle(surface, color, (sx, sy), r)
            pygame.draw.circle(surface, WHITE,  (sx, sy), r, 2)
        return sx, sy, r

    def take_damage(self, dmg, particles, floating_texts, camera):
        self.hp -= dmg
        camera.shake(5)
        for _ in range(random.randint(10, 15)):
            particles.append(BloodParticle(self.x, self.y))
        if self.hp <= 0:
            self.dead = True

    def _collide_walls(self, walls):
        """Empuja al enemigo fuera de cualquier pared. Igual que el jugador."""
        for wall in walls:
            nearest_x = max(wall.left,  min(self.x, wall.right))
            nearest_y = max(wall.top,   min(self.y, wall.bottom))
            ddx = self.x - nearest_x
            ddy = self.y - nearest_y
            dist = math.hypot(ddx, ddy)
            if 0 < dist < self.r:
                self.x += (ddx / dist) * (self.r - dist + 1)
                self.y += (ddy / dist) * (self.r - dist + 1)

    def _draw_hp_bar(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        z   = camera.zoom
        r_s = max(4, int(self.r * z))
        bw  = max(24, int(self.r * 2.8 * z))
        bh  = max(4, int(6 * z))
        ratio = max(0, self.hp / self.max_hp)

        # ── Barra HP encima del sprite ──
        bar_y = sy - r_s - bh - 4
        pygame.draw.rect(surface, DARK_RED,   (sx - bw//2, bar_y, bw, bh))
        pygame.draw.rect(surface, NEON_GREEN, (sx - bw//2, bar_y, int(bw * ratio), bh))
        pygame.draw.rect(surface, WHITE,      (sx - bw//2, bar_y, bw, bh), 1)

        # ── Nombre debajo del sprite ──
        if self._name_font is None:
            self._name_font = get_font(max(8, int(11 * z)), bold=True)
        font_size = max(8, int(11 * z))
        # recrear fuente solo si el zoom cambia significativamente
        nf = pygame.font.SysFont("consolas", font_size, bold=True)
        lbl = nf.render(self.NAME, True, self.color)
        surface.blit(lbl, (sx - lbl.get_width() // 2, sy + r_s + 3))


# ── Momia ──
class Momia(EnemyBase):
    NAME = "Momia de Guanajuato"
    def __init__(self, x, y):
        super().__init__(x, y, hp=3, speed=1.2, xp=10, color=NEON_GREEN, r=13)
        self.shoot_cd    = 180
        self.move_timer  = 90

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return
        # Movimiento lento hacia el jugador
        self.move_timer -= 1
        if self.move_timer > 0:
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.x += (dx/d) * self.speed
            self.y += (dy/d) * self.speed
        else:
            if self.move_timer < -60:
                self.move_timer = 90

        # Disparo ráfaga lineal x3
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            speed = 5.5
            for i in range(3):
                delay_offset = i * 8
                bullets.append(Bullet(self.x, self.y,
                                      dx/d*speed, dy/d*speed,
                                      r=6, color=NEON_GREEN))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        # Texturas direccionales: momia_up.png  momia_down.png  momia_left.png  momia_right.png
        #                         momia_upleft.png  momia_upright.png
        #                         momia_downleft.png  momia_downright.png
        # (48×48 px, fondo transparente, mismo sistema que el jugador)
        px = camera._game.player.x if (hasattr(camera,'_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera,'_game') and camera._game) else self.y
        sx, sy, r = self._draw_tex_or_circle(surface, camera, "momia", self.color, self.r, px, py)
        z = camera.zoom
        # Vendas decorativas encima (siempre)
        for i in range(3):
            a  = i * (math.pi / 1.5)
            ex = sx + int(math.cos(a) * r * 0.8)
            ey = sy + int(math.sin(a) * r * 0.8)
            pygame.draw.line(surface, (200, 200, 180), (sx, sy), (ex, ey), max(1, int(2*z)))
        self._draw_hp_bar(surface, camera)


# ── Zombi ──
class Zombi(EnemyBase):
    NAME = "Zombi"
    def __init__(self, x, y):
        super().__init__(x, y, hp=2, speed=2.5, xp=15, color=NEON_PINK, r=13)
        self.shoot_cd = 200
        self.angle    = random.uniform(0, math.tau)
        self.erratic  = random.uniform(0.04, 0.1)

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return
        # Movimiento errático
        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        target_angle = math.atan2(dy, dx)
        self.angle  += (target_angle - self.angle) * 0.08
        self.angle  += random.uniform(-self.erratic, self.erratic)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            bullets.append(Bullet(self.x, self.y, dx/d*2.5, dy/d*2.5,
                                  r=14, color=NEON_PINK, homing=True, is_giant=True))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        z = camera.zoom
        # Texturas direccionales: zombi_up/down/left/right/upleft/upright/downleft/downright.png
        px = camera._game.player.x if (hasattr(camera,'_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera,'_game') and camera._game) else self.y
        sx, sy, r = self._draw_tex_or_circle(surface, camera, "zombi", self.color, self.r, px, py)
        # Ojos decorativos encima
        eo = int(r * 0.35)
        pygame.draw.circle(surface, NEON_YELLOW, (sx - eo, sy - eo // 2), max(2, int(3*z)))
        pygame.draw.circle(surface, NEON_YELLOW, (sx + eo, sy - eo // 2), max(2, int(3*z)))
        self._draw_hp_bar(surface, camera)


# ── Pescado Mutante ──
class PescadoMutante(EnemyBase):
    NAME = "Pescado Mutante"
    def __init__(self, x, y):
        super().__init__(x, y, hp=2, speed=1.8, xp=20, color=NEON_CYAN, r=14)
        self.shoot_cd = 150

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return
        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        self.x += (dx/d) * self.speed
        self.y += (dy/d) * self.speed

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            # Proyectiles con rebote (bounces=2)
            for spread in [-0.25, 0, 0.25]:
                angle = math.atan2(dy, dx) + spread
                bullets.append(Bullet(self.x, self.y,
                                      math.cos(angle)*4.5, math.sin(angle)*4.5,
                                      r=7, color=NEON_CYAN, bounces=2))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        z = camera.zoom
        # Texturas direccionales: pescado_up/down/left/right/upleft/upright/downleft/downright.png
        px = camera._game.player.x if (hasattr(camera,'_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera,'_game') and camera._game) else self.y
        sx, sy, r = self._draw_tex_or_circle(surface, camera, "pescado", self.color, self.r, px, py)
        self._draw_hp_bar(surface, camera)


# ── Esqueleto Rumbero ──
class EsqueletoRumbero(EnemyBase):
    NAME = "Esqueleto Rumbero"
    def __init__(self, x, y):
        super().__init__(x, y, hp=4, speed=1.0, xp=25, color=NEON_ORANGE, r=14)
        self.shoot_cd      = 140
        self.retreat_dist  = 260   # se mantiene a esta distancia

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return
        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        # Retrocede si está muy cerca
        if d < self.retreat_dist:
            self.x -= (dx/d) * self.speed
            self.y -= (dy/d) * self.speed
        else:
            self.x += (dx/d) * self.speed * 0.5
            self.y += (dy/d) * self.speed * 0.5

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            base_angle = math.atan2(dy, dx)
            # Abanico de 5 balas
            for i in range(5):
                spread = (i - 2) * 0.18
                a = base_angle + spread
                bullets.append(Bullet(self.x, self.y,
                                      math.cos(a)*5.5, math.sin(a)*5.5,
                                      r=6, color=NEON_ORANGE))
        self._collide_walls(walls)

    def draw(self, surface, camera):
        z = camera.zoom
        # Texturas direccionales: esqueleto_up/down/left/right/upleft/upright/downleft/downright.png
        px = camera._game.player.x if (hasattr(camera,'_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera,'_game') and camera._game) else self.y
        sx, sy, r = self._draw_tex_or_circle(surface, camera, "esqueleto", self.color, self.r, px, py)
        # Sonajero decorativo encima
        pygame.draw.line(surface, NEON_YELLOW, (sx, sy+r),
                         (sx+int(r*0.8), sy+int(r*1.8)), max(1, int(2*camera.zoom)))
        pygame.draw.circle(surface, NEON_YELLOW, (sx+int(r*0.8), sy+int(r*2)), max(2, int(4*camera.zoom)))
        self._draw_hp_bar(surface, camera)


# ══════════════════════════════════════════════
#  JEFE: CTHULHU DJ SONIDERO
# ══════════════════════════════════════════════
class CthulhuDJ(EnemyBase):
    NAME = "Cthulhu DJ Sonidero"
    def __init__(self, x, y):
        super().__init__(x, y, hp=40, speed=1.0, xp=200, color=NEON_PURPLE, r=36)
        self.phase      = 1
        self.shoot_timer= 0
        self.angle      = 0.0
        self.spiral_arm = 0.0

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        # Movimiento hacia jugador con algo de circling
        dx = player.x - self.x
        dy = player.y - self.y
        d  = math.hypot(dx, dy) or 1
        perp_x = -dy / d
        perp_y =  dx / d
        self.x += (dx/d) * self.speed * 0.4 + perp_x * 0.6
        self.y += (dy/d) * self.speed * 0.4 + perp_y * 0.6

        # ── Colisión con paredes (mismo sistema que el jugador) ──
        for wall in walls:
            nearest_x = max(wall.left, min(self.x, wall.right))
            nearest_y = max(wall.top,  min(self.y, wall.bottom))
            ddx = self.x - nearest_x
            ddy = self.y - nearest_y
            dist = math.hypot(ddx, ddy)
            if dist < self.r and dist > 0:
                self.x += (ddx / dist) * (self.r - dist)
                self.y += (ddy / dist) * (self.r - dist)

        # Cambiar de fase
        if self.hp < self.max_hp * 0.5:
            self.phase = 2

        self.shoot_timer += 1
        cd = 30 if self.phase == 2 else 50

        if self.shoot_timer >= cd:
            self.shoot_timer = 0
            # Patrón circular
            num_bullets = 16 if self.phase == 2 else 10
            for i in range(num_bullets):
                a = self.angle + (math.tau / num_bullets) * i
                spd = 3.5
                bullets.append(Bullet(self.x, self.y,
                                      math.cos(a)*spd, math.sin(a)*spd,
                                      r=8, color=NEON_PURPLE))
            self.angle += 0.3

            # Espiral adicional en fase 2
            if self.phase == 2:
                for i in range(8):
                    a = self.spiral_arm + (math.tau / 8) * i
                    spd = 4.5
                    bullets.append(Bullet(self.x, self.y,
                                          math.cos(a)*spd, math.sin(a)*spd,
                                          r=7, color=NEON_PINK))
                self.spiral_arm += 0.18

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        r = max(8, int(self.r * z))
        # TODO: Cargar sprite Cthulhu DJ aquí
        # Cuerpo
        t  = pygame.time.get_ticks() * 0.002
        gc = int(abs(math.sin(t)) * 180)
        glow_col = (int(gc * 0.7), 0, 255)
        pygame.draw.circle(surface, glow_col, (sx, sy), r + int(8*z))  # glow
        pygame.draw.circle(surface, NEON_PURPLE, (sx, sy), r)
        # Tentáculos
        num_tent = 6
        for i in range(num_tent):
            a   = t + (math.tau / num_tent) * i
            ex  = sx + int(math.cos(a) * r * 1.6)
            ey  = sy + int(math.sin(a) * r * 1.6)
            pygame.draw.line(surface, NEON_PINK, (sx, sy), (ex, ey), max(1, int(3*z)))
            pygame.draw.circle(surface, NEON_CYAN, (ex, ey), max(2, int(5*z)))
        # Audífonos DJ
        pygame.draw.arc(surface, NEON_YELLOW,
                        (sx - r, sy - r, r*2, r*2), 0.2, math.pi - 0.2,
                        max(2, int(4*z)))
        # Ojos
        pygame.draw.circle(surface, NEON_YELLOW, (sx - int(r*0.35), sy), max(3, int(5*z)))
        pygame.draw.circle(surface, NEON_YELLOW, (sx + int(r*0.35), sy), max(3, int(5*z)))
        # Barra HP grande
        bw = max(40, int(r * 3 * z))
        bh = max(6, int(8*z))
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, DARK_RED, (sx - bw//2, sy - r - bh - 6, bw, bh))
        pygame.draw.rect(surface, NEON_PURPLE, (sx - bw//2, sy - r - bh - 6, int(bw*ratio), bh))
        # Nombre
        font = get_font(max(8, int(13*z)), bold=True)
        lbl  = font.render("CTHULHU DJ SONIDERO", True, NEON_YELLOW)
        surface.blit(lbl, (sx - lbl.get_width()//2, sy - r - bh - 22))


# ══════════════════════════════════════════════



# ══════════════════════════════════════════════════════════════════
#  JEFE 2: LA MOMIA MAYOR (Las Catacumbas)
# ══════════════════════════════════════════════════════════════════
class MomiaMayor(EnemyBase):
    """
    Jefe del Acto 2.
    Fase 1: 8 vendas en espiral rotando.
    Fase 2 (HP<=50%): 12 vendas rápidas + ráfaga directa al jugador.
    """
    NAME = "La Momia Mayor"
    def __init__(self, x, y):
        super().__init__(x, y, hp=35, speed=0.8, xp=250,
                         color=(140,210,80), r=34)
        self.phase       = 1
        self.shoot_timer = 0
        self.spiral_ang  = 0.0

    def update(self, player, bullets, walls):
        if self.stun_timer > 0:
            self.stun_timer -= 1; return
        dx=player.x-self.x; dy=player.y-self.y; d=math.hypot(dx,dy) or 1
        px,py = -dy/d, dx/d
        self.x += dx/d*self.speed*0.3 + px*self.speed
        self.y += dy/d*self.speed*0.3 + py*self.speed
        self._collide_walls(walls)
        if self.hp < self.max_hp*0.5: self.phase = 2
        self.shoot_timer += 1
        cd = 35 if self.phase == 2 else 60
        if self.shoot_timer >= cd:
            self.shoot_timer = 0
            n = 12 if self.phase == 2 else 8
            for i in range(n):
                a = self.spiral_ang + (math.tau/n)*i
                spd = 4.5 if self.phase == 2 else 3.5
                bullets.append(Bullet(self.x, self.y,
                    math.cos(a)*spd, math.sin(a)*spd, r=7, color=(140,210,80)))
            if self.phase == 2:
                ap = math.atan2(dy, dx)
                for sp in [-0.3, 0, 0.3]:
                    bullets.append(Bullet(self.x, self.y,
                        math.cos(ap+sp)*5.5, math.sin(ap+sp)*5.5,
                        r=8, color=(57,255,20)))
            self.spiral_ang += 0.25 if self.phase == 1 else 0.4

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        r = max(8, int(self.r*z))
        t = pygame.time.get_ticks()*0.002
        gc = int(abs(math.sin(t*1.5))*150+80)
        # Texturas
        px = camera._game.player.x if (hasattr(camera,'_game') and camera._game) else self.x
        py = camera._game.player.y if (hasattr(camera,'_game') and camera._game) else self.y
        sx2, sy2, r2 = self._draw_tex_or_circle(
            surface, camera, "momia_mayor", (140,210,80), self.r, px, py)
        # Glow verde encima si no hay textura
        if r2 == r:  # círculo fallback
            pygame.draw.circle(surface, (0,gc,0), (sx2,sy2), r2+int(8*z), 3)
        # Vendas
        for i in range(4):
            a = t*0.5 + (math.tau/4)*i
            ex = sx2 + int(math.cos(a)*r2*1.4)
            ey = sy2 + int(math.sin(a)*r2*1.4)
            pygame.draw.line(surface,(220,220,180),(sx2,sy2),(ex,ey),max(2,int(3*z)))
        # Barra HP
        bw=max(40,int(r2*3*z)); bh=max(6,int(8*z))
        ratio=max(0,self.hp/self.max_hp)
        pygame.draw.rect(surface,(150,0,30),(sx2-bw//2,sy2-r2-bh-6,bw,bh))
        pygame.draw.rect(surface,(100,200,60),(sx2-bw//2,sy2-r2-bh-6,int(bw*ratio),bh))
        nf = get_font(max(8,int(13*z)), bold=True)
        lbl = nf.render("LA MOMIA MAYOR", True, (180,255,100))
        surface.blit(lbl,(sx2-lbl.get_width()//2, sy2-r2-bh-22))
