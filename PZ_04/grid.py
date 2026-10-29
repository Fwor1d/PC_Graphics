"""Логическая сетка. Этот модуль не зависит от pygame."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

Position = tuple[int, int]


class Tile(IntEnum):
    EMPTY = 0
    WALL = 1
    WEIGHTED = 2


DIRECTIONS: tuple[Position, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass
class Grid:
    rows: int = 24
    cols: int = 38
    start: Position | None = None
    goal: Position | None = None
    cells: list[list[Tile]] = field(init=False)

    def __post_init__(self) -> None:
        if self.rows < 2 or self.cols < 2:
            raise ValueError("Размеры сетки должны быть не менее 2×2")
        self.cells = [[Tile.EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        if self.start is None:
            self.start = (self.rows // 2, min(3, self.cols - 2))
        if self.goal is None:
            self.goal = (self.rows // 2, self.cols - 2)
        if not self.inside(self.start) or not self.inside(self.goal):
            raise ValueError("Старт и цель должны находиться в сетке")
        if self.start == self.goal:
            # Для компактной сетки с позициями по умолчанию (например, 2×2).
            if self.cols == 2 and self.start == (self.rows // 2, 0):
                self.goal = (self.rows // 2, 1)
            else:
                raise ValueError("Старт и цель не могут совпадать")

    def inside(self, node: Position) -> bool:
        return 0 <= node[0] < self.rows and 0 <= node[1] < self.cols

    def get(self, node: Position) -> Tile:
        if not self.inside(node):
            raise IndexError(node)
        return self.cells[node[0]][node[1]]

    def set_tile(self, node: Position, tile: Tile) -> bool:
        """Установить тип клетки. True только если карта действительно изменилась."""
        if not self.inside(node) or node in (self.start, self.goal):
            return False
        tile = Tile(tile)
        if self.get(node) == tile:
            return False
        self.cells[node[0]][node[1]] = tile
        return True

    def set_start(self, node: Position) -> bool:
        if not self.inside(node) or node == self.goal or node == self.start:
            return False
        self.cells[node[0]][node[1]] = Tile.EMPTY
        self.start = node
        return True

    def set_goal(self, node: Position) -> bool:
        if not self.inside(node) or node == self.start or node == self.goal:
            return False
        self.cells[node[0]][node[1]] = Tile.EMPTY
        self.goal = node
        return True

    def clear(self) -> None:
        """Очистить рельеф; старт и цель остаются на своих местах."""
        for row in self.cells:
            row[:] = [Tile.EMPTY] * self.cols

    def load_demo(self) -> None:
        """Демонстрационная карта с развилками и клетками стоимости 5."""
        self.clear()
        self.start = (self.rows // 2, 2)
        self.goal = (self.rows // 2, self.cols - 3)

        def wall(r: int, c: int) -> None:
            self.set_tile((r, c), Tile.WALL)

        def weighted(r: int, c: int) -> None:
            self.set_tile((r, c), Tile.WEIGHTED)

        # Стены не замыкают цель полностью; проходы создают альтернативные пути.
        for r in range(2, self.rows - 2):
            if r not in (5, 6, 17, 18):
                wall(r, 11)
        for c in range(14, 28):
            if c not in (17, 18, 25):
                wall(8, c)
        for r in range(4, self.rows - 3):
            if r not in (12, 13, 19):
                wall(r, 29)
        for c in range(3, 10):
            weighted(self.rows // 2, c)
        for c in range(15, 26):
            weighted(13, c)
        for r in range(9, 16):
            weighted(r, 27)

    def movement_cost(self, node: Position) -> int:
        return 5 if self.get(node) == Tile.WEIGHTED else 1


def get_neighbors(node: Position, grid: Grid) -> list[Position]:
    """Соседи строго по четырём направлениям, без выхода за границы и стен."""
    r, c = node
    result: list[Position] = []
    for dr, dc in DIRECTIONS:
        neighbor = (r + dr, c + dc)
        if grid.inside(neighbor) and grid.get(neighbor) != Tile.WALL:
            result.append(neighbor)
    return result
