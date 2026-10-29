import random

import pygame

from algorithms import bubble_sort_steps, selection_sort_steps, binary_search_steps
from visualizer import draw_screen
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, STEP_INTERVAL,
    ARRAY_SIZE, VALUE_MIN, VALUE_MAX,
)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Practice 03 - Algorithm Visualizer")
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.Font(None, 41),
        "section": pygame.font.Font(None, 30),
        "body": pygame.font.Font(None, 25),
        "small": pygame.font.Font(None, 22),
        "tiny": pygame.font.Font(None, 19),
    }

    mode = 1
    original = [random.randint(VALUE_MIN, VALUE_MAX) for _ in range(ARRAY_SIZE)]
    values = original.copy()
    target = original[0]
    generator = None
    step = None
    state = "IDLE"
    timer = 0.0
    editing = False
    target_input = ""

    def reset():
        nonlocal values, generator, step, state, timer
        # Старый генератор сбрасывается до подготовки нового массива.
        generator = None
        step = None
        state = "IDLE"
        timer = 0.0
        values = sorted(original) if mode == 3 else original.copy()

    def begin():
        nonlocal generator
        if mode == 1:
            generator = bubble_sort_steps(values)
        elif mode == 2:
            generator = selection_sort_steps(values)
        else:
            generator = binary_search_steps(values, target)

    def next_step():
        nonlocal generator, step, state
        if generator is None:
            begin()
        try:
            step = next(generator)
            if step["type"] == "done":
                generator = None
                state = "FINISHED"
        except StopIteration:
            generator = None
            state = "FINISHED"

    active = True
    while active:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                active = False
                break
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                active = False
                break

            if editing:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if target_input:
                        target = int(target_input)
                        editing = False
                        reset()
                elif event.key == pygame.K_BACKSPACE:
                    target_input = target_input[:-1]
                elif event.unicode.isascii() and event.unicode.isdigit():
                    if len(target_input) < 4:
                        target_input += event.unicode
                continue

            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                mode = event.key - pygame.K_0
                reset()
            elif event.key == pygame.K_r:
                reset()
                original = [random.randint(VALUE_MIN, VALUE_MAX) for _ in range(ARRAY_SIZE)]
                reset()
                target = original[0]
            elif event.key == pygame.K_t and mode == 3:
                reset()
                editing = True
                target_input = ""
            elif event.key == pygame.K_SPACE:
                if state == "RUNNING":
                    state = "PAUSED"
                elif state == "PAUSED":
                    state = "RUNNING"
                else:
                    reset()
                    begin()
                    state = "RUNNING"
            elif event.key == pygame.K_n:
                if state != "FINISHED":
                    if state == "IDLE":
                        state = "PAUSED"
                    elif state == "RUNNING":
                        state = "PAUSED"
                    timer = 0.0
                    next_step()

        if state == "RUNNING" and not editing:
            timer += dt
            if timer >= STEP_INTERVAL:
                timer -= STEP_INTERVAL
                next_step()

        draw_screen(
            screen, values, step, mode, state, target,
            editing, target_input, fonts,
        )

    pygame.quit()


if __name__ == "__main__":
    main()
