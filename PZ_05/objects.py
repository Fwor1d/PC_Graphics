"""Неизменяемая локальная геометрия, состояние и выбор по силуэту."""

from dataclasses import dataclass, field

import numpy as np

from settings import SCALE_MIN, SCALE_MAX, SHEAR_MIN, SHEAR_MAX, TRANSLATION_LIMIT
from transformations import (
    around_pivot, inverse_transform_points, reflection, rotation, scale, shear,
    transform_points, translation,
)


@dataclass(frozen=True)
class Polygon:
    name: str
    vertices: np.ndarray
    color: tuple


def house_geometry():
    specs = (
        ("Корпус", [(-90, -35), (90, -35), (90, 100), (-90, 100)], (65, 181, 164)),
        ("Крыша", [(-112, -35), (-25, -125), (112, -35)], (245, 130, 112)),
        ("Дверь", [(27, 20), (65, 20), (65, 100), (27, 100)], (28, 59, 75)),
        ("Окно", [(-62, -8), (-20, -8), (-20, 34), (-62, 34)], (248, 214, 135)),
    )
    result = []
    for name, vertices, color in specs:
        # Immutable backing buffer also prevents accidentally restoring writeability.
        data = np.array(vertices, dtype=np.float64)
        immutable = np.frombuffer(data.tobytes(), dtype=np.float64).reshape(-1, 2)
        result.append(Polygon(name, immutable, color))
    return tuple(result)


def point_in_polygon(point, vertices, tolerance=1e-8):
    """Ray casting. Граница считается частью фигуры (допуск 1e-8)."""
    px, py = point
    inside = False
    for a, b in zip(vertices, np.roll(vertices, -1, axis=0)):
        edge, offset = b - a, np.array(point) - a
        length = np.linalg.norm(edge)
        cross = edge[0] * offset[1] - edge[1] * offset[0]
        if (length > 0 and abs(cross) <= tolerance * length
                and -tolerance <= np.dot(offset, edge) <= length * length + tolerance):
            return True
        if (a[1] > py) != (b[1] > py):
            crossing = a[0] + (py - a[1]) * edge[0] / edge[1]
            if crossing > px:
                inside = not inside
    return inside


@dataclass
class TransformState:
    tx: float = 0.0
    ty: float = 0.0
    angle: float = 0.0
    sx: float = 1.0
    sy: float = 1.0
    kx: float = 0.0
    ky: float = 0.0
    reflect_h: bool = False
    reflect_v: bool = False
    pivot: tuple = (0.0, 0.0)
    mode: str = "A"

    def constrain(self):
        self.sx = float(np.clip(self.sx, SCALE_MIN, SCALE_MAX))
        self.sy = float(np.clip(self.sy, SCALE_MIN, SCALE_MAX))
        self.kx = float(np.clip(self.kx, SHEAR_MIN, SHEAR_MAX))
        self.ky = float(np.clip(self.ky, SHEAR_MIN, SHEAR_MAX))
        self.tx = float(np.clip(self.tx, -TRANSLATION_LIMIT, TRANSLATION_LIMIT))
        self.ty = float(np.clip(self.ty, -TRANSLATION_LIMIT, TRANSLATION_LIMIT))
        self.angle %= 360.0

    def matrix(self):
        """A=T @ Rp @ Dp; B=Rp @ T @ Dp. Dp, Rp центрированы на p.

        D = H @ S @ F. Поэтому A совпадает с T @ T(p) @ R @ H @ S @ F @ T(-p).
        В B перенос предшествует вращению: pivot объекта описывает окружность
        вокруг p при ненулевом T. Это ожидаемое различие двух порядков.
        """
        f = np.eye(3, dtype=np.float64)
        if self.reflect_h:
            f = reflection("vertical") @ f
        if self.reflect_v:
            f = reflection("horizontal") @ f
        dp = around_pivot(shear(self.kx, self.ky) @ scale(self.sx, self.sy) @ f, self.pivot)
        rp = around_pivot(rotation(self.angle), self.pivot)
        t = translation(self.tx, self.ty)
        if self.mode == "A":
            return t @ rp @ dp
        if self.mode == "B":
            return rp @ t @ dp
        raise ValueError("Composition mode must be A or B")


@dataclass
class House:
    polygons: tuple = field(default_factory=house_geometry)
    state: TransformState = field(default_factory=TransformState)
    selected: bool = False
    message: str = "ЛКМ — выделить объект; P + ЛКМ — задать pivot"

    def reset(self):
        self.state = TransformState()
        self.selected = False
        self.message = "Исходное состояние восстановлено"

    def transformed(self, view=None):
        matrix = self.state.matrix()
        if view is not None:
            matrix = view @ matrix
        return tuple(transform_points(p.vertices, matrix) for p in self.polygons)

    def click(self, screen_point, view, set_pivot=False):
        local = inverse_transform_points([screen_point], view @ self.state.matrix())
        if local is None:
            self.selected = False
            self.message = "Обратное преобразование недоступно: проверьте матрицу"
            return False
        if set_pivot:
            self.state.pivot = tuple(float(v) for v in local[0])
            self.message = f"Pivot local: ({local[0, 0]:.2f}, {local[0, 1]:.2f})"
            return True
        self.selected = any(point_in_polygon(local[0], p.vertices) for p in self.polygons)
        self.message = "Домик выделен по силуэту" if self.selected else "Выделение снято"
        return self.selected

    def demo(self):
        self.reset()
        self.state.tx, self.state.ty, self.state.angle = 120.0, 60.0, 90.0
        self.message = "Пример: (20, 0), T(120, 60), R(+90°). M — сравнить режимы"
