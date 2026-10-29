"""Пошаговые BFS, Dijkstra и A*. Здесь намеренно нет импорта pygame."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq
from itertools import count
from typing import Generator

from grid import Grid, Position, get_neighbors


@dataclass(frozen=True)
class SearchResult:
    found: bool
    path: tuple[Position, ...]
    path_length: int
    path_cost: int
    visited_nodes: int


@dataclass(frozen=True)
class SearchStep:
    # expand = обработать вершину, path = показать клетку пути, finish = итог
    kind: str
    node: Position | None = None
    opened: tuple[Position, ...] = ()
    frontier_size: int = 0
    result: SearchResult | None = None


def heuristic(a: Position, b: Position) -> int:
    """Манхэттенское расстояние для четырёх направлений."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(
    came_from: dict[Position, Position], start: Position, goal: Position
) -> tuple[Position, ...]:
    """Восстановить путь, включая начальную и конечную клетки."""
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return tuple(path)


def _finish(
    grid: Grid,
    came_from: dict[Position, Position],
    visited_nodes: int,
    found: bool,
) -> Generator[SearchStep, None, None]:
    if found:
        path = reconstruct_path(came_from, grid.start, grid.goal)
        for node in path[1:-1]:
            yield SearchStep(kind="path", node=node)
        result = SearchResult(
            found=True,
            path=path,
            path_length=len(path) - 1,
            path_cost=sum(grid.movement_cost(node) for node in path[1:]),
            visited_nodes=visited_nodes,
        )
    else:
        result = SearchResult(False, (), 0, 0, visited_nodes)
    yield SearchStep(kind="finish", result=result)


def bfs_steps(grid: Grid) -> Generator[SearchStep, None, None]:
    """BFS оптимален по числу переходов, но игнорирует веса при поиске."""
    start, goal = grid.start, grid.goal
    frontier = deque([start])
    discovered = {start}
    came_from: dict[Position, Position] = {}
    visited_nodes = 0

    while frontier:
        current = frontier.popleft()
        visited_nodes += 1
        opened: list[Position] = []
        if current != goal:
            for neighbor in get_neighbors(current, grid):
                if neighbor not in discovered:
                    discovered.add(neighbor)
                    came_from[neighbor] = current
                    frontier.append(neighbor)
                    opened.append(neighbor)
        yield SearchStep("expand", node=current, opened=tuple(opened), frontier_size=len(frontier))
        if current == goal:
            yield from _finish(grid, came_from, visited_nodes, found=True)
            return

    yield from _finish(grid, came_from, visited_nodes, found=False)


def _weighted_steps(grid: Grid, use_heuristic: bool) -> Generator[SearchStep, None, None]:
    """Общая основа Dijkstra (h=0) и A* (h=Manhattan)."""
    start, goal = grid.start, grid.goal
    order = count()
    frontier = [(heuristic(start, goal) if use_heuristic else 0, next(order), 0, start)]
    costs: dict[Position, int] = {start: 0}
    came_from: dict[Position, Position] = {}
    closed: set[Position] = set()

    while frontier:
        _, _, entry_cost, current = heapq.heappop(frontier)
        # В heap могут оставаться устаревшие приоритеты.
        if current in closed or entry_cost != costs[current]:
            continue
        closed.add(current)
        opened: list[Position] = []
        if current != goal:
            for neighbor in get_neighbors(current, grid):
                if neighbor in closed:
                    continue
                new_cost = costs[current] + grid.movement_cost(neighbor)
                if new_cost < costs.get(neighbor, float("inf")):
                    costs[neighbor] = new_cost
                    came_from[neighbor] = current
                    priority = new_cost + (heuristic(neighbor, goal) if use_heuristic else 0)
                    heapq.heappush(frontier, (priority, next(order), new_cost, neighbor))
                    opened.append(neighbor)
        yield SearchStep("expand", node=current, opened=tuple(opened), frontier_size=len(frontier))
        if current == goal:
            yield from _finish(grid, came_from, len(closed), found=True)
            return

    yield from _finish(grid, came_from, len(closed), found=False)


def dijkstra_steps(grid: Grid) -> Generator[SearchStep, None, None]:
    yield from _weighted_steps(grid, use_heuristic=False)


def astar_steps(grid: Grid) -> Generator[SearchStep, None, None]:
    yield from _weighted_steps(grid, use_heuristic=True)


ALGORITHMS = {
    "BFS": bfs_steps,
    "Dijkstra": dijkstra_steps,
    "A*": astar_steps,
}
