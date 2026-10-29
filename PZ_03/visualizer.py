import pygame

from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, ALGORITHM_NAMES,
    BACKGROUND, PANEL, PANEL_BORDER, TEXT, SECONDARY_TEXT,
    NORMAL, COMPARING, SWAPPING, MINIMUM, SORTED,
    ACTIVE_RANGE, MIDDLE, FOUND, EXCLUDED,
    VALUE_MAX,
)


# Область столбцов: x = 48..877; по высоте ниже строки состояния.
CHART_X = 48
CHART_WIDTH = 828
CHART_BOTTOM = 547
BAR_MAX_HEIGHT = 326


def draw_text(screen, font, text, x, y, color=TEXT):
    image = font.render(str(text), True, color)
    screen.blit(image, (x, y))


def draw_array(screen, values, step, mode, fonts):
    if not values:
        return

    bar_space = CHART_WIDTH / len(values)
    bar_width = max(2, int(bar_space) - 4)
    action = step.get("type") if step else None
    indices = step.get("indices", ()) if step else ()

    for i, value in enumerate(values):
        x = round(CHART_X + i * bar_space + (bar_space - bar_width) / 2)
        height = round(value / VALUE_MAX * BAR_MAX_HEIGHT)
        y = CHART_BOTTOM - height
        rect = pygame.Rect(x, y, bar_width, height)
        color = NORMAL

        if mode == 1:
            if step and i >= step.get("sorted_from", len(values)):
                color = SORTED
            if action == "compare" and i in indices:
                color = COMPARING
            elif action == "swap" and i in indices:
                color = SWAPPING

        elif mode == 2:
            if step and i < step.get("sorted_count", 0):
                color = SORTED
            if action == "swap" and i in indices:
                color = SWAPPING
            elif step and i == step.get("min_index"):
                color = MINIMUM
            if step and i == step.get("current") and action == "compare":
                color = COMPARING
            elif step and i == step.get("current") and action == "new_min":
                color = MINIMUM

        else:
            if step:
                left = step.get("left", 0)
                right = step.get("right", len(values) - 1)
                if i < left or i > right:
                    color = EXCLUDED
                else:
                    color = ACTIVE_RANGE
                if i == step.get("mid"):
                    color = MIDDLE
                if i == step.get("found_index"):
                    color = FOUND
            else:
                color = ACTIVE_RANGE

        pygame.draw.rect(screen, color, rect, border_radius=2)

        if mode == 2 and step:
            # Начало рабочей области отмечено белой рамкой.
            if i == step.get("start") and action != "pass_complete":
                pygame.draw.rect(screen, TEXT, rect, 2, border_radius=2)
            # Если проверяемый элемент одновременно является минимумом,
            # оранжевая рамка показывает обе роли элемента.
            if i == step.get("min_index") and i == step.get("current"):
                pygame.draw.rect(screen, MINIMUM, rect, 2, border_radius=2)

        if mode == 3 and step:
            if i == step.get("left") or i == step.get("right"):
                pygame.draw.rect(screen, TEXT, rect, 2, border_radius=2)

        if len(values) <= 30:
            label = fonts["tiny"].render(str(value), True, TEXT)
            label_x = x + (bar_width - label.get_width()) // 2
            screen.blit(label, (label_x, y - 21))

    pygame.draw.line(
        screen, PANEL_BORDER, (CHART_X, CHART_BOTTOM + 2),
        (CHART_X + CHART_WIDTH, CHART_BOTTOM + 2), 2,
    )


def draw_statistics(screen, step, mode, target, state, fonts):
    draw_text(screen, fonts["section"], "STATISTICS", 942, 152)
    pygame.draw.line(screen, PANEL_BORDER, (942, 189), (1190, 189), 1)

    if mode in (1, 2):
        stats = [
            ("Comparisons", step.get("comparisons", 0) if step else 0),
            ("Swaps", step.get("swaps", 0) if step else 0),
            ("Pass", step.get("pass", 0) if step else 0),
            ("Steps", step.get("steps", 0) if step else 0),
        ]
        for i, (label, value) in enumerate(stats):
            y = 206 + i * 45
            draw_text(screen, fonts["body"], label, 942, y, SECONDARY_TEXT)
            draw_text(screen, fonts["body"], value, 1120, y, TEXT)

        if mode == 2:
            draw_text(screen, fonts["small"], "Selection indices:", 942, 404, SECONDARY_TEXT)
            for row, key in enumerate(("start", "current", "min_index")):
                value = step.get(key) if step else None
                title = {"start": "Start", "current": "Current", "min_index": "Minimum"}[key]
                draw_text(
                    screen, fonts["small"],
                    f"{title}: {value if value is not None else '-'}",
                    942, 435 + row * 32,
                )
    else:
        left = step.get("left", 0) if step else 0
        right = step.get("right", -1) if step else -1
        mid = step.get("mid") if step else None
        result = step.get("result", "Not started") if step else "Not started"
        stats = [
            ("Target", str(target)),
            ("Comparisons", str(step.get("comparisons", 0) if step else 0)),
            ("Steps", str(step.get("steps", 0) if step else 0)),
            ("Current range", f"[{left}, {right}]" if step and left <= right else "-"),
            ("Left", str(left) if step and left <= right else "-"),
            ("Mid", str(mid) if mid is not None else "-"),
            ("Right", str(right) if step and left <= right else "-"),
        ]
        for i, (label, value) in enumerate(stats):
            y = 200 + i * 39
            draw_text(screen, fonts["small"], label, 942, y, SECONDARY_TEXT)
            draw_text(screen, fonts["small"], value, 1090, y, TEXT)

        draw_text(screen, fonts["small"], "Result", 942, 491, SECONDARY_TEXT)
        draw_text(
            screen, fonts["small"], result, 942, 518,
            FOUND if step and step.get("found_index") is not None else TEXT,
        )


def draw_legend(screen, fonts):
    draw_text(screen, fonts["section"], "COLOR LEGEND", 43, 606)
    items = [
        ("Normal", NORMAL),
        ("Comparing", COMPARING),
        ("Swapping", SWAPPING),
        ("Minimum", MINIMUM),
        ("Sorted", SORTED),
        ("Active range", ACTIVE_RANGE),
        ("Mid", MIDDLE),
        ("Found", FOUND),
        ("Excluded", EXCLUDED),
    ]
    for i, (label, color) in enumerate(items):
        row = i // 5
        col = i % 5
        x = 44 + col * 234
        y = 644 + row * 35
        pygame.draw.rect(screen, color, pygame.Rect(x, y, 17, 17), border_radius=2)
        draw_text(screen, fonts["small"], label, x + 26, y - 2)


def draw_screen(screen, values, step, mode, state, target, editing, target_input, fonts):
    screen.fill(BACKGROUND)
    draw_text(screen, fonts["title"], "ALGORITHM VISUALIZER", 28, 18)
    draw_text(screen, fonts["section"], ALGORITHM_NAMES[mode], 28, 65)
    draw_text(screen, fonts["small"], f"Status: {state}", 28, 100, SECONDARY_TEXT)

    pygame.draw.rect(screen, PANEL, pygame.Rect(26, 128, 875, 455), border_radius=9)
    pygame.draw.rect(
        screen, PANEL_BORDER, pygame.Rect(26, 128, 875, 455), 1, border_radius=9,
    )
    pygame.draw.rect(screen, PANEL, pygame.Rect(914, 128, 300, 455), border_radius=9)
    pygame.draw.rect(
        screen, PANEL_BORDER, pygame.Rect(914, 128, 300, 455), 1, border_radius=9,
    )

    message = step.get("message", "Ready. SPACE to start; N for one step.") if step else (
        "Ready. SPACE to start; N for one step."
    )
    if editing:
        message = f"Enter target: {target_input}_   (ENTER to confirm, BACKSPACE to delete)"
    elif mode == 3 and state == "IDLE":
        message = "Array sorted for search. Press T to set target."
    draw_text(screen, fonts["body"], message, 48, 148, SECONDARY_TEXT)

    draw_array(screen, values, step, mode, fonts)
    draw_statistics(screen, step, mode, target, state, fonts)

    pygame.draw.rect(screen, PANEL, pygame.Rect(26, 596, 1188, 110), border_radius=9)
    pygame.draw.rect(
        screen, PANEL_BORDER, pygame.Rect(26, 596, 1188, 110), 1, border_radius=9,
    )
    draw_legend(screen, fonts)

    pygame.draw.rect(screen, PANEL, pygame.Rect(26, 718, 1188, 81), border_radius=9)
    pygame.draw.rect(
        screen, PANEL_BORDER, pygame.Rect(26, 718, 1188, 81), 1, border_radius=9,
    )
    draw_text(
        screen, fonts["small"],
        "1 Bubble   2 Selection   3 Binary   SPACE Start/Pause   N Next step   R Reset/New array",
        44, 733,
    )
    draw_text(
        screen, fonts["small"],
        "T Set target (Binary)   0-9 Enter digits   BACKSPACE Delete   ENTER Apply   ESC Exit",
        44, 764, SECONDARY_TEXT,
    )
    pygame.display.flip()
