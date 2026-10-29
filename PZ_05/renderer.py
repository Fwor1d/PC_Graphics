"""Отрисовка в фиксированном логическом размере с масштабированием в окно."""

import numpy as np
import pygame

import settings as c
from transformations import transform_points, translation


class Renderer:
    def __init__(self):
        self.surface = pygame.Surface((c.WIDTH, c.HEIGHT))
        self.scene = pygame.Rect(20, 102, 710, 576)
        self.view = translation(self.scene.centerx, self.scene.centery + 15)
        family = pygame.font.match_font("arial,dejavusans,helvetica")
        mono = pygame.font.match_font("menlo,dejavusansmono,courier")
        self.fonts = {s: pygame.font.Font(family, s) for s in (13, 14, 15, 17, 20, 26)}
        self.mono = pygame.font.Font(mono, 15)
        self.viewport = pygame.Rect(0, 0, c.WIDTH, c.HEIGHT)

    def text(self, text, x, y, size=15, color=c.TEXT, mono=False):
        font = self.mono if mono else self.fonts[size]
        self.surface.blit(font.render(str(text), True, color), (x, y))

    def card(self, rect, color=c.PANEL):
        pygame.draw.rect(self.surface, color, rect, border_radius=12)

    def screen_to_canvas(self, position):
        if not self.viewport.collidepoint(position):
            return None
        return ((position[0] - self.viewport.x) * c.WIDTH / self.viewport.width,
                (position[1] - self.viewport.y) * c.HEIGHT / self.viewport.height)

    def grid(self):
        self.surface.set_clip(self.scene)
        ox, oy = self.view[:2, 2]
        for x in range(int(ox) % 40 + self.scene.left // 40 * 40 - 40, self.scene.right, 40):
            pygame.draw.line(self.surface, c.GRID, (x, self.scene.top), (x, self.scene.bottom))
        for y in range(int(oy) % 40 + self.scene.top // 40 * 40 - 40, self.scene.bottom, 40):
            pygame.draw.line(self.surface, c.GRID, (self.scene.left, y), (self.scene.right, y))
        axis = (72, 92, 116)
        pygame.draw.line(self.surface, axis, (self.scene.left, oy), (self.scene.right, oy))
        pygame.draw.line(self.surface, axis, (ox, self.scene.top), (ox, self.scene.bottom))
        pygame.draw.polygon(self.surface, axis, [(self.scene.right - 7, oy), (self.scene.right - 15, oy - 4), (self.scene.right - 15, oy + 4)])
        pygame.draw.polygon(self.surface, axis, [(ox, self.scene.bottom - 7), (ox - 4, self.scene.bottom - 15), (ox + 4, self.scene.bottom - 15)])
        self.text("X", self.scene.right - 24, oy - 25, color=c.MUTED)
        self.text("Y", ox + 12, self.scene.bottom - 30, color=c.MUTED)
        self.text("0", ox + 8, oy + 6, size=13, color=c.MUTED)
        for offset in (-240, -160, -80, 80, 160, 240):
            self.text(str(offset), ox + offset - 10, oy + 6, size=13, color=c.MUTED)
        self.surface.set_clip(None)

    def draw_house(self, house, matrix):
        self.surface.set_clip(self.scene)
        # The exact same world matrix feeds polygons, the pivot and the inspector.
        for polygon in house.polygons:
            points = transform_points(polygon.vertices, self.view @ matrix)
            pygame.draw.polygon(self.surface, polygon.color, np.rint(points).astype(int).tolist())
            pygame.draw.polygon(self.surface, c.GOLD if house.selected else (16, 43, 53),
                                np.rint(points).astype(int).tolist(), 3 if house.selected else 2)
        # Neutral source contours stay visible even when the two figures coincide.
        for polygon in house.polygons:
            points = transform_points(polygon.vertices, self.view)
            for a, b in zip(points, np.roll(points, -1, axis=0)):
                distance = np.linalg.norm(b - a)
                for d in np.arange(0, distance, 10):
                    start = a + (b - a) * d / distance
                    end = a + (b - a) * min(d + 5, distance) / distance
                    pygame.draw.line(self.surface, c.OUTLINE, start, end, 2)
        pivot = transform_points([house.state.pivot], self.view @ matrix)[0]
        p = tuple(np.rint(pivot).astype(int))
        pygame.draw.circle(self.surface, c.BACKGROUND, p, 10)
        pygame.draw.circle(self.surface, c.GOLD, p, 8, 2)
        pygame.draw.line(self.surface, c.GOLD, (p[0] - 13, p[1]), (p[0] + 13, p[1]))
        pygame.draw.line(self.surface, c.GOLD, (p[0], p[1] - 13), (p[0], p[1] + 13))
        self.text("pivot", p[0] + 15, p[1] - 9, size=14, color=c.GOLD)
        point = transform_points([[20, 0]], self.view @ matrix)[0]
        pygame.draw.circle(self.surface, c.TEXT, np.rint(point).astype(int), 4)
        self.surface.set_clip(None)

    @staticmethod
    def number(value):
        return f"{value:.2f}" if abs(value) < 10000 else f"{value:.2e}"

    def panel(self, house, matrix):
        s = house.state
        x = 766
        self.card((748, 102, 352, 260))
        self.text("TRANSFORM / ПАРАМЕТРЫ", x, 118, size=17)
        rows = [
            ("Перенос X / Y", f"{s.tx:.1f} / {s.ty:.1f}"),
            ("Угол, градусы", f"{s.angle:.1f}°"),
            ("Масштаб X / Y", f"{s.sx:.2f} / {s.sy:.2f}"),
            ("Shear X / Y", f"{s.kx:+.2f} / {s.ky:+.2f}"),
            ("Зеркало H / V", f"{'ON' if s.reflect_h else 'off'} / {'ON' if s.reflect_v else 'off'}"),
            ("Pivot local X", self.number(s.pivot[0])),
            ("Pivot local Y", self.number(s.pivot[1])),
        ]
        for i, (label, value) in enumerate(rows):
            self.text(label, x, 153 + i * 27, size=14, color=c.MUTED)
            self.text(value, x + 174, 153 + i * 27, size=14, color=c.ACCENT)
        self.card((748, 374, 352, 147))
        self.text("M / LOCAL → WORLD", x, 389, size=17)
        for i in range(3):
            for j in range(3):
                value = matrix[i, j]
                self.text(self.number(0.0 if abs(value) < 0.0005 else value),
                          x + 4 + j * 109, 424 + i * 26, mono=True,
                          color=c.TEXT if i < 2 else c.MUTED)
        self.card((748, 533, 352, 145))
        self.text("ПОРЯДОК КОМПОЗИЦИИ", x, 548, size=17)
        label = "A   T @ Rp @ Dp" if s.mode == "A" else "B   Rp @ T @ Dp"
        self.text(label, x, 578, size=20, color=c.ACCENT)
        self.text("Поворот → перенос" if s.mode == "A" else "Перенос → поворот", x, 608, color=c.MUTED)
        sample = transform_points([[20, 0]], matrix)[0]
        self.text(f"(20, 0) → ({sample[0]:.1f}, {sample[1]:.1f})", x, 638, size=14)

    def draw(self, window, house, fps=0.0, pivot_mode=False):
        self.surface.fill(c.BACKGROUND)
        self.text("AFFINE", 22, 20, size=26, color=c.ACCENT)
        self.text("TRANSFORM STUDIO", 130, 20, size=26)
        self.text("ПЗ №5  /  NumPy × PyGame  /  X вправо · Y вниз · +θ по часовой", 22, 59, color=c.MUTED)
        self.card((893, 24, 207, 36), c.CARD)
        self.text("ВЫДЕЛЕН" if house.selected else "ЛКМ: ВЫБРАТЬ", 910, 33, size=14,
                  color=c.GOLD if house.selected else c.MUTED)
        self.card(self.scene)
        self.grid()
        matrix = house.state.matrix()
        self.draw_house(house, matrix)
        self.text("СЦЕНА / WORLD", 38, 118, size=14, color=c.MUTED)
        self.text("P + ЛКМ: выбор pivot" if pivot_mode else "- - исходный контур     ● результат     + pivot",
                  38, 650, size=14, color=c.GOLD if pivot_mode else c.MUTED)
        self.panel(house, matrix)
        self.text("Стрелки  перенос   Q/E  угол   Z/X  scale X   A/D  scale Y   H/V  зеркало   J/L  shear X   U/O  shear Y", 22, 692, size=14)
        self.text("P + ЛКМ  pivot    ЛКМ  выделение    M  порядок    R  сброс    F1  пример    Esc  выход", 22, 714, size=14, color=c.MUTED)
        self.text(house.message, 22, 738, size=13, color=c.ACCENT)
        self.text(f"{fps:.0f} FPS", 1040, 738, size=13, color=c.MUTED)
        w, h = window.get_size()
        factor = min(w / c.WIDTH, h / c.HEIGHT)
        size = (max(1, round(c.WIDTH * factor)), max(1, round(c.HEIGHT * factor)))
        self.viewport = pygame.Rect((w - size[0]) // 2, (h - size[1]) // 2, *size)
        window.fill(c.BACKGROUND)
        window.blit(pygame.transform.smoothscale(self.surface, size), self.viewport)
