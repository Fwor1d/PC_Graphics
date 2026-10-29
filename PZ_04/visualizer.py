"""Отрисовка интерфейса PyGame. Алгоритмы сюда не импортируют ничего."""
from __future__ import annotations

from pathlib import Path
import pygame

from grid import Tile
from settings import (
    BG, PANEL, PANEL_ALT, BORDER, WHITE, MUTED, FAINT, ACCENT,
    START, GOAL, WALL, WEIGHTED, OPEN, CLOSED, PATH,
    EMPTY_A, EMPTY_B, SPEEDS, PANEL_WIDTH, TILE_LABELS,
)


class FontBook:
    """Пытаемся выбрать шрифт с поддержкой кириллицы на macOS/Windows/Linux."""
    def __init__(self):
        paths = (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        )
        self.path = next((p for p in paths if Path(p).is_file()), None)
        self.cache: dict[tuple[int, bool], pygame.font.Font] = {}

    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self.cache:
            if self.path:
                font = pygame.font.Font(self.path, size)
                font.set_bold(bold)
            else:
                font = pygame.font.SysFont("arial,dejavusans,liberation sans", size, bold=bold)
            self.cache[key] = font
        return self.cache[key]


class Renderer:
    def __init__(self):
        self.fonts = FontBook()
        self.buttons: dict[str, pygame.Rect] = {}
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self.grid_rect = pygame.Rect(0, 0, 0, 0)
        self.cell_size = 1
        self.scroll = 0
        self.sidebar_content_height = 748

    def text(self, surface, value, x, y, size=15, color=WHITE, bold=False, max_width=None):
        font = self.fonts.get(size, bold)
        label = str(value)
        if max_width is not None and font.size(label)[0] > max_width:
            while label and font.size(label + "…")[0] > max_width:
                label = label[:-1]
            label += "…"
        image = font.render(label, True, color)
        surface.blit(image, (round(x), round(y)))
        return image.get_width()

    def centered(self, surface, value, rect, size=15, color=WHITE, bold=False):
        font = self.fonts.get(size, bold)
        image = font.render(str(value), True, color)
        surface.blit(image, image.get_rect(center=rect.center))

    def round_rect(self, surface, rect, color, radius=12, border=None):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)

    def pill(self, surface, rect, text, color=ACCENT, bg=PANEL_ALT, size=13):
        self.round_rect(surface, rect, bg, radius=rect.height // 2)
        self.centered(surface, text, rect, size=size, color=color, bold=True)

    def button(self, surface, key, rect, label, selected=False, primary=False, text_size=15):
        self.buttons[key] = rect.copy()
        mouse = pygame.mouse.get_pos()
        visible = True
        if key.startswith("algo:") or key in ("run", "step", "reset", "demo", "clear", "speed_up", "speed_down"):
            visible = self.sidebar_rect.collidepoint(mouse) and self.sidebar_rect.colliderect(rect)
        hover = rect.collidepoint(mouse) and visible
        if primary:
            bg = (103, 177, 255) if hover else ACCENT
            fg = BG
            stroke = None
        elif selected:
            bg = (41, 75, 111) if hover else (35, 64, 95)
            fg = (180, 220, 255)
            stroke = (71, 119, 165)
        else:
            bg = (36, 52, 74) if hover else PANEL_ALT
            fg = WHITE if hover else MUTED
            stroke = BORDER
        self.round_rect(surface, rect, bg, radius=9, border=stroke)
        self.centered(surface, label, rect, size=text_size, color=fg, bold=selected or primary)

    def layout(self, screen):
        w, h = screen.get_size()
        self.board_rect = pygame.Rect(20, 88, w - PANEL_WIDTH - 56, h - 153)
        self.sidebar_rect = pygame.Rect(w - PANEL_WIDTH - 20, 88, PANEL_WIDTH, h - 153)
        self.scroll = max(0, min(self.scroll, self.max_scroll()))

    def max_scroll(self):
        return max(0, self.sidebar_content_height - self.sidebar_rect.height + 20)

    def scroll_sidebar(self, direction):
        self.scroll = max(0, min(self.max_scroll(), self.scroll + direction * 45))

    def button_at(self, point):
        for key, rect in self.buttons.items():
            if not rect.collidepoint(point):
                continue
            if key.startswith("brush:") or key == "clear":
                if key.startswith("brush:") and self.board_rect.collidepoint(point):
                    return key
                if key == "clear" and self.sidebar_rect.collidepoint(point):
                    return key
            elif self.sidebar_rect.collidepoint(point):
                return key
        return None

    def cell_at(self, point, grid):
        if not self.grid_rect.collidepoint(point):
            return None
        mx, my = point
        col = (mx - self.grid_rect.x) // self.cell_size
        row = (my - self.grid_rect.y) // self.cell_size
        if 0 <= row < grid.rows and 0 <= col < grid.cols:
            return (row, col)
        return None

    def draw(self, screen, app):
        screen.fill(BG)
        self.buttons.clear()
        self.layout(screen)
        self.draw_header(screen, app)
        self.draw_board(screen, app)
        self.draw_sidebar(screen, app)
        self.draw_footer(screen)

    def draw_header(self, screen, app):
        pygame.draw.rect(screen, (19, 31, 48), pygame.Rect(0, 0, screen.get_width(), 3))
        pygame.draw.circle(screen, ACCENT, (36, 39), 13)
        self.centered(screen, "P", pygame.Rect(25, 28, 22, 22), 15, BG, bold=True)
        self.text(screen, "PATHFINDING LAB", 60, 21, 25, WHITE, bold=True)
        self.text(screen, "Практическая работа №4  /  Визуализация поиска пути", 61, 53, 13, MUTED)
        tag = pygame.Rect(screen.get_width() - 168, 25, 148, 33)
        self.pill(screen, tag, "PYTHON + PYGAME", color=ACCENT, size=12)

    def draw_board(self, screen, app):
        board = self.board_rect
        self.round_rect(screen, board, PANEL, radius=14, border=BORDER)
        self.text(screen, "Карта и редактор", board.x + 19, board.y + 20, 19, WHITE, bold=True)
        self.text(screen, f"{app.grid.cols} × {app.grid.rows} клеток", board.x + 19, board.y + 50, 13, FAINT)
        brush_items = (
            ("wall", "Стена"), ("weighted", "Вес 5"),
            ("start", "Старт"), ("goal", "Цель"), ("erase", "Ластик"),
        )
        toolbar_x = board.x + 260
        gap = 6
        tool_width = max(62, (board.right - toolbar_x - 20 - gap * 4) // 5)
        for i, (key, label) in enumerate(brush_items):
            rect = pygame.Rect(toolbar_x + (tool_width + gap) * i, board.y + 25, tool_width, 36)
            self.button(screen, "brush:" + key, rect, label, selected=app.brush == key, text_size=13)

        content_x = board.x + 15
        content_y = board.y + 79
        content_w = board.width - 30
        content_h = board.height - 145
        size = min(content_w // app.grid.cols, content_h // app.grid.rows)
        self.cell_size = max(1, size)
        width = self.cell_size * app.grid.cols
        height = self.cell_size * app.grid.rows
        left = content_x + (content_w - width) // 2
        top = content_y + (content_h - height) // 2
        self.grid_rect = pygame.Rect(left, top, width, height)
        frame = self.grid_rect.inflate(12, 12)
        self.round_rect(screen, frame, (12, 21, 35), 9, border=BORDER)
        mouse = pygame.mouse.get_pos()
        hovered_cell = self.cell_at(mouse, app.grid)
        for row in range(app.grid.rows):
            for col in range(app.grid.cols):
                node = (row, col)
                tile = app.grid.get(node)
                color = EMPTY_A if (row + col) % 2 == 0 else EMPTY_B
                if tile == Tile.WALL:
                    color = WALL
                elif tile == Tile.WEIGHTED:
                    color = (80, 58, 118)
                if node in app.closed_set:
                    color = CLOSED
                elif node in app.open_set:
                    color = OPEN
                if node in app.path_set:
                    color = PATH
                if node == app.grid.start:
                    color = START
                elif node == app.grid.goal:
                    color = GOAL
                pos = pygame.Rect(left + col * size + 1, top + row * size + 1, max(1, size - 2), max(1, size - 2))
                pygame.draw.rect(screen, color, pos, border_radius=3 if size > 14 else 1)
                if node == app.current and node not in (app.grid.start, app.grid.goal):
                    pygame.draw.rect(screen, WHITE, pos, width=2, border_radius=3)
                if node in (app.grid.start, app.grid.goal):
                    self.centered(screen, "S" if node == app.grid.start else "G", pos, max(12, size - 9), BG, True)
                elif tile == Tile.WEIGHTED and node not in app.open_set and node not in app.closed_set and node not in app.path_set and size >= 17:
                    self.centered(screen, "5", pos, 11 if size <= 21 else 12, (231, 203, 253), True)
                if node == hovered_cell and node not in (app.grid.start, app.grid.goal):
                    pygame.draw.rect(screen, (180, 211, 241), pos, width=1, border_radius=3)

        legend_y = board.bottom - 46
        pygame.draw.line(screen, BORDER, (board.x + 20, legend_y - 13), (board.right - 20, legend_y - 13))
        x = board.x + 21
        for name, color in TILE_LABELS:
            square = pygame.Rect(x, legend_y + 5, 13, 13)
            pygame.draw.rect(screen, color, square, border_radius=3)
            text_w = self.text(screen, name, x + 19, legend_y + 3, 12, MUTED)
            x += text_w + 39

    def draw_sidebar(self, screen, app):
        pane = self.sidebar_rect
        self.round_rect(screen, pane, PANEL, radius=14, border=BORDER)
        old_clip = screen.get_clip()
        inner_clip = pygame.Rect(pane.x + 1, pane.y + 2, pane.width - 4, pane.height - 4)
        screen.set_clip(inner_clip)
        x = pane.x + 18
        w = pane.width - 36
        sy = lambda y: pane.y + y - self.scroll

        self.text(screen, "АЛГОРИТМ", x, sy(19), 12, MUTED, bold=True)
        gap = 7
        bw = (w - 2 * gap) // 3
        for i, name in enumerate(("BFS", "Dijkstra", "A*")):
            self.button(screen, "algo:" + name, pygame.Rect(x + i * (bw + gap), sy(47), bw, 39), name,
                        selected=app.algorithm == name, text_size=14)
        pygame.draw.line(screen, BORDER, (x, sy(101)), (x + w, sy(101)))

        self.text(screen, "УПРАВЛЕНИЕ ПОИСКОМ", x, sy(113), 12, MUTED, bold=True)
        play_label = "Пауза  [Space]" if app.running else "Продолжить  [Space]" if app.generator else "Запустить  [Space]"
        self.button(screen, "run", pygame.Rect(x, sy(140), w, 42), play_label, primary=True, text_size=15)
        third = (w - 14) // 3
        for i, (name, label) in enumerate((('step', 'Шаг [N]'), ('reset', 'Сброс [R]'), ('demo', 'Демо [D]'))):
            self.button(screen, name, pygame.Rect(x + i * (third + 7), sy(191), third, 36), label, text_size=12)
        self.button(screen, "clear", pygame.Rect(x, sy(234), w, 30), "Очистить карту  [C]", text_size=12)

        self.text(screen, "СКОРОСТЬ", x, sy(278), 12, MUTED, bold=True)
        self.button(screen, "speed_down", pygame.Rect(x, sy(303), 41, 35), "−", text_size=19)
        self.round_rect(screen, pygame.Rect(x + 48, sy(303), w - 96, 35), PANEL_ALT, 9, border=BORDER)
        self.centered(screen, f"{SPEEDS[app.speed_index]} шагов/с", pygame.Rect(x + 48, sy(303), w - 96, 35), 14, WHITE, True)
        self.button(screen, "speed_up", pygame.Rect(x + w - 41, sy(303), 41, 35), "+", text_size=20)

        self.text(screen, "СТАТИСТИКА", x, sy(359), 12, MUTED, bold=True)
        statuses = {
            "idle": ("ГОТОВО К ЗАПУСКУ", MUTED),
            "running": ("ИДЁТ ПОИСК", ACCENT),
            "paused": ("ПАУЗА", PATH),
            "found": ("МАРШРУТ НАЙДЕН", START),
            "not_found": ("PATH NOT FOUND", GOAL),
        }
        status_label, status_color = statuses[app.status]
        status_w = self.fonts.get(11, True).size(status_label)[0] + 22
        self.pill(screen, pygame.Rect(x + w - status_w, sy(352), status_w, 25), status_label, color=status_color, size=11)
        items = (
            ("Обработано клеток", str(app.visited_nodes)),
            ("Длина маршрута", "—" if app.result is None or not app.result.found else str(app.result.path_length)),
            ("Стоимость пути", "—" if app.result is None or not app.result.found else str(app.result.path_cost)),
            ("Шагов анимации", str(app.step_count)),
            ("В очереди", str(app.frontier_size)),
            ("Результат", "Есть" if app.status == "found" else "Нет" if app.status == "not_found" else "—"),
        )
        half_w = (w - 9) // 2
        for i, (name, value) in enumerate(items):
            row, col = divmod(i, 2)
            rect = pygame.Rect(x + col * (half_w + 9), sy(389 + row * 58), half_w, 51)
            self.round_rect(screen, rect, PANEL_ALT, radius=9, border=BORDER)
            self.text(screen, name, rect.x + 10, rect.y + 7, 10, MUTED, max_width=half_w - 16)
            self.text(screen, value, rect.x + 10, rect.y + 22, 20, WHITE, bold=True)

        self.text(screen, "СРАВНЕНИЕ АЛГОРИТМОВ", x, sy(578), 12, MUTED, bold=True)
        self.text(screen, "Алгоритм", x + 7, sy(606), 11, FAINT)
        self.text(screen, "Узлы", x + 116, sy(606), 11, FAINT)
        self.text(screen, "Шаги", x + 179, sy(606), 11, FAINT)
        self.text(screen, "Цена", x + 250, sy(606), 11, FAINT)
        for i, name in enumerate(("BFS", "Dijkstra", "A*")):
            rect = pygame.Rect(x, sy(625 + i * 37), w, 33)
            self.round_rect(screen, rect, (28, 48, 72) if app.algorithm == name else PANEL_ALT, 7)
            res = app.history.get(name)
            self.text(screen, name, x + 7, rect.y + 8, 12, ACCENT if app.algorithm == name else WHITE, bold=True)
            self.text(screen, str(res.visited_nodes) if res else "—", x + 118, rect.y + 8, 12, WHITE)
            self.text(screen, str(res.path_length) if res and res.found else "—", x + 182, rect.y + 8, 12, WHITE)
            self.text(screen, str(res.path_cost) if res and res.found else "—", x + 250, rect.y + 8, 12, WHITE)
        self.text(screen, "Результаты сохраняются до изменения карты.", x, sy(740), 11, FAINT)
        screen.set_clip(old_clip)
        if self.max_scroll() > 0:
            track = pygame.Rect(pane.right - 7, pane.top + 10, 3, pane.height - 20)
            thumb_h = max(27, int(track.height * pane.height / (self.sidebar_content_height + 20)))
            thumb_y = track.top + int((track.height - thumb_h) * self.scroll / self.max_scroll())
            pygame.draw.rect(screen, (54, 71, 93), track, border_radius=2)
            pygame.draw.rect(screen, ACCENT, pygame.Rect(track.x, thumb_y, 3, thumb_h), border_radius=2)

    def draw_footer(self, screen):
        x, y = 25, screen.get_height() - 45
        self.text(screen, "МЫШЬ", x, y, 11, ACCENT, bold=True)
        self.text(screen, "ЛКМ: рисовать   ПКМ: стирать   S/G/W + ЛКМ: старт / цель / вес", x + 53, y - 1, 12, MUTED)
        self.text(screen, "1 / 2 / 3: алгоритм    ↑/↓: скорость    Esc: выход", screen.get_width() - 465, y - 1, 12, MUTED)
