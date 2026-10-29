"""ПР №4: визуализация BFS, Dijkstra и A* на двумерной карте."""
from __future__ import annotations

import pygame

from algorithms import ALGORITHMS, SearchResult, SearchStep
from grid import Grid, Tile
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    ROWS, COLS, FPS, SPEEDS, DEFAULT_SPEED_INDEX,
)
from visualizer import Renderer


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pathfinding Lab — Практическая работа №4")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer()
        self.grid = Grid(ROWS, COLS)
        self.grid.load_demo()
        self.algorithm = "A*"
        self.brush = "wall"
        self.speed_index = DEFAULT_SPEED_INDEX
        self.generator = None
        self.running = False
        self.status = "idle"
        self.open_set: set[tuple[int, int]] = set()
        self.closed_set: set[tuple[int, int]] = set()
        self.path_set: set[tuple[int, int]] = set()
        self.current: tuple[int, int] | None = None
        self.result: SearchResult | None = None
        self.history: dict[str, SearchResult] = {}
        self.visited_nodes = 0
        self.step_count = 0
        self.frontier_size = 0
        self.accumulator = 0.0
        self.keep_running = True

    def reset_search(self, clear_history: bool = False):
        self.generator = None
        self.running = False
        self.status = "idle"
        self.open_set.clear()
        self.closed_set.clear()
        self.path_set.clear()
        self.current = None
        self.result = None
        self.visited_nodes = 0
        self.step_count = 0
        self.frontier_size = 0
        self.accumulator = 0
        if clear_history:
            self.history.clear()

    def select_algorithm(self, name: str):
        if name in ALGORITHMS and self.algorithm != name:
            self.algorithm = name
            # Результаты уже завершённых запусков нужны для сравнения.
            self.reset_search(clear_history=False)

    def prepare_generator(self):
        if self.generator is None:
            # Повторный запуск после результата: удаляем только визуальные метки.
            self.reset_search(clear_history=False)
            self.generator = ALGORITHMS[self.algorithm](self.grid)
            self.open_set.add(self.grid.start)
            self.status = "paused"

    def toggle_run(self):
        if self.running:
            self.running = False
            self.status = "paused"
            return
        self.prepare_generator()
        self.running = True
        self.status = "running"

    def step_once(self):
        self.prepare_generator()
        self.running = False
        self.status = "paused"
        self.advance()

    def advance(self):
        if self.generator is None:
            return
        try:
            event: SearchStep = next(self.generator)
        except StopIteration:
            # Defensive fallback: нормальное завершение генерирует finish.
            self.generator = None
            self.running = False
            self.status = "not_found"
            return

        if event.kind == "expand":
            self.current = event.node
            self.open_set.discard(event.node)
            self.closed_set.add(event.node)
            self.open_set.update(event.opened)
            self.visited_nodes += 1
            self.step_count += 1
            self.frontier_size = event.frontier_size
        elif event.kind == "path":
            if event.node is not None:
                self.path_set.add(event.node)
            self.step_count += 1
        elif event.kind == "finish":
            self.result = event.result
            self.history[self.algorithm] = event.result
            self.running = False
            self.status = "found" if event.result.found else "not_found"
            self.open_set.clear()
            self.current = None
            self.frontier_size = 0
            self.generator = None

    def edit_cell(self, node, mouse_button: int, dragging: bool = False):
        if node is None:
            return
        keys = pygame.key.get_pressed()
        if mouse_button == 3:
            brush = "erase"
        elif keys[pygame.K_s]:
            brush = "start"
        elif keys[pygame.K_g]:
            brush = "goal"
        elif keys[pygame.K_w]:
            brush = "weighted"
        else:
            brush = self.brush
        if dragging and brush in ("start", "goal"):
            return
        if brush == "wall":
            changed = self.grid.set_tile(node, Tile.WALL)
        elif brush == "weighted":
            changed = self.grid.set_tile(node, Tile.WEIGHTED)
        elif brush == "erase":
            changed = self.grid.set_tile(node, Tile.EMPTY)
        elif brush == "start":
            changed = self.grid.set_start(node)
        elif brush == "goal":
            changed = self.grid.set_goal(node)
        else:
            changed = False
        if changed:
            self.reset_search(clear_history=True)

    def perform_button(self, name):
        if name.startswith("algo:"):
            self.select_algorithm(name.split(":", 1)[1])
        elif name.startswith("brush:"):
            self.brush = name.split(":", 1)[1]
        elif name == "run":
            self.toggle_run()
        elif name == "step":
            self.step_once()
        elif name == "reset":
            self.reset_search()
        elif name == "demo":
            self.grid.load_demo()
            self.reset_search(clear_history=True)
        elif name == "clear":
            self.grid.clear()
            self.reset_search(clear_history=True)
        elif name == "speed_up":
            self.speed_index = min(len(SPEEDS) - 1, self.speed_index + 1)
        elif name == "speed_down":
            self.speed_index = max(0, self.speed_index - 1)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.keep_running = False
        elif key in (pygame.K_1, pygame.K_KP1):
            self.select_algorithm("BFS")
        elif key in (pygame.K_2, pygame.K_KP2):
            self.select_algorithm("Dijkstra")
        elif key in (pygame.K_3, pygame.K_KP3):
            self.select_algorithm("A*")
        elif key == pygame.K_SPACE:
            self.toggle_run()
        elif key == pygame.K_n:
            self.step_once()
        elif key == pygame.K_r:
            self.reset_search()
        elif key == pygame.K_c:
            self.grid.clear()
            self.reset_search(clear_history=True)
        elif key == pygame.K_d:
            self.grid.load_demo()
            self.reset_search(clear_history=True)
        elif key == pygame.K_UP:
            self.speed_index = min(len(SPEEDS) - 1, self.speed_index + 1)
        elif key == pygame.K_DOWN:
            self.speed_index = max(0, self.speed_index - 1)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.keep_running = False
            elif event.type == pygame.VIDEORESIZE:
                w, h = max(MIN_WIDTH, event.w), max(MIN_HEIGHT, event.h)
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5) and self.renderer.sidebar_rect.collidepoint(event.pos):
                    self.renderer.scroll_sidebar(-1 if event.button == 4 else 1)
                elif event.button == 1:
                    key = self.renderer.button_at(event.pos)
                    if key:
                        self.perform_button(key)
                    else:
                        self.edit_cell(self.renderer.cell_at(event.pos, self.grid), 1)
                elif event.button == 3:
                    self.edit_cell(self.renderer.cell_at(event.pos, self.grid), 3)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:
                    self.edit_cell(self.renderer.cell_at(event.pos, self.grid), 1, dragging=True)
                elif event.buttons[2]:
                    self.edit_cell(self.renderer.cell_at(event.pos, self.grid), 3, dragging=True)
            elif event.type == pygame.MOUSEWHEEL:
                if self.renderer.sidebar_rect.collidepoint(pygame.mouse.get_pos()):
                    self.renderer.scroll_sidebar(-event.y)

    def update(self, dt):
        if not self.running:
            return
        self.accumulator += min(dt, 0.1) * SPEEDS[self.speed_index]
        num_steps = min(int(self.accumulator), 500)
        self.accumulator -= num_steps
        for _ in range(num_steps):
            if not self.running:
                break
            self.advance()

    def run(self):
        try:
            while self.keep_running:
                dt = self.clock.tick(FPS) / 1000.0
                self.handle_events()
                self.update(dt)
                self.renderer.draw(self.screen, self)
                pygame.display.flip()
        finally:
            pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()
