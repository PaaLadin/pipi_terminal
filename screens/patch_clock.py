import pygame
from datetime import datetime, timedelta

def draw_bell_icon(surface, color, pos):
    """Идеально ровный, крупный пиксельный колокольчик SovIntel, собранный линиями"""
    x, y = pos
    # Юбка колокола (нижнее широкое основание)
    pygame.draw.line(surface, color, (x, y + 40), (x + 40, y + 40), 4)
    # Основной купол (вертикальные стены и крыша)
    pygame.draw.line(surface, color, (x + 6, y + 20), (x + 6, y + 40), 3)
    pygame.draw.line(surface, color, (x + 34, y + 20), (x + 34, y + 40), 3)
    # Скосы крыши купола
    pygame.draw.line(surface, color, (x + 6, y + 20), (x + 20, y + 6), 3)
    pygame.draw.line(surface, color, (x + 34, y + 20), (x + 20, y + 6), 3)
    # Язычок/молоточек снизу
    pygame.draw.circle(surface, color, (x + 20, y + 44), 3)
    # Ушко сверху
    pygame.draw.circle(surface, color, (x + 20, y + 4), 2)
