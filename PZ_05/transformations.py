"""Чистая линейная алгебра: float64, столбцы, X вправо, Y вниз.

Точки хранятся строками N×2, но умножаются как столбцы (M @ P.T).T.
Положительное вращение на экране направлено по часовой стрелке.
"""

import numpy as np


def translation(tx, ty):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], dtype=np.float64)


def scale(sx, sy):
    return np.diag(np.array([sx, sy, 1], dtype=np.float64))


def rotation(angle_degrees):
    angle = np.deg2rad(angle_degrees)
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


def reflection(axis):
    """vertical: x -> -x; horizontal: y -> -y (локальные оси)."""
    if axis == "vertical":
        return scale(-1, 1)
    if axis == "horizontal":
        return scale(1, -1)
    raise ValueError("axis must be 'vertical' or 'horizontal'")


def shear(kx=0.0, ky=0.0):
    """Одновременный shear: x'=x+kx*y, y'=ky*x+y; det=1-kx*ky."""
    return np.array([[1, kx, 0], [ky, 1, 0], [0, 0, 1]], dtype=np.float64)


def shear_x(k):
    return shear(kx=k)


def shear_y(k):
    return shear(ky=k)


def compose(*matrices):
    """compose(A, B) = A @ B: аргументы записываются в порядке матрицы."""
    result = np.eye(3, dtype=np.float64)
    for matrix in matrices:
        result = result @ np.asarray(matrix, dtype=np.float64)
    return result


def around_pivot(matrix, pivot):
    px, py = pivot
    return translation(px, py) @ matrix @ translation(-px, -py)


def rotation_around_pivot(angle_degrees, pivot):
    return around_pivot(rotation(angle_degrees), pivot)


def transform_points(points, matrix):
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("Expected points of shape (N, 2)")
    homogeneous = np.column_stack((points, np.ones(len(points))))
    result = (np.asarray(matrix, dtype=np.float64) @ homogeneous.T).T
    if not np.all(np.isfinite(result)) or np.any(np.abs(result[:, 2]) < 1e-14):
        raise ValueError("Transformation produced invalid homogeneous coordinates")
    return result[:, :2] / result[:, 2:3]


def safe_inverse(matrix):
    """None при вырождении/плохой обусловленности вместо аварии hit-test."""
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.shape != (3, 3) or not np.all(np.isfinite(matrix)):
        return None
    try:
        if abs(np.linalg.det(matrix)) < 1e-10 or np.linalg.cond(matrix) > 1e12:
            return None
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return None


def inverse_transform_points(points, matrix):
    inverse = safe_inverse(matrix)
    return None if inverse is None else transform_points(points, inverse)
