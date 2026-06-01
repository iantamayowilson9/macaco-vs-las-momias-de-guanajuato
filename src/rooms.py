"""
Sistema roguelite:
  plantillas de cuartos, layouts por acto, generación procedimental.
"""
import pygame
import math
import random
from src.constants import *
from src.font import get_font
from src.door import Door
from src.enemies import Momia, Zombi, PescadoMutante, EsqueletoRumbero, CthulhuDJ

#  SISTEMA ROGUELITE — CUARTOS DEFINIDOS A MANO + GENERADOR ALEATORIO
#
#  Cada "plantilla" es un dict con:
#    walls        : lista de pygame.Rect en coordenadas LOCALES (ox=0, oy=0)
#    enemy_slots  : lista de (x,y) locales donde pueden spawnear enemigos
#    spawn_local  : (x,y) local del spawn del jugador
#    w, h         : ancho y alto del cuarto en px
#
#  El generador elige plantillas al azar, las coloca en el mundo
#  trasladando sus coords locales al offset (world_ox, world_oy),
#  abre huecos en las paredes exteriores según las conexiones del
#  camino roguelite, y crea las Doors correspondientes.
# ══════════════════════════════════════════════════════════════════

SCENARIO_THEMES = [
    {"name": "El Antro",          "bg": (5,0,20),  "grid": (30,0,60)},
    {"name": "Las Catacumbas",    "bg": (0,5,0),   "grid": (0,40,20)},
    {"name": "Calles de la CDMX", "bg": (5,5,0),   "grid": (40,40,0)},
]

# ── Tamaños de cuarto ──────────────────────────────────────────
RW = 2000   # ancho de cuarto
RH = 800    # alto de cuarto
WALL_T = 40 # grosor de pared exterior
DOOR_GAP = 160  # tamaño del hueco de la puerta en px

# ── Helper: paredes exteriores con hueco opcional ──────────────
def outer_walls(ox, oy, w, h,
                open_left=False, open_right=False,
                open_top=False,  open_bottom=False):
    """
    Genera las 4 paredes exteriores con huecos centrados.
    Las esquinas siempre son sólidas (cuadrado de WALL_T×WALL_T).
    Los huecos solo se abren en la parte MEDIA de cada lado,
    nunca en las esquinas, para que las paredes never se solapen.
    """
    walls = []
    gap = DOOR_GAP
    T   = WALL_T

    # ── Esquinas sólidas (siempre) ──
    walls.append(pygame.Rect(ox,       oy,       T, T))   # TL
    walls.append(pygame.Rect(ox+w-T,   oy,       T, T))   # TR
    walls.append(pygame.Rect(ox,       oy+h-T,   T, T))   # BL
    walls.append(pygame.Rect(ox+w-T,   oy+h-T,   T, T))   # BR

    # ── Techo (sin esquinas) ──
    if open_top:
        cx = ox + w//2
        left_end  = cx - gap//2
        right_start = cx + gap//2
        if left_end > ox + T:
            walls.append(pygame.Rect(ox+T, oy, left_end - ox - T, T))
        if right_start < ox+w-T:
            walls.append(pygame.Rect(right_start, oy, ox+w-T - right_start, T))
    else:
        walls.append(pygame.Rect(ox+T, oy, w - 2*T, T))

    # ── Suelo (sin esquinas) ──
    if open_bottom:
        cx = ox + w//2
        left_end    = cx - gap//2
        right_start = cx + gap//2
        if left_end > ox + T:
            walls.append(pygame.Rect(ox+T, oy+h-T, left_end - ox - T, T))
        if right_start < ox+w-T:
            walls.append(pygame.Rect(right_start, oy+h-T, ox+w-T - right_start, T))
    else:
        walls.append(pygame.Rect(ox+T, oy+h-T, w - 2*T, T))

    # ── Pared izquierda (sin esquinas) ──
    if open_left:
        cy = oy + h//2
        top_end    = cy - gap//2
        bot_start  = cy + gap//2
        if top_end > oy + T:
            walls.append(pygame.Rect(ox, oy+T, T, top_end - oy - T))
        if bot_start < oy+h-T:
            walls.append(pygame.Rect(ox, bot_start, T, oy+h-T - bot_start))
    else:
        walls.append(pygame.Rect(ox, oy+T, T, h - 2*T))

    # ── Pared derecha (sin esquinas) ──
    if open_right:
        cy = oy + h//2
        top_end   = cy - gap//2
        bot_start = cy + gap//2
        if top_end > oy + T:
            walls.append(pygame.Rect(ox+w-T, oy+T, T, top_end - oy - T))
        if bot_start < oy+h-T:
            walls.append(pygame.Rect(ox+w-T, bot_start, T, oy+h-T - bot_start))
    else:
        walls.append(pygame.Rect(ox+w-T, oy+T, T, h - 2*T))

    return walls

# ── Plantillas de cuartos (coordenadas LOCALES) ───────────────
#
# REGLA: todos los obstáculos son bloques SÓLIDOS que van de
# pared a pared (o entre sí) sin dejar huecos menores a 120px.
# Esto evita que enemigos queden atrapados en esquinas de 1px.
#
# RW=2000  RH=800  WALL_T=40
# Interior jugable: x=[40..1960]  y=[40..760]
# Mínimo pasillo: 160px (DOOR_GAP) para que el jugador y enemigos pasen.

def template_tres_islas(ox, oy):
    """
    Tres islas rectangulares sólidas flotando en el centro.
    Todas tocan el techo o el suelo → sin huecos laterales.
    Pasillos de ~200px entre islas y paredes.
    """
    # Isla izquierda: x=240..560, de techo a y=480  (gap inferior=280px)
    # Isla central:  x=760..1240, de y=320 a suelo  (gap superior=280px)
    # Isla derecha:  x=1440..1760, de techo a y=480 (gap inferior=280px)
    walls = [
        # Isla izquierda (cuelga del techo)
        pygame.Rect(ox+240,  oy+WALL_T, 320, 440),
        # Isla central (sube del suelo)
        pygame.Rect(ox+760,  oy+320,    480, 440),
        # Isla derecha (cuelga del techo)
        pygame.Rect(ox+1440, oy+WALL_T, 320, 440),
    ]
    slots = [
        (ox+140, oy+200),(ox+140, oy+600),
        (ox+640, oy+200),(ox+640, oy+600),
        (ox+1000,oy+200),(ox+1100,oy+200),
        (ox+1360,oy+200),(ox+1360,oy+600),
        (ox+1860,oy+200),(ox+1860,oy+600),
        (ox+900, oy+600),(ox+400, oy+680),
    ]
    return walls, slots

def template_corredor_h(ox, oy):
    """
    Dos bloques altos a izquierda y derecha forman un corredor central.
    Van del techo al suelo para que no haya huecos verticales.
    """
    # Bloque izq: x=40..360  (ya es la pared izq + extensión)
    # Bloque der: x=1640..1960
    # Corredor central: x=360..1640 = 1280px de ancho
    # Dentro del corredor, dos pilares sólidos unidos al techo/suelo
    walls = [
        # Bloque sólido izquierdo (rellena desde pared hasta x=360)
        pygame.Rect(ox+WALL_T, oy+WALL_T, 320, 320),   # mitad superior
        pygame.Rect(ox+WALL_T, oy+440,    320, 320),   # mitad inferior
        # Bloque sólido derecho
        pygame.Rect(ox+1640,   oy+WALL_T, 320, 320),
        pygame.Rect(ox+1640,   oy+440,    320, 320),
        # Pilar central izquierdo (techo→centro)
        pygame.Rect(ox+760,    oy+WALL_T, 160, 320),
        # Pilar central derecho (suelo→centro)
        pygame.Rect(ox+1080,   oy+440,    160, 320),
    ]
    slots = [
        (ox+500, oy+200),(ox+500, oy+600),
        (ox+700, oy+600),(ox+1000,oy+200),
        (ox+1300,oy+200),(ox+1300,oy+600),
        (ox+600, oy+400),(ox+1400,oy+400),
        (ox+200, oy+400),(ox+1800,oy+400),
    ]
    return walls, slots

def template_u_invertida(ox, oy):
    """
    Forma de U invertida: dos brazos que bajan desde el techo,
    dejando un canal central libre. Los brazos llegan hasta y=540.
    """
    brazo_w = 280
    brazo_h = 500   # desde techo (y=40) hasta y=540
    walls = [
        # Brazo izquierdo
        pygame.Rect(ox+240,  oy+WALL_T, brazo_w, brazo_h),
        # Brazo derecho
        pygame.Rect(ox+1480, oy+WALL_T, brazo_w, brazo_h),
        # Barra horizontal que los une por arriba (ya son el techo + los brazos)
        # Pilares bajos en el centro (suben del suelo)
        pygame.Rect(ox+760,  oy+440,    200, 320),
        pygame.Rect(ox+1040, oy+440,    200, 320),
    ]
    slots = [
        (ox+140, oy+200),(ox+140, oy+600),
        (ox+580, oy+200),(ox+580, oy+600),
        (ox+1000,oy+200),
        (ox+1420,oy+200),(ox+1420,oy+600),
        (ox+1860,oy+200),(ox+1860,oy+600),
        (ox+600, oy+680),(ox+1400,oy+680),
    ]
    return walls, slots

def template_cuatro_bloques(ox, oy):
    """
    Cuatro bloques en cuadrantes. Cada uno va de pared exterior
    a la mitad del cuarto, con un pasillo en cruz en el centro.
    Pasillo en cruz de 200px de ancho.
    """
    # Cruz: eje H en y=300..500, eje V en x=900..1100
    # Bloque NW: x=40..900, y=40..300
    # Bloque NE: x=1100..1960, y=40..300
    # Bloque SW: x=40..900, y=500..760
    # Bloque SE: x=1100..1960, y=500..760
    walls = [
        pygame.Rect(ox+WALL_T, oy+WALL_T, 860, 260),   # NW
        pygame.Rect(ox+1100,   oy+WALL_T, 860, 260),   # NE
        pygame.Rect(ox+WALL_T, oy+500,    860, 260),   # SW
        pygame.Rect(ox+1100,   oy+500,    860, 260),   # SE
    ]
    slots = [
        (ox+500, oy+200),(ox+200, oy+160),
        (ox+1500,oy+200),(ox+1800,oy+160),
        (ox+500, oy+600),(ox+200, oy+640),
        (ox+1500,oy+600),(ox+1800,oy+640),
        (ox+1000,oy+200),(ox+1000,oy+600),
        (ox+400, oy+400),(ox+1600,oy+400),
    ]
    return walls, slots

def template_arena(ox, oy):
    """
    Arena casi abierta: solo 4 pilares cuadrados macizos de 120×120.
    Sin huecos problemáticos porque los pilares son pequeños y cuadrados.
    """
    walls = [
        pygame.Rect(ox+300,  oy+160, 120, 120),
        pygame.Rect(ox+880,  oy+160, 120, 120),
        pygame.Rect(ox+1460, oy+160, 120, 120),
        pygame.Rect(ox+300,  oy+520, 120, 120),
        pygame.Rect(ox+880,  oy+520, 120, 120),
        pygame.Rect(ox+1460, oy+520, 120, 120),
        pygame.Rect(ox+1780, oy+340, 120, 120),
        pygame.Rect(ox+100,  oy+340, 120, 120),
    ]
    slots = [
        (ox+200, oy+100),(ox+600, oy+100),(ox+1000,oy+100),(ox+1400,oy+100),(ox+1800,oy+100),
        (ox+200, oy+400),(ox+600, oy+400),(ox+1000,oy+400),(ox+1400,oy+400),(ox+1800,oy+400),
        (ox+200, oy+700),(ox+600, oy+700),(ox+1000,oy+700),(ox+1400,oy+700),(ox+1800,oy+700),
    ]
    return walls, slots

ROOM_TEMPLATES = [
    template_tres_islas,
    template_corredor_h,
    template_u_invertida,
    template_cuatro_bloques,
    template_arena,
]

# ── Instanciar un cuarto a partir de una plantilla y conexiones ─
def build_room_instance(tmpl_fn, world_ox, world_oy, connections,
                        theme, depth, is_start, is_boss, boss_cls=None):
    if boss_cls is None:
        from src.enemies import CthulhuDJ
        boss_cls = CthulhuDJ
    """
    Crea el dict completo de un cuarto.
    tmpl_fn: función template_*  (o None para inicio/boss)
    """
    ol = connections.get('left',   False)
    or_= connections.get('right',  False)
    ot = connections.get('top',    False)
    ob = connections.get('bottom', False)

    # Paredes exteriores con huecos
    walls = outer_walls(world_ox, world_oy, RW, RH,
                        open_left=ol, open_right=or_,
                        open_top=ot,  open_bottom=ob)

    enemy_slots = []
    spawn_x = world_ox + RW // 2
    spawn_y = world_oy + RH // 2
    boss_x  = world_ox + RW // 2
    boss_y  = world_oy + RH // 2

    if tmpl_fn is not None:
        interior_walls, slots = tmpl_fn(world_ox, world_oy)
        # ── Filtrar paredes interiores que tapen los huecos de las puertas ──
        # Para cada puerta abierta, definir una zona "sagrada" que no puede
        # ser bloqueada por obstáculos interiores.
        safe_zones = []   # lista de pygame.Rect que deben quedar libres
        margin = DOOR_GAP // 2 + 20   # margen extra de seguridad
        if ol:   # hueco izquierdo: franja vertical en x=[ox..ox+200], y=cy±margin
            cy = world_oy + RH//2
            safe_zones.append(pygame.Rect(world_ox, cy-margin, 200, margin*2))
        if or_:  # hueco derecho
            cy = world_oy + RH//2
            safe_zones.append(pygame.Rect(world_ox+RW-200, cy-margin, 200, margin*2))
        if ot:   # hueco superior
            cx = world_ox + RW//2
            safe_zones.append(pygame.Rect(cx-margin, world_oy, margin*2, 200))
        if ob:   # hueco inferior
            cx = world_ox + RW//2
            safe_zones.append(pygame.Rect(cx-margin, world_oy+RH-200, margin*2, 200))

        filtered = []
        for w_rect in interior_walls:
            blocked = any(w_rect.colliderect(sz) for sz in safe_zones)
            if not blocked:
                filtered.append(w_rect)
        walls += filtered
        enemy_slots = slots

    # ── Función de spawn de enemigos ──
    MAX_ENEMIES = 14   # máximo por cuarto
    _slots    = enemy_slots
    _depth    = depth
    _is_start = is_start
    _is_boss  = is_boss
    _bx, _by  = boss_x, boss_y
    _boss_cls = boss_cls

    def make_enemies(room):
        if _is_start:
            return []
        if _is_boss:
            return [_boss_cls(_bx, _by)]
        # Elegir enemigos: tomar una muestra aleatoria de los slots
        chosen = random.sample(_slots, min(MAX_ENEMIES, len(_slots)))
        result = []
        for ex, ey in chosen:
            if _depth <= 2:
                cls = random.choices([Momia, Zombi, PescadoMutante],
                                     weights=[5, 3, 2])[0]
            elif _depth <= 4:
                cls = random.choices([Momia, Zombi, PescadoMutante, EsqueletoRumbero],
                                     weights=[3, 3, 2, 2])[0]
            else:
                cls = random.choices([Momia, Zombi, PescadoMutante, EsqueletoRumbero],
                                     weights=[2, 2, 3, 3])[0]
            result.append(cls(ex, ey))
        return result

    # ── Posiciones de puertas (centro del hueco) ──
    door_defs = []
    if ol:  door_defs.append(('left',   world_ox,       world_oy + RH//2))
    if or_: door_defs.append(('right',  world_ox + RW,  world_oy + RH//2))
    if ot:  door_defs.append(('top',    world_ox + RW//2, world_oy))
    if ob:  door_defs.append(('bottom', world_ox + RW//2, world_oy + RH))

    return {
        "walls":         walls,
        "spawn_enemies": make_enemies,
        "door_defs":     door_defs,
        "spawn_x":       world_ox + RW//8,   # spawn cerca del borde izquierdo
        "spawn_y":       world_oy + RH//2,
        "name":          theme["name"] + (" – JEFE" if is_boss else (" – Inicio" if is_start else f" – Sala {depth}")),
        "bg_color":      theme["bg"],
        "grid_color":    theme["grid"],
        "is_boss":       is_boss,
        "is_start":      is_start,
        "world_ox":      world_ox,
        "world_oy":      world_oy,
    }


# ══════════════════════════════════════════════════════════════════
#  GENERADOR DE MAPA ROGUELITE
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
#  LAYOUTS FIJOS DE ANTRO — cada layout es una lista de nodos:
#
#  Cada nodo: (grid_x, grid_y, connections_dict, depth_override)
#  grid_x/y se multiplican por ROOM_STRIDE para obtener world_ox/oy.
#  connections: qué lados tienen puerta ('left','right','top','bottom').
#  depth_override: None = usar índice en la lista; int = forzar ese depth.
#
#  El layout define la FORMA del mapa. Cada run elige uno al azar.
#  Cuarto 0 siempre = inicio sin enemigos.
#  Último cuarto siempre = jefe.
# ══════════════════════════════════════════════════════════════════

ROOM_STRIDE = RW + 300   # px de negro entre cuartos (pasillo visual)

# Cada layout es lista de (gx, gy, conexiones)
# El orden define la secuencia de juego (depth = índice).

MAP_LAYOUTS = [

    # ── LAYOUT 1: Pasillo largo horizontal (El Antro clásico) ──────
    # [Inicio] → [Sala] → [Sala] → [Sala] → [Sala] → [JEFE]
    [
        (0, 0, {'right': True}),
        (1, 0, {'left': True, 'right': True}),
        (2, 0, {'left': True, 'right': True}),
        (3, 0, {'left': True, 'right': True}),
        (4, 0, {'left': True, 'right': True}),
        (5, 0, {'left': True}),
    ],

    # ── LAYOUT 2: L horizontal + brazo hacia abajo ──────────────────
    #  [I] → [S] → [S] → [S]
    #                       ↓
    #                      [S]
    #                       ↓
    #                     [JEFE]
    [
        (0, 0, {'right': True}),
        (1, 0, {'left': True, 'right': True}),
        (2, 0, {'left': True, 'right': True}),
        (3, 0, {'left': True, 'bottom': True}),
        (3, 1, {'top': True, 'bottom': True}),
        (3, 2, {'top': True}),
    ],

    # ── LAYOUT 3: Zigzag (sube y baja) ─────────────────────────────
    #  [I] → [S]
    #          ↓
    #        [S] → [S]
    #                ↓
    #              [S] → [JEFE]
    [
        (0, 0, {'right': True}),
        (1, 0, {'left': True, 'bottom': True}),
        (1, 1, {'top': True, 'right': True}),
        (2, 1, {'left': True, 'bottom': True}),
        (2, 2, {'top': True, 'right': True}),
        (3, 2, {'left': True}),
    ],

    # ── LAYOUT 4: T — rama que se divide ───────────────────────────
    #  [I] → [S] → [S] → [S] → [JEFE]
    #                ↓
    #               [S]
    #                ↓
    #               [S]
    [
        (0, 0, {'right': True}),
        (1, 0, {'left': True, 'right': True}),
        (2, 0, {'left': True, 'right': True, 'bottom': True}),
        (3, 0, {'left': True, 'right': True}),
        (4, 0, {'left': True}),
        (2, 1, {'top': True, 'bottom': True}),
        (2, 2, {'top': True}),
    ],

    # ── LAYOUT 5: Cuadrado / loop ───────────────────────────────────
    #  [I] → [S] → [S]
    #  ↑              ↓
    # [S]           [S]
    #  ↑              ↓
    # [S] ← [S] ← [JEFE]
    [
        (0, 0, {'right': True, 'bottom': True}),
        (1, 0, {'left': True, 'right': True}),
        (2, 0, {'left': True, 'bottom': True}),
        (2, 1, {'top': True, 'bottom': True}),
        (2, 2, {'top': True, 'left': True}),
        (1, 2, {'right': True, 'left': True}),
        (0, 2, {'right': True, 'top': True}),
        (0, 1, {'bottom': True, 'top': True}),
    ],

    # ── LAYOUT 6: Cruz (zona VIP central) ──────────────────────────
    #        [S]
    #         ↓
    # [I]→[S]→[S]→[S]→[JEFE]
    #         ↓
    #        [S]
    [
        (0, 1, {'right': True}),
        (1, 1, {'left': True, 'right': True}),
        (2, 1, {'left': True, 'right': True, 'top': True, 'bottom': True}),
        (3, 1, {'left': True, 'right': True}),
        (4, 1, {'left': True}),
        (2, 0, {'bottom': True}),
        (2, 2, {'top': True}),
    ],

    # ── LAYOUT 7: S / serpentina ────────────────────────────────────
    # [I]→[S]→[S]→[S]
    #                ↓
    #        [S]←[S]←[S]
    #         ↓
    #        [S]→[S]→[JEFE]
    [
        (0, 0, {'right': True}),
        (1, 0, {'left': True, 'right': True}),
        (2, 0, {'left': True, 'right': True}),
        (3, 0, {'left': True, 'bottom': True}),
        (3, 1, {'top': True, 'left': True}),
        (2, 1, {'right': True, 'left': True}),
        (1, 1, {'right': True, 'bottom': True}),
        (1, 2, {'top': True, 'right': True}),
        (2, 2, {'left': True, 'right': True}),
        (3, 2, {'left': True}),
    ],

]


# generate_map y generate_act2 definidos abajo


# ══════════════════════════════════════════════



# ══════════════════════════════════════════════════════════════════
#  TEMAS FIJOS POR ACTO
# ══════════════════════════════════════════════════════════════════
THEME_ANTRO = {"name": "El Antro",       "bg": (5,0,20),  "grid": (30,0,60)}
THEME_CATA  = {"name": "Las Catacumbas", "bg": (0,8,2),   "grid": (0,50,20)}

# ══════════════════════════════════════════════════════════════════
#  LAYOUTS POR ACTO
#  Cada layout: lista de (gx, gy, conexiones)
#  depth 0 = inicio vacío, depth último = jefe
# ══════════════════════════════════════════════════════════════════

# ── Acto 1: El Antro (4 salas + Cthulhu DJ) ───────────────────────
LAYOUTS_ANTRO = [
    # Pasillo recto
    [(0,0,{'right':True}),(1,0,{'left':True,'right':True}),
     (2,0,{'left':True,'right':True}),(3,0,{'left':True,'right':True}),
     (4,0,{'left':True})],
    # L + bajada
    [(0,0,{'right':True}),(1,0,{'left':True,'right':True}),
     (2,0,{'left':True,'right':True}),(3,0,{'left':True,'bottom':True}),
     (3,1,{'top':True})],
    # Zigzag
    [(0,0,{'right':True}),(1,0,{'left':True,'bottom':True}),
     (1,1,{'top':True,'right':True}),(2,1,{'left':True,'bottom':True}),
     (2,2,{'top':True})],
    # Cruz VIP
    [(0,1,{'right':True}),(1,1,{'left':True,'right':True,'top':True}),
     (2,1,{'left':True,'right':True}),(3,1,{'left':True}),
     (1,0,{'bottom':True})],
]

# ── Acto 2: Las Catacumbas (4 salas + Momia Mayor) ────────────────
LAYOUTS_CATA = [
    # Serpiente
    [(0,0,{'right':True}),(1,0,{'left':True,'bottom':True}),
     (1,1,{'top':True,'left':True}),(0,1,{'right':True,'bottom':True}),
     (0,2,{'top':True})],
    # T invertida
    [(0,1,{'right':True}),(1,1,{'left':True,'right':True,'top':True}),
     (2,1,{'left':True}),(1,0,{'bottom':True,'right':True}),
     (2,0,{'left':True})],
    # L descendente
    [(0,0,{'bottom':True}),(0,1,{'top':True,'bottom':True}),
     (0,2,{'top':True,'right':True}),(1,2,{'left':True,'right':True}),
     (2,2,{'left':True})],
    # Pasillo vertical
    [(0,0,{'bottom':True}),(0,1,{'top':True,'bottom':True}),
     (0,2,{'top':True,'bottom':True}),(0,3,{'top':True,'bottom':True}),
     (0,4,{'top':True})],
]


def _build_rooms(layout, theme, boss_cls):
    """Construye la lista de cuartos a partir de un layout, tema y clase de jefe."""
    rooms, pos_to_idx = [], {}
    for depth, node in enumerate(layout):
        gx, gy, conn = node
        ox, oy = gx * ROOM_STRIDE, gy * ROOM_STRIDE
        is_start = depth == 0
        is_boss  = depth == len(layout) - 1
        tmpl_fn  = None if (is_start or is_boss) else random.choice(ROOM_TEMPLATES)
        room = build_room_instance(tmpl_fn, ox, oy, conn, theme,
                                   depth, is_start, is_boss,
                                   boss_cls=boss_cls)
        room["path_index"] = depth
        room["grid_pos"]   = (gx, gy)
        rooms.append(room)
        pos_to_idx[(gx, gy)] = depth

    for room in rooms:
        gx, gy = room["grid_pos"]
        door_objs = []
        for (side, wx, wy) in room["door_defs"]:
            if side == 'right':   ngx, ngy = gx+1, gy
            elif side == 'left':  ngx, ngy = gx-1, gy
            elif side == 'bottom':ngx, ngy = gx,   gy+1
            else:                 ngx, ngy = gx,   gy-1
            t = pos_to_idx.get((ngx, ngy))
            if t is not None:
                door_objs.append(Door(wx, wy, side, t))
        room["doors"] = door_objs
    return rooms


def generate_map():
    """Acto 1 — El Antro con Cthulhu DJ como jefe."""
    from src.enemies import CthulhuDJ
    return _build_rooms(random.choice(LAYOUTS_ANTRO), THEME_ANTRO, CthulhuDJ)


def generate_act2():
    """Acto 2 — Las Catacumbas con Momia Mayor como jefe."""
    from src.enemies import MomiaMayor
    return _build_rooms(random.choice(LAYOUTS_CATA), THEME_CATA, MomiaMayor)
