# Macaco vs. Las Momias de Guanajuato

Bullet Hell Invertido — Roguelite — Pygame 1280×720

## Instalación y ejecución

```bash
pip install pygame
cd macaco
python main.py
```

## Controles

| Tecla | Acción |
|-------|--------|
| Mouse | Mover al Macaco + apuntar escudo |
| ESC   | Pausa / Salir (en menú) |
| P     | Pausa / Continuar |
| R     | Reiniciar sala actual |

## Estructura del proyecto

```
macaco/
├── main.py              Punto de entrada
├── src/
│   ├── constants.py     Colores, tamaños, configuración global
│   ├── font.py          Carga de fuente Earthbound.otf
│   ├── camera.py        Cámara con screen shake y zoom
│   ├── effects.py       Textos flotantes y partículas de sangre
│   ├── items.py         Monedas, cofres e ítems de recompensa
│   ├── door.py          Puertas entre cuartos
│   ├── bullet.py        Proyectiles (con trail, homing y rebote)
│   ├── enemies.py       Bestiario: Momia, Zombi, Pescado,
│   │                    Esqueleto, CthulhuDJ, MomiaMayor
│   ├── player.py        El Macaco (escudo, XP, texturas 8-dir)
│   ├── rooms.py         Generador roguelite de mapas
│   └── game.py          Clase Game — bucle, estados, HUD, texturas
└── assets/
    ├── fonts/
    │   └── Earthbound.otf     ← pon tu fuente aquí
    └── sprites/               ← pon tus PNGs aquí
```

## Cómo añadir texturas

Pon los archivos PNG en `assets/sprites/`. Se cargan automáticamente al iniciar.

### Jugador (8 direcciones)
`player_up.png`  `player_down.png`  `player_left.png`  `player_right.png`
`player_upleft.png`  `player_upright.png`  `player_downleft.png`  `player_downright.png`
— **64×64 px**, fondo transparente, apuntando hacia **arriba** como base

### Escudo
`shield.png` — **128×128 px**, arco apuntando hacia la **derecha (→)**

### Enemigos (8 direcciones, mismo patrón)
`momia_up.png` ... `esqueleto_downright.png`
— **48×48 px**, fondo transparente

### Jefes (un solo sprite)
`cthulhu.png`  `momia_mayor.png` — **96×96 px**

### Fondos y paredes
`background_antro.png`  `background_cata.png` — cualquier tamaño, se estira
`wall_antro.png`  `wall_cata.png` — **64×64 px**, se tesela
`obstacle_antro.png`  `obstacle_cata.png` — **64×64 px**, se tesela
`door_open.png`  `door_locked.png` — **64×128 px** sugerido

## Mecánicas

- **Sin disparar**: el jugador REFLEJA balas con el escudo orbital
- **Roguelite**: cada run genera un mapa diferente
- **2 Actos**: El Antro (Cthulhu DJ) → Las Catacumbas (Momia Mayor)
- **4 Ítems**: +HP, +50 monedas, +10% escudo, +10% velocidad
