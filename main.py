"""
╔══════════════════════════════════════════════════════════╗
║   MACACO VS. LAS MOMIAS DE GUANAJUATO                    ║
║   Bullet Hell Invertido | Pygame 1280x720                ║
╠══════════════════════════════════════════════════════════╣
║   Requisitos:  pip install pygame                        ║
║   Ejecutar:    python main.py                            ║
╠══════════════════════════════════════════════════════════╣
║   Estructura de carpetas:                                ║
║   macaco/                                                ║
║   ├── main.py          ← punto de entrada               ║
║   ├── src/                                              ║
║   │   ├── constants.py   colores, tamaños, config        ║
║   │   ├── font.py        fuente Earthbound.otf           ║
║   │   ├── camera.py      screen shake y zoom             ║
║   │   ├── effects.py     textos flotantes y sangre       ║
║   │   ├── items.py       monedas, cofres e ítems         ║
║   │   ├── door.py        puertas entre cuartos           ║
║   │   ├── bullet.py      proyectiles                     ║
║   │   ├── enemies.py     bestiario completo              ║
║   │   ├── player.py      El Macaco                       ║
║   │   ├── rooms.py       generador roguelite de mapas    ║
║   │   └── game.py        clase principal y bucle         ║
║   └── assets/                                           ║
║       ├── fonts/         Earthbound.otf                  ║
║       └── sprites/       PNGs de personajes y enemigos   ║
╚══════════════════════════════════════════════════════════╝

Texturas (todas opcionales — sin ellas usa gráficos geométricos):
  assets/sprites/
    background_antro.png   fondo del Acto 1
    background_cata.png    fondo del Acto 2
    wall_antro.png         paredes del Acto 1  (64×64, se tesela)
    wall_cata.png          paredes del Acto 2
    obstacle_antro.png     obstáculos del Acto 1
    obstacle_cata.png      obstáculos del Acto 2
    shield.png             escudo del jugador  (128×128, apunta →)
    player_up/down/...png  8 direcciones del Macaco (64×64)
    momia_up/down/...png   8 direcciones de cada enemigo (48×48)
    zombi_up/down/...png
    pescado_up/down/...png
    esqueleto_up/down/...png
    cthulhu.png            Jefe 1  (96×96)
    momia_mayor.png        Jefe 2  (96×96)
    door_open.png          puerta abierta
    door_locked.png        puerta cerrada

Fuente:
  assets/fonts/Earthbound.otf
"""

import pygame
import sys
from src.game import Game

if __name__ == "__main__":
    pygame.init()
    game = Game()
    game.run()
