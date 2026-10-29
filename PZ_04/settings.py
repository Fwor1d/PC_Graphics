"""Размеры, подписи и палитра интерфейса."""
from __future__ import annotations

WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 860
MIN_WIDTH = 1200
MIN_HEIGHT = 750
ROWS = 24
COLS = 38
PANEL_WIDTH = 338
FPS = 60
SPEEDS = (2, 5, 10, 20, 40, 80, 160, 320)
DEFAULT_SPEED_INDEX = 4

BG = (10, 16, 27)
PANEL = (17, 27, 43)
PANEL_ALT = (22, 35, 54)
BORDER = (42, 58, 78)
WHITE = (236, 243, 250)
MUTED = (144, 163, 185)
FAINT = (97, 116, 139)
ACCENT = (86, 161, 255)
START = (50, 203, 144)
GOAL = (247, 109, 125)
WALL = (72, 86, 107)
WEIGHTED = (165, 120, 232)
OPEN = (52, 170, 201)
CLOSED = (63, 105, 174)
PATH = (251, 195, 84)
EMPTY_A = (26, 39, 58)
EMPTY_B = (29, 43, 64)
SUCCESS = START
ERROR = GOAL

TILE_LABELS = (
    ("Старт", START),
    ("Цель", GOAL),
    ("Стена", WALL),
    ("Вес 5", WEIGHTED),
    ("В очереди", OPEN),
    ("Проверена", CLOSED),
    ("Маршрут", PATH),
)
