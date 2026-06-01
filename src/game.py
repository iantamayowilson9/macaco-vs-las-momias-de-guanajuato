"""
Clase principal Game: bucle, estados, cámara, HUD, texturas y lógica central.
"""
import pygame
import math
import random
from src.constants import *
from src.font import get_font
import sys
from src.camera import Camera
from src.effects import FloatingText, BloodParticle
from src.items import Coin, Chest, ChestItem
from src.door import Door
from src.bullet import Bullet
from src.enemies import Momia, Zombi, PescadoMutante, EsqueletoRumbero, CthulhuDJ
from src.player import Player
from src.rooms import generate_map, generate_act2

#  CLASE PRINCIPAL DEL JUEGO
# ══════════════════════════════════════════════
class Game:
    def __init__(self):
        pygame.init()
        self.screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Macaco vs. Las Momias de Guanajuato")
        self.clock    = pygame.time.Clock()

        self.font_sm  = get_font(14, bold=True)
        self.font_md  = get_font(20, bold=True)
        self.font_lg  = get_font(36, bold=True)
        self.font_xl  = get_font(64, bold=True)

        # ══════════════════════════════════════════════════════════
        #  SISTEMA DE TEXTURAS
        #  Para activar una textura, pon el archivo de imagen en la
        #  misma carpeta que este script y descomenta la línea.
        #
        #  Formatos soportados: .png  .jpg  .bmp  .gif
        #  Las texturas se escalan automáticamente al tamaño correcto.
        # ══════════════════════════════════════════════════════════
        self.tex = self._load_textures()

        self.camera   = Camera()
        self.rooms    = []       # se genera al iniciar cada run
        self.acto     = 1        # 1=El Antro  2=Las Catacumbas
        self._act_trans_timer = 0
        self.estado   = "MENU"

        # Estas listas se llenan al cargar un cuarto
        self.enemies       = []
        self.bullets       = []
        self.coins         = []
        self.items         = []
        self.particles     = []
        self.floating_texts= []
        self.doors         = []
        self.chests        = []
        self.walls         = []

        self.player        = None
        self.current_room  = 0
        self.chest_spawned = False
        self.bg_color      = DIM_GRAY

        # Estrellas de fondo (decoración)
        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
                       random.randint(1, 3), random.random()) for _ in range(120)]

        self.menu_bg_tick  = 0
        self.run_number     = 0
        self._disco_tick    = 0
        self._scanline_surf = None

    # ══════════════════════════════════════════════════════════
    #  CARGA DE TEXTURAS
    # ══════════════════════════════════════════════════════════
    def _load_textures(self):
        """
        Carga todas las texturas del juego desde archivos de imagen.
        Si un archivo no existe, la textura queda en None y se usa
        el dibujo geométrico de neón por defecto.

        ┌──────────────────────────────────────────────────────────┐
        │  CÓMO AÑADIR TUS TEXTURAS:                               │
        │                                                          │
        │  1. Copia tu imagen a la misma carpeta que este .py      │
        │  2. Descomenta la línea correspondiente                  │
        │  3. Cambia el nombre del archivo por el tuyo             │
        │                                                          │
        │  Tamaños recomendados (se escalan automáticamente):      │
        │    Piso del Antro    : cualquier tamaño, se tesela       │
        │    Piso Catacumbas   : cualquier tamaño, se tesela       │
        │    Bloque de pared   : cuadrado, ej. 64×64 o 128×128    │
        │    Jugador (torso)   : 64×64 con fondo transparente      │
        │    Jugador (piernas) : 64×64 con fondo transparente      │
        │    Momia             : 48×48 con fondo transparente      │
        │    Zombi             : 48×48 con fondo transparente      │
        │    Pescado Mutante   : 48×48 con fondo transparente      │
        │    Esqueleto Rumbero : 48×48 con fondo transparente      │
        │    Cthulhu DJ        : 96×96 con fondo transparente      │
        │    Momia Mayor       : 96×96 con fondo transparente      │
        └──────────────────────────────────────────────────────────┘
        """
        def load(path):
            """Intenta cargar una imagen. Devuelve None si no existe."""
            try:
                img = pygame.image.load(path).convert_alpha()
                return img
            except Exception:
                return None   # archivo no encontrado → dibujo geométrico

        t = {}

        # ── PISOS ─────────────────────────────────────────────────
        # Se tesela en toda el área interior del cuarto.
        t["floor_antro"]  = None   # TODO: t["floor_antro"]  = load("piso_antro.png")
        t["floor_cata"]   = None   # TODO: t["floor_cata"]   = load("piso_catacumbas.png")

        # ── PAREDES (bloque individual, se repite por cada Rect) ──
        # Se escala al tamaño del rect de cada pared.
        # ── PAREDES EXTERIORES (64×64 px, se tesela) ─────────────
        t["wall_antro"]     = load("wall_antro.png")
        t["wall_cata"]      = load("wall_cata.png")
        # ── OBSTÁCULOS INTERIORES (columnas, bloques — 64×64 px) ──
        # Si no existe el archivo, usa la misma textura de wall.
        t["obstacle_antro"] = load("obstacle_antro.png")
        t["obstacle_cata"]  = load("obstacle_cata.png")

        # ── JUGADOR — 8 DIRECCIONES ──────────────────────────────
        # Nombra tus archivos exactamente así y ponlos en la misma carpeta:
        #
        #   player_up.png        player_down.png
        #   player_left.png      player_right.png
        #   player_upleft.png    player_upright.png
        #   player_downleft.png  player_downright.png
        #
        # Si un archivo no existe, esa dirección usará el círculo naranja.
        # ── ESCUDO ────────────────────────────────────────────────
        # El escudo es un arco de 90°. La imagen debe ser un arco/media luna
        # orientado hacia la DERECHA (→) con fondo transparente.
        # El juego lo recorta a un arco y lo rota hacia el mouse automáticamente.
        #
        # Archivo: shield.png
        # Tamaño:  128×128 px  (cuadrado, fondo transparente)
        # Diseño:  arco o media luna en el lado DERECHO del canvas,
        #          centrado verticalmente. El centro del canvas = centro del jugador.
        #
        # Ejemplo de posición del arco dentro del canvas de 128×128:
        #   El arco va de x≈64 hacia x≈128, centrado en y=64
        #   Grosor sugerido: 12-16px
        #
        t["shield"] = load("shield.png")

        # ── JUGADOR — 8 DIRECCIONES ──────────────────────────────
        # Nombra tus archivos exactamente así y ponlos en la misma carpeta:
        #
        #   player_up.png        player_down.png
        #   player_left.png      player_right.png
        #   player_upleft.png    player_upright.png
        #   player_downleft.png  player_downright.png
        #
        # Si un archivo no existe, esa dirección usará el círculo naranja.
        t["player_up"]        = load("player_up.png")
        t["player_down"]      = load("player_down.png")
        t["player_left"]      = load("player_left.png")
        t["player_right"]     = load("player_right.png")
        t["player_upleft"]    = load("player_upleft.png")
        t["player_upright"]   = load("player_upright.png")
        t["player_downleft"]  = load("player_downleft.png")
        t["player_downright"] = load("player_downright.png")

        # ══════════════════════════════════════════════════════════
        # ── ENEMIGOS — 8 DIRECCIONES (igual que el jugador) ──────
        # Formato del nombre: PREFIJO_DIRECCIÓN.png
        # Direcciones: up  down  left  right  upleft  upright  downleft  downright
        #
        # Si solo pones algunas direcciones, el juego usa el círculo
        # de neón para las que falten.
        #
        # Tamaño recomendado: 48×48 px, fondo transparente (PNG-32)
        # ══════════════════════════════════════════════════════════

        # ── Momia de Guanajuato ──
        for _d in ["up","down","left","right","upleft","upright","downleft","downright"]:
            t[f"momia_{_d}"] = load(f"momia_{_d}.png")

        # ── Zombi ──
        for _d in ["up","down","left","right","upleft","upright","downleft","downright"]:
            t[f"zombi_{_d}"] = load(f"zombi_{_d}.png")

        # ── Pescado Mutante ──
        for _d in ["up","down","left","right","upleft","upright","downleft","downright"]:
            t[f"pescado_{_d}"] = load(f"pescado_{_d}.png")

        # ── Esqueleto Rumbero ──
        for _d in ["up","down","left","right","upleft","upright","downleft","downright"]:
            t[f"esqueleto_{_d}"] = load(f"esqueleto_{_d}.png")

        # ── Cthulhu DJ Sonidero (jefe — un solo sprite, no tiene 8 dirs) ──
        t["cthulhu"]      = load("cthulhu.png")      # 96×96 px

        # ── La Momia Mayor (jefe — un solo sprite) ──
        t["momia_mayor"]  = load("momia_mayor.png")  # 96×96 px

        return t

    def _draw_sprite(self, surface, tex_key, sx, sy, w, h, angle=0):
        """
        Dibuja una textura escalada y rotada en coordenadas de pantalla.
        Si la textura es None, no dibuja nada (el caller usa dibujos geométricos).
        w, h: tamaño en PIXELS DE PANTALLA (ya con zoom aplicado).
        angle: rotación en grados (0 = sin rotar).
        """
        img = self.tex.get(tex_key)
        if img is None:
            return False   # señal al caller: usa el dibujo geométrico
        scaled = pygame.transform.scale(img, (max(1,w), max(1,h)))
        if angle != 0:
            scaled = pygame.transform.rotate(scaled, -angle)
            # Re-centrar tras la rotación
            rect = scaled.get_rect(center=(sx, sy))
            surface.blit(scaled, rect.topleft)
        else:
            surface.blit(scaled, (sx - w//2, sy - h//2))
        return True   # textura dibujada con éxito

    # ── Carga de cuarto ──
    def load_room(self, room_idx, from_door=None):
        room = self.rooms[room_idx]
        self.current_room  = room_idx
        self.walls         = room["walls"]
        self.bg_color      = room["bg_color"]
        self.grid_color    = room.get("grid_color", (20, 20, 20))

        if self.player is None:
            self.player = Player(room["spawn_x"], room["spawn_y"])
        else:
            # Posicionar al jugador en el lado correcto según la puerta de entrada
            if from_door:
                side = from_door.side
                ox  = room.get("world_ox", 0)
                oy  = room.get("world_oy", 0)
                # Spawn bien dentro del cuarto (200px desde la pared)
                # y centrado en el hueco de la puerta
                inset = WALL_T + 200
                if side == 'right':   px,py = ox + inset,       oy + RH//2
                elif side == 'left':  px,py = ox + RW - inset,  oy + RH//2
                elif side == 'bottom':px,py = ox + RW//2,       oy + inset
                else:                 px,py = ox + RW//2,       oy + RH - inset
                self.player.x = float(px)
                self.player.y = float(py)
            else:
                self.player.x = float(room["spawn_x"])
                self.player.y = float(room["spawn_y"])
            self.player.hp = max(1, self.player.hp)

        self.player.floating_texts = self.floating_texts

        self.bullets       = []
        self.coins         = []
        self.items         = []
        self.chests        = []
        self.particles     = []

        # ── Cuartos ya limpiados: no re-spawnear enemigos ──
        if room.get("cleared", False) or room.get("is_start", False):
            self.enemies       = []
            self.chest_spawned = True   # no spawnear cofre de nuevo
        else:
            self.enemies       = room["spawn_enemies"](room)
            self.chest_spawned = False

        # ── Clonar puertas ──
        self.doors = []
        for d in room["doors"]:
            nd = Door(d.x, d.y, d.side, d.target_room)
            # Cuarto inicio o ya limpiado → puertas abiertas
            if room.get("is_start", False) or room.get("cleared", False):
                nd.open = True
            self.doors.append(nd)

    def restart_current_room(self):
        """Reinicio instantáneo (tecla R): resetea al jugador y re-spawnea enemigos."""
        room = self.rooms[self.current_room]
        self.player.hp          = PLAYER_MAX_HP
        self.player.dead        = False
        self.player.invincible_timer = 0
        self.player.x           = float(room["spawn_x"])
        self.player.y           = float(room["spawn_y"])
        self.enemies            = room["spawn_enemies"](room)
        self.bullets            = []
        self.coins              = []
        self.items              = []
        self.chests             = []
        self.particles          = []  # limpiar sangre al reiniciar
        self.floating_texts     = []
        self.player.floating_texts = self.floating_texts
        # Re-clonar puertas cerradas al reiniciar
        self.doors = []
        for d in room["doors"]:
            nd = Door(d.x, d.y, d.side, d.target_room)
            if room.get("is_start", False): nd.open = True
            self.doors.append(nd)
        self.chest_spawned      = False
        self.camera.shake_intensity = 0
        self.camera.flash_timer     = 0
        self.estado             = "GAMEPLAY"

    # ── Convertir posición del mouse a coordenadas del mundo ──
    def screen_to_world(self, sx, sy):
        """Pantalla → mundo, inversa exacta de world_to_screen."""
        cx = SCREEN_W / 2
        cy = SCREEN_H / 2
        wx = (sx - cx) / self.camera.zoom + self.camera.focus_x
        wy = (sy - cy) / self.camera.zoom + self.camera.focus_y
        return wx, wy

    # ── Dibujar fondo del cuarto ──
    def draw_background(self):
        # 1. Todo negro (exterior del cuarto y zona HUD)
        self.screen.fill(BLACK)

        # 2. Calcular el rectángulo de pantalla que ocupa el interior del cuarto
        #    (entre las paredes exteriores del cuarto actual)
        room   = self.rooms[self.current_room]
        ox     = room.get("world_ox", 0)
        oy     = room.get("world_oy", 0)
        min_wx = ox + WALL_T
        max_wx = ox + RW - WALL_T
        min_wy = oy + WALL_T
        max_wy = oy + RH - WALL_T

        # Convertir esquinas del cuarto a pantalla
        sx1, sy1 = self.camera.world_to_screen(min_wx, min_wy)
        sx2, sy2 = self.camera.world_to_screen(max_wx, max_wy)
        # Clipear a la zona de juego
        sx1 = max(0, sx1); sy1 = max(0, sy1)
        sx2 = min(GAME_ZONE_W, sx2); sy2 = min(SCREEN_H, sy2)
        if sx2 > sx1 and sy2 > sy1:
            fw, fh = sx2-sx1, sy2-sy1
            # ── TEXTURA DE PISO ──────────────────────────────────────
            # Elige la textura según el acto actual
            floor_key = "floor_antro" if self.acto == 1 else "floor_cata"
            floor_img = self.tex.get(floor_key)
            if floor_img and fw > 0 and fh > 0:
                # Teselar la textura (repetir en X e Y)
                tile_w = floor_img.get_width()
                tile_h = floor_img.get_height()
                for ty in range(sy1, sy2, tile_h):
                    for tx in range(sx1, sx2, tile_w):
                        clip_w = min(tile_w, sx2 - tx)
                        clip_h = min(tile_h, sy2 - ty)
                        src_rect = pygame.Rect(0, 0, clip_w, clip_h)
                        self.screen.blit(floor_img, (tx, ty), src_rect)
            else:
                # ── PISO DISCOTECA — color sólido que pulsa suavemente ──
                # Sin cuadros: el color del piso oscila entre dos tonos
                t = self._disco_tick
                if self.acto == 1:
                    # Antro: oscila entre morado oscuro y morado medio
                    v = int(abs(math.sin(t * 0.015)) * 30)
                    floor_col = (5 + v, 0, 20 + v*2)
                else:
                    # Catacumbas: oscila entre verde muy oscuro y verde tenue
                    v = int(abs(math.sin(t * 0.015)) * 25)
                    floor_col = (0, 8 + v, 2 + v//2)
                pygame.draw.rect(self.screen, floor_col, (sx1, sy1, fw, fh))



    def draw_walls(self):
        # ══════════════════════════════════════════════════════════
        # TEXTURAS DE PAREDES Y OBSTÁCULOS
        # ──────────────────────────────────────────────────────────
        # El sistema distingue DOS tipos de rectángulos:
        #
        #   PAREDES EXTERIORES (w >= RW*0.8 o h >= RH*0.8, o son delgadas)
        #     → Usan wall_antro.png / wall_cata.png
        #     → Se dibujan con marco decorativo (borde oscuro + línea neón)
        #
        #   OBSTÁCULOS INTERIORES (bloques, columnas, etc.)
        #     → Usan obstacle_antro.png / obstacle_cata.png
        #     → Si no hay textura, color sólido con borde neón
        #
        # Especificaciones:
        #   wall_antro.png / wall_cata.png      → 64×64 px, se tesela
        #   obstacle_antro.png / obstacle_cata.png → 64×64 px, se tesela
        #
        # Para activarlas descomenta en _load_textures:
        #   t["wall_antro"]     = load("wall_antro.png")
        #   t["wall_cata"]      = load("wall_cata.png")
        #   t["obstacle_antro"] = load("obstacle_antro.png")
        #   t["obstacle_cata"]  = load("obstacle_cata.png")
        # ══════════════════════════════════════════════════════════

        wall_key = "wall_antro"     if self.acto == 1 else "wall_cata"
        obs_key  = "obstacle_antro" if self.acto == 1 else "obstacle_cata"
        wall_img = self.tex.get(wall_key)
        obs_img  = self.tex.get(obs_key)
        z = self.camera.zoom

        # Colores base según acto (fallback sin textura)
        if self.acto == 1:
            wall_fill   = (28, 18, 48)    # morado muy oscuro
            wall_border = (70, 40, 110)   # morado medio
            wall_glow   = (120, 60, 200)  # neón morado
            obs_fill    = (35, 22, 58)
            obs_border  = (90, 55, 140)
            obs_glow    = (160, 80, 255)
        else:
            wall_fill   = (8,  28, 12)
            wall_border = (20, 70, 30)
            wall_glow   = (40, 180, 60)
            obs_fill    = (10, 35, 15)
            obs_border  = (25, 90, 40)
            obs_glow    = (60, 220, 80)

        def draw_tiled(surf, img, sx, sy, rw, rh):
            """Tesela img dentro del rect (sx,sy,rw,rh)."""
            tw, th = img.get_width(), img.get_height()
            clip = pygame.Rect(sx, sy, rw, rh)
            surf.set_clip(clip)
            for ty in range(sy, sy + rh, th):
                for tx in range(sx, sx + rw, tw):
                    surf.blit(img, (tx, ty))
            surf.set_clip(None)

        def draw_wall_styled(sx, sy, rw, rh, img, fill, border, glow):
            """
            Dibuja un bloque de pared con:
              1. Fill / textura interior
              2. Bordes oscuros (sombra lateral izquierda y superior)
              3. Borde neón interior (línea fina de brillo)
            """
            if rw < 2 or rh < 2:
                return
            b = max(1, int(4 * z))   # grosor del borde decorativo

            # ── 1. Fondo interior ──
            if img:
                draw_tiled(self.screen, img, sx, sy, rw, rh)
            else:
                pygame.draw.rect(self.screen, fill, (sx, sy, rw, rh))

            # ── 2. Sombra/marco oscuro (izquierda + arriba más oscuro) ──
            dark = (max(0,fill[0]-15), max(0,fill[1]-10), max(0,fill[2]-20))
            pygame.draw.rect(self.screen, dark, (sx, sy, rw, b))          # top
            pygame.draw.rect(self.screen, dark, (sx, sy, b, rh))          # left
            pygame.draw.rect(self.screen, border, (sx, sy+rh-b, rw, b))  # bottom
            pygame.draw.rect(self.screen, border, (sx+rw-b, sy, b, rh))  # right

            # ── 3. Línea de brillo neón interior (1px adentro del borde) ──
            inset = b
            if rw > inset*2 and rh > inset*2:
                pygame.draw.rect(self.screen, glow,
                                 (sx+inset, sy+inset, rw-inset*2, rh-inset*2), 1)

        for wall in self.walls:
            sx, sy = self.camera.world_to_screen(wall.x, wall.y)
            rw = max(2, int(wall.w * z))
            rh = max(2, int(wall.h * z))

            # Distinguir pared exterior de obstáculo interior
            # Las paredes exteriores son muy delgadas (WALL_T=40px) o muy largas
            is_outer = (wall.w == WALL_T or wall.h == WALL_T or
                        wall.w >= int(RW * 0.7) or wall.h >= int(RH * 0.7))

            if is_outer:
                draw_wall_styled(sx, sy, rw, rh, wall_img, wall_fill, wall_border, wall_glow)
            else:
                draw_wall_styled(sx, sy, rw, rh, obs_img or wall_img,
                                 obs_fill, obs_border, obs_glow)

    # ══════════════════════════════════════════
    #  BUCLE PRINCIPAL
    # ══════════════════════════════════════════
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._handle_events()

            if self.estado == "MENU":
                self._update_menu()
                self._draw_menu()

            elif self.estado == "GAMEPLAY":
                self._update_gameplay()
                self._draw_gameplay()

            elif self.estado == "PAUSED":
                self._draw_gameplay()
                self._draw_pause()

            elif self.estado == "ACT_TRANSITION":
                self._update_act_trans()
                self._draw_gameplay()
                self._draw_act_trans()

            elif self.estado == "GAME_OVER":
                self._draw_game_over()

            elif self.estado == "VICTORY":
                self._draw_victory()

            pygame.display.flip()

    # ── Eventos ──
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.estado == "GAMEPLAY":
                        self.estado = "PAUSED"
                    elif self.estado == "PAUSED":
                        self.estado = "GAMEPLAY"
                    elif self.estado == "MENU":
                        pygame.quit()
                        sys.exit()
                if event.key == pygame.K_p:
                    if self.estado == "GAMEPLAY":
                        self.estado = "PAUSED"
                    elif self.estado == "PAUSED":
                        self.estado = "GAMEPLAY" 
                if event.key == pygame.K_r:
                    if self.estado in ("GAMEPLAY", "GAME_OVER", "PAUSED"):
                        if self.player:
                            self.restart_current_room()
                        else:
                            self.start_game()
                # ── MENÚ: Iniciar juego con ENTER / ESPACIO ──
                if self.estado == "MENU":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.start_game()

    def start_game(self):
        """Inicia una nueva run: genera el mapa procedimental y resetea todo."""
        self._tutorial_alpha = 255
        self._bg_cache = (None, None)
        self.rooms          = generate_map()
        self.player         = None
        self.particles      = []
        self.floating_texts = []
        self.run_number     = getattr(self, 'run_number', 0) + 1
        self.load_room(0)
        self.estado = "GAMEPLAY"

    # ══════════════════════════════════════════
    #  MENÚ PRINCIPAL
    # ══════════════════════════════════════════
    def _update_menu(self):
        self.menu_bg_tick += 1

    def _draw_menu(self):
        """
        ╔═════════════════════════════════════════════════╗
        ║  ESPACIO PARA TU MENÚ ACTUAL                    ║
        ║  Al presionar el botón de inicio, ejecuta:      ║
        ║      self.start_game()                          ║
        ║  o cambia directamente:                         ║
        ║      self.estado = "GAMEPLAY"                   ║
        ╚═════════════════════════════════════════════════╝

        Por defecto se muestra un menú funcional neón.
        Reemplaza todo el contenido de este método con tu menú.
        """
        t = self.menu_bg_tick * 0.02
        self.screen.fill(BLACK)

        # Fondo psicodélico animado
        for i in range(0, SCREEN_W, 80):
            col_r = int(abs(math.sin(t + i * 0.01)) * 60)
            col_b = int(abs(math.cos(t + i * 0.015)) * 120)
            pygame.draw.line(self.screen, (col_r, 0, col_b), (i, 0), (i, SCREEN_H), 2)

        # Estrellas
        for (sx, sy, sr, phase) in self.stars:
            bright = int(abs(math.sin(t * 2 + phase * 6)) * 200 + 55)
            pygame.draw.circle(self.screen, (bright, bright, bright), (sx, sy), sr)

        # Título
        title1 = self.font_xl.render("MACACO", True, NEON_ORANGE)
        title2 = self.font_xl.render("vs. LAS MOMIAS", True, NEON_PINK)
        title3 = self.font_lg.render("DE GUANAJUATO", True, NEON_CYAN)
        cx = SCREEN_W // 2
        self.screen.blit(title1, (cx - title1.get_width()//2, 120))
        self.screen.blit(title2, (cx - title2.get_width()//2, 210))
        self.screen.blit(title3, (cx - title3.get_width()//2, 300))

        # Subtítulo
        sub = self.font_md.render("[ BULLET HELL INVERTIDO ]", True, NEON_YELLOW)
        self.screen.blit(sub, (cx - sub.get_width()//2, 360))

        # Botón Iniciar (parpadeante)
        if int(t * 2) % 2 == 0:
            btn = self.font_lg.render(">> ENTER / ESPACIO para JUGAR <<", True, WHITE)
            self.screen.blit(btn, (cx - btn.get_width()//2, 460))

        # Controles
        controls = [
            "MOUSE  = Mover al Macaco + Apuntar Escudo",
            "ESCUDO = Refleja balas enemigas automáticamente",
            "R      = Reiniciar sala",
            "ESC    = Pausar / Salir (en menú)",
        ]
        for i, line in enumerate(controls):
            ct = self.font_sm.render(line, True, (150, 150, 200))
            self.screen.blit(ct, (cx - ct.get_width()//2, 560 + i * 20))

    # ══════════════════════════════════════════
    #  GAMEPLAY – UPDATE
    # ══════════════════════════════════════════
    def _update_gameplay(self):
        mouse_sx, mouse_sy = pygame.mouse.get_pos()
        mouse_wx, mouse_wy = self.screen_to_world(mouse_sx, mouse_sy)

        # ── Jugador ──
        self.player.update(mouse_wx, mouse_wy, self.walls)

        # ── Enemigos ──
        for enemy in self.enemies:
            enemy.update(self.player, self.bullets, self.walls)

        # ── Proyectiles ──
        for b in self.bullets:
            b.update(self.walls, self.player if b.owner == "enemy" else None)

        # ── Colisión escudo / jugador con balas ──
        self.player.check_bullet_collision(
            self.bullets, self.particles, self.floating_texts, self.camera)

        # ── Balas del jugador que golpean enemigos ──
        for b in self.bullets:
            if b.dead or b.owner != "player": continue
            for enemy in self.enemies:
                if enemy.dead: continue
                dx = b.x - enemy.x
                dy = b.y - enemy.y
                if math.hypot(dx, dy) < enemy.r + b.r:
                    # Explosión especial de proyectil gigante rebotado
                    if b.is_giant:
                        for nearby in self.enemies:
                            if math.hypot(nearby.x - b.x, nearby.y - b.y) < 80:
                                nearby.take_damage(1, self.particles,
                                                   self.floating_texts, self.camera)
                        self.camera.shake(10)
                    else:
                        enemy.take_damage(1, self.particles,
                                          self.floating_texts, self.camera)
                    b.dead = True
                    # XP y monedas al matar
                    if enemy.dead:
                        self.player.gain_xp(enemy.xp)
                        for _ in range(random.randint(1, 4)):
                            self.coins.append(Coin(enemy.x + random.randint(-20,20),
                                                   enemy.y + random.randint(-20,20)))

        # ── Monedas ──
        for c in self.coins:
            c.update(self.player)

        # ── Ítems del cofre ──
        for it in self.items:
            it.update(self.player)

        # ── Cofres ──
        for chest in self.chests:
            chest.update(self.player, self.items, self.coins,
                         self.camera, self.floating_texts)

        # ── Puertas ──
        for door in self.doors:
            if door.player_crosses(self.player):
                # Calcular el lado opuesto de entrada
                opp = {'right':'left','left':'right','top':'bottom','bottom':'top'}
                fake_door = type('D', (), {'side': opp.get(door.side, door.side)})()
                self.load_room(door.target_room, from_door=fake_door)
                return   # recargar evita procesar el frame viejo

        # ── ¿Sala limpia? Spawnar cofre ──
        all_dead = all(e.dead for e in self.enemies)
        if all_dead and not self.chest_spawned and len(self.enemies) > 0:
            self.chest_spawned = True
            # Marcar cuarto como limpiado (no re-spawnear al volver)
            self.rooms[self.current_room]["cleared"] = True
            # Abrir puertas
            for door in self.doors:
                door.open = True
                self.floating_texts.append(
                    FloatingText("¡PUERTA ABIERTA!", door.x, door.y - 40,
                                 NEON_GREEN, 22, 80))
            # Cofre en el centro aproximado del mapa
            cx_world = sum(w.centerx for w in self.walls) / max(1, len(self.walls))
            cy_world = sum(w.centery for w in self.walls) / max(1, len(self.walls))
            # Ajustar a posición más "visible"
            cx_world = max(200, min(cx_world, 1600))
            cy_world = max(200, min(cy_world, 600))
            self.chests.append(Chest(cx_world, cy_world))
            self.floating_texts.append(
                FloatingText("¡COFRE APARECIÓ!", cx_world, cy_world - 60,
                             NEON_YELLOW, 24, 100))

        # ── Textos flotantes ──
        for ft in self.floating_texts:
            ft.update()

        # ── Partículas ── (máx 300 para evitar lag)
        for p in self.particles:
            p.update()
        if len(self.particles) > 300:
            self.particles = self.particles[-300:]

        # ── Cámara ──
        self.camera.update(self.player.x, self.player.y)
        if not self.camera.free_pan and self.camera.target_zoom != 1.0:
            if abs(self.camera.zoom - 1.0) < 0.05:
                self.camera.reset_zoom()

        # ── Limpiar muertos ──
        self.enemies       = [e for e in self.enemies       if not e.dead]
        self.bullets       = [b for b in self.bullets       if not b.dead]
        self.coins         = [c for c in self.coins         if not c.dead]
        self.items         = [it for it in self.items       if not it.dead]
        self.chests        = [ch for ch in self.chests      if not ch.dead]
        self.floating_texts= [ft for ft in self.floating_texts if not ft.dead]

        # ── Game Over ──
        if self.player.dead:
            self.camera.flash_timer = 0
            self.camera.flash_alpha = 0
            self.estado = "GAME_OVER"

        # ── Victoria: derrotó al jefe (último cuarto del camino roguelite) ──
        if self.rooms:
            last_room = self.rooms[-1]
            if (self.current_room == len(self.rooms) - 1 and
                    last_room.get("is_boss", False) and
                    self.chest_spawned and len(self.enemies) == 0):
                self.camera.flash_timer = 0
                self.camera.flash_alpha = 0
                if self.acto==1:
                    self.estado="ACT_TRANSITION"; self._act_trans_timer=180
                else:
                    self.estado="VICTORY"

    # ══════════════════════════════════════════
    #  TUTORIAL CUARTO 0
    # ══════════════════════════════════════════
    def _draw_tutorial(self):
        """Panel de controles en cuarto 0. Se desvanece al moverse."""
        if self.current_room != 0 or self._tutorial_alpha <= 0:
            return
        room = self.rooms[0]
        px, py = self.player.x, self.player.y
        dist = math.hypot(px - room["spawn_x"], py - room["spawn_y"])
        if dist > 80:
            self._tutorial_alpha = max(0, self._tutorial_alpha - 4)
        if self._tutorial_alpha <= 0:
            return

        alpha = self._tutorial_alpha
        cx = GAME_ZONE_W // 2
        pw, ph = 520, 290
        panel_x = cx - pw // 2
        panel_y = SCREEN_H // 2 - ph // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((0, 0, 0, min(200, alpha)))
        pygame.draw.rect(panel, (*NEON_PURPLE, min(255, alpha)), (0, 0, pw, ph), 2)
        pygame.draw.rect(panel, (*NEON_CYAN, min(80, alpha)),    (2, 2, pw-4, ph-4), 1)
        self.screen.blit(panel, (panel_x, panel_y))

        y = panel_y + 18

        def row(text, size, color, bold=False, center=True):
            nonlocal y
            f = get_font(size, bold=bold)
            s = f.render(text, True, color)
            s.set_alpha(alpha)
            x_pos = cx - s.get_width()//2 if center else panel_x + 28
            self.screen.blit(s, (x_pos, y))
            y += s.get_height() + 5

        row("MACACO VS. LAS MOMIAS", 20, NEON_ORANGE, bold=True)
        y += 3
        pygame.draw.line(self.screen, (*NEON_PURPLE, alpha),
                         (panel_x+20, y), (panel_x+pw-20, y), 1)
        y += 10

        controles = [
            ("MOUSE",  "Mover al Macaco + apuntar el Escudo",  NEON_CYAN),
            ("ESCUDO", "Refleja balas enemigas de vuelta",      NEON_GREEN),
            ("MATA",   "Elimina todos los enemigos del cuarto", NEON_YELLOW),
            ("COFRE",  "Recoge el cofre para subir de stats",   NEON_PINK),
            ("PUERTA", "Cruza la puerta para avanzar",          WHITE),
        ]
        for key, desc, col in controles:
            fk = get_font(13, bold=True)
            fd = get_font(13)
            ks = fk.render(f"[{key}]", True, col)
            ds = fd.render(desc, True, (200, 200, 200))
            ks.set_alpha(alpha); ds.set_alpha(alpha)
            self.screen.blit(ks, (panel_x + 28, y))
            self.screen.blit(ds, (panel_x + 28 + ks.get_width() + 10, y))
            y += ks.get_height() + 4

        y += 4
        pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 180 + 50)
        row("Muevete para empezar", 13, (pulse, pulse, 60))

    # ══════════════════════════════════════════
    #  GAMEPLAY – DRAW
    # ══════════════════════════════════════════
    def _draw_gameplay(self):
        # Clipear zona de juego — nada se pinta sobre el HUD lateral
        self.screen.set_clip(pygame.Rect(0, 0, GAME_ZONE_W, SCREEN_H))
        self.draw_background()
        self.draw_walls()

        # Partículas (sangre estática – debajo de todo)
        for p in self.particles:
            p.draw(self.screen, self.camera)

        # Monedas
        for c in self.coins:
            c.draw(self.screen, self.camera)

        # Ítems
        for it in self.items:
            it.draw(self.screen, self.camera)

        # Cofres
        for ch in self.chests:
            ch.draw(self.screen, self.camera)

        # Puertas
        for door in self.doors:
            door.draw(self.screen, self.camera)

        # Proyectiles
        for b in self.bullets:
            b.draw(self.screen, self.camera)

        # Enemigos — con referencia al game para texturas y posición del jugador
        self.camera._game = self
        for e in self.enemies:
            e.draw(self.screen, self.camera)
        self.camera._game = None

        # Jugador — pasar referencia al Game para acceder a texturas
        self.camera._game = self
        self.player.draw(self.screen, self.camera)
        self.camera._game = None

        # Textos flotantes
        for ft in self.floating_texts:
            ft.draw(self.screen, self.camera)

        # Cerrar clip antes del flash y HUD
        self.screen.set_clip(None)

        # Flash de pantalla (encima de todo el gameplay, solo en zona de juego)
        self.camera.draw_flash_zone(self.screen, GAME_ZONE_W)

        # ── FILTRO SCANLINE CRT ──
        if self._scanline_surf is None:
            self._scanline_surf = pygame.Surface((GAME_ZONE_W, SCREEN_H), pygame.SRCALPHA)
            for scan_y in range(0, SCREEN_H, 3):
                pygame.draw.line(self._scanline_surf, (0,0,0,50),
                                 (0, scan_y), (GAME_ZONE_W, scan_y), 1)
        self.screen.blit(self._scanline_surf, (0, 0))

        # ── Tutorial (solo cuarto 0) ──
        self._draw_tutorial()

        # ── HUD lateral ──
        room_name = self.rooms[self.current_room].get("name", "")
        acto_str  = f"ACTO {self.acto}: " + ("El Antro" if self.acto==1 else "Las Catacumbas")
        self.player.draw_hud(self.screen, self.font_sm, self.font_md,
                             room_name=room_name, acto_name=acto_str, font_lg=self.font_lg)
        self.player.draw_minimap(self.screen, self.rooms,
                                 self.current_room, self.font_sm)

    # ══════════════════════════════════════════
    #  PAUSA
    # ══════════════════════════════════════════
    def _update_act_trans(self):
        self._act_trans_timer -= 1
        if self._act_trans_timer <= 0:
            self.start_act2()

    def _draw_act_trans(self):
        t=self._act_trans_timer; alpha=min(200,int((180-t)/180*200))
        ov=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        ov.fill((0,8,2,alpha)); self.screen.blit(ov,(0,0))
        if t<150:
            cx=GAME_ZONE_W//2; tk=pygame.time.get_ticks()*0.001
            pls=int(abs(math.sin(tk*3))*30)
            t1=self.font_xl.render("ACTO 2",True,(80+pls,255,80+pls))
            t2=self.font_lg.render("LAS CATACUMBAS",True,NEON_GREEN)
            t3=self.font_md.render("Las momias despiertan...",True,(120,200,120))
            self.screen.blit(t1,(cx-t1.get_width()//2,190))
            self.screen.blit(t2,(cx-t2.get_width()//2,300))
            self.screen.blit(t3,(cx-t3.get_width()//2,370))

    def _draw_pause(self):
        # Overlay semitransparente
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cx = GAME_ZONE_W // 2

        # Título PAUSA
        t = pygame.time.get_ticks() * 0.001
        pulse = int(abs(math.sin(t * 2)) * 40)
        title = self.font_xl.render("PAUSA", True, (255, pulse*2, pulse))
        self.screen.blit(title, (cx - title.get_width()//2, 220))

        # Línea decorativa
        pygame.draw.line(self.screen, NEON_PURPLE,
                         (cx - 200, 310), (cx + 200, 310), 2)

        # Opciones
        opts = [
            ("ESC  /  P",  "Continuar",  NEON_GREEN),
            ("R",          "Reiniciar sala", NEON_YELLOW),
            ("SALIR",      "Cierra el juego", (180,180,180)),
        ]
        for i, (key, desc, col) in enumerate(opts):
            k_img = self.font_md.render(f"[ {key} ]", True, col)
            d_img = self.font_sm.render(desc, True, (200, 200, 200))
            y = 340 + i * 60
            self.screen.blit(k_img, (cx - k_img.get_width()//2, y))
            self.screen.blit(d_img, (cx - d_img.get_width()//2, y + k_img.get_height() + 2))

        # Stats rápidas del jugador
        if self.player:
            pygame.draw.line(self.screen, NEON_PURPLE,
                             (cx - 200, 530), (cx + 200, 530), 1)
            stats = [
                f"Nivel: {self.player.level}    XP: {self.player.xp}/{self.player.xp_to_level}",
                f"Monedas: ${self.player.coins}    HP: {self.player.hp}/{self.player.max_hp}",
                f"Daño: {self.player.damage:.2f}x    Defensa: {self.player.defense:.2f}s",
                f"Velocidad: {self.player.speed:.1f}    Escudo: r={self.player.shield_radius}",
            ]
            for i, line in enumerate(stats):
                s = self.font_sm.render(line, True, (160, 160, 200))
                self.screen.blit(s, (cx - s.get_width()//2, 545 + i * 20))

    # ══════════════════════════════════════════
    #  GAME OVER
    # ══════════════════════════════════════════
    def _draw_game_over(self):
        self.screen.fill((5, 0, 0))
        t = pygame.time.get_ticks() * 0.001
        for i in range(0, SCREEN_H, 40):
            col = int(abs(math.sin(t + i*0.05)) * 60)
            pygame.draw.line(self.screen, (col, 0, 0), (0, i), (SCREEN_W, i), 1)

        go  = self.font_xl.render("GAME OVER", True, BLOOD_RED)
        sub = self.font_lg.render("Presiona R para reintentar", True, NEON_PINK)
        coins_txt = self.font_md.render(
            f"Monedas recolectadas: {self.player.coins if self.player else 0}",
            True, NEON_YELLOW)
        cx = SCREEN_W // 2
        self.screen.blit(go,  (cx - go.get_width()//2, 220))
        self.screen.blit(sub, (cx - sub.get_width()//2, 340))
        self.screen.blit(coins_txt, (cx - coins_txt.get_width()//2, 420))

    # ══════════════════════════════════════════
    #  VICTORIA
    # ══════════════════════════════════════════
    def _draw_victory(self):
        self.screen.fill((0, 5, 20))
        t = pygame.time.get_ticks() * 0.001
        for i in range(0, SCREEN_W, 30):
            col_r = int(abs(math.sin(t + i*0.02)) * 200)
            col_g = int(abs(math.cos(t + i*0.025)) * 200)
            pygame.draw.line(self.screen, (col_r, col_g, 100), (i, 0), (i, SCREEN_H), 1)

        vc  = self.font_xl.render("¡VICTORIA!", True, NEON_YELLOW)
        sub = self.font_lg.render("¡El Macaco limpia la ciudad!", True, NEON_GREEN)
        coins_txt = self.font_md.render(
            f"Monedas totales: {self.player.coins if self.player else 0}",
            True, NEON_CYAN)
        cx = SCREEN_W // 2
        self.screen.blit(vc,  (cx - vc.get_width()//2, 200))
        self.screen.blit(sub, (cx - sub.get_width()//2, 320))
        self.screen.blit(coins_txt, (cx - coins_txt.get_width()//2, 420))
        hint = self.font_md.render("Presiona R para jugar de nuevo", True, WHITE)
        self.screen.blit(hint, (cx - hint.get_width()//2, 520))


# ══════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════
if __name__ == "__main__":
    game = Game()
    game.run()

