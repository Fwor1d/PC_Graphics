
import argparse
from pathlib import Path

import pygame

from objects import House
from renderer import Renderer
import settings as c


def update(house, keys, dt):
    """Удерживаемые клавиши; единичные переключатели обрабатывает KEYDOWN."""
    s = house.state
    s.tx += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * c.MOVE_SPEED * dt
    s.ty += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * c.MOVE_SPEED * dt
    s.angle += (keys[pygame.K_e] - keys[pygame.K_q]) * c.ROTATE_SPEED * dt
    s.sx += (keys[pygame.K_x] - keys[pygame.K_z]) * c.SCALE_SPEED * dt
    s.sy += (keys[pygame.K_d] - keys[pygame.K_a]) * c.SCALE_SPEED * dt
    s.kx += (keys[pygame.K_l] - keys[pygame.K_j]) * c.SHEAR_SPEED * dt
    s.ky += (keys[pygame.K_o] - keys[pygame.K_u]) * c.SHEAR_SPEED * dt
    s.constrain()


def handle_event(event, house, renderer, keys):
    """Возвращает False при запросе закрытия."""
    if event.type == pygame.QUIT:
        return False
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return False
        if event.key == pygame.K_r:
            house.reset()
        elif event.key == pygame.K_m:
            house.state.mode = "B" if house.state.mode == "A" else "A"
        elif event.key == pygame.K_h:
            house.state.reflect_h = not house.state.reflect_h
        elif event.key == pygame.K_v:
            house.state.reflect_v = not house.state.reflect_v
        elif event.key == pygame.K_F1:
            house.demo()
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        point = renderer.screen_to_canvas(event.pos)
        if point is not None and renderer.scene.collidepoint(point):
            house.click(point, renderer.view, set_pivot=bool(keys[pygame.K_p]))
    return True


def run(frames=None, screenshot=None, demo=None):
    pygame.init()
    try:
        pygame.display.set_caption("Affine Transform Studio — ПЗ №5")
        desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
        factor = min(1.0, (desktop_w - 80) / c.WIDTH, (desktop_h - 120) / c.HEIGHT)
        factor = max(0.25, factor)
        window = pygame.display.set_mode((round(c.WIDTH * factor), round(c.HEIGHT * factor)), pygame.RESIZABLE)
        renderer, house = Renderer(), House()
        if demo:
            house.demo()
            house.state.mode = demo
        clock = pygame.time.Clock()
        running, count = True, 0
        # Establish the letterbox mapping before processing the first click.
        renderer.draw(window, house)
        while running:
            dt = min(clock.tick(c.FPS) / 1000.0, 0.1)
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if not handle_event(event, house, renderer, keys):
                    running = False
            if not running:
                break
            if pygame.key.get_focused():
                update(house, keys, dt)
            renderer.draw(window, house, clock.get_fps(), bool(keys[pygame.K_p]))
            pygame.display.flip()
            count += 1
            if frames is not None and count >= frames:
                running = False
        if screenshot:
            path = Path(screenshot)
            path.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(window, str(path))
    finally:
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, help="Завершить после N кадров (проверка запуска)")
    parser.add_argument("--screenshot", help="Сохранить последний кадр окна в PNG")
    parser.add_argument("--demo", choices=("A", "B"), help="Открыть обязательный пример T(120,60), R(90°)")
    args = parser.parse_args()
    if args.frames is not None and args.frames < 1:
        parser.error("--frames must be positive")
    run(args.frames, args.screenshot, args.demo)


if __name__ == "__main__":
    main()
