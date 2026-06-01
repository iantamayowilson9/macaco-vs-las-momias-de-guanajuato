import pygame, os

_FONT_PATH  = os.path.join("assets", "fonts", "Earthbound.otf")
_font_cache = {}

def get_font(size, bold=False):
    """
    Carga y cachea las fuentes para evitar cuello de botella al renderizar texto.
    Si la fuente personalizada no existe, usa Consolas como respaldo del sistema.
    """
    key = (size, bold)
    if key not in _font_cache:
        try:
            _font_cache[key] = pygame.font.Font(_FONT_PATH, size)
        except Exception:
            _font_cache[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return _font_cache[key]