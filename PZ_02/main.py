import pygame

# ------------------------------------------------------------
# Настройки окна
# ------------------------------------------------------------

WIDTH = 1000
HEIGHT = 650
FPS = 60
UI_HEIGHT = 88
# ------------------------------------------------------------
# Состояния заказа
# ------------------------------------------------------------

NO_ORDER = "NO_ORDER"
WAITING = "WAITING"
READY = "READY"
DONE = "DONE"

# ------------------------------------------------------------
# Цвета
# ------------------------------------------------------------

BG_COLOR = (245, 240, 230)

UI_PANEL_COLOR = (232, 227, 218)
UI_BORDER_COLOR = (90, 90, 90)

ENTRANCE_COLOR = (185, 220, 185)
COUNTER_COLOR = (180, 125, 85)
CASHIER_COLOR = (125, 125, 140)
PICKUP_COLOR = (245, 210, 155)
READY_PICKUP_COLOR = (140, 220, 150)

BORDER_COLOR = (60, 60, 60)
TEXT_COLOR = (35, 35, 35)
MUTED_TEXT_COLOR = (80, 80, 80)
ERROR_COLOR = (170, 60, 50)
SUCCESS_COLOR = (40, 120, 70)

MENU_PANEL_COLOR = (250, 246, 238)
MENU_OVERLAY_COLOR = (0, 0, 0, 70)

# ------------------------------------------------------------
# Зоны пекарни
# ------------------------------------------------------------

ENTRANCE_RECT = pygame.Rect(40, 520, 180, 90)

COUNTER_RECT = pygame.Rect(320, 180, 360, 90)
CASHIER_RECT = pygame.Rect(760, 180, 150, 110)

PICKUP_RECT = pygame.Rect(620, 470, 260, 100)

# Зона, в которой клиент может сделать заказ
COUNTER_INTERACTION_RECT = pygame.Rect(330, 285, 340, 85)

# Зона, в которой клиент может получить готовый заказ
PICKUP_INTERACTION_RECT = pygame.Rect(590, 440, 320, 150)

# Препятствия
OBSTACLES = [
    COUNTER_RECT,
    CASHIER_RECT,
]

# ------------------------------------------------------------
# Товары
# ------------------------------------------------------------

PRODUCTS_TEMPLATE = [
    {
        "name": "Хлеб",
        "price": 70,
        "stock": 3,
        "cook_time": 0.0,
    },
    {
        "name": "Булочка",
        "price": 90,
        "stock": 4,
        "cook_time": 0.0,
    },
    {
        "name": "Сэндвич",
        "price": 180,
        "stock": 2,
        "cook_time": 5.0,
    },
    {
        "name": "Кофе",
        "price": 140,
        "stock": 5,
        "cook_time": 3.0,
    },
]

PRODUCT_KEYS = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
    pygame.K_4: 3,
    pygame.K_KP1: 0,
    pygame.K_KP2: 1,
    pygame.K_KP3: 2,
    pygame.K_KP4: 3,
}

# ------------------------------------------------------------
# Создание начального состояния
# ------------------------------------------------------------

def create_initial_state():
    """
    Создаёт начальное состояние приложения.
    """

    return {
        "running": True,
        "fps": 0.0,

        "money": 420,

        "products": [product.copy() for product in PRODUCTS_TEMPLATE],

        "menu_open": False,
        "message": "",

        "current_order": None,
        "order_state": NO_ORDER,

        "cook_time_left": 0.0,
        "cook_time_total": 0.0,

        "player": {
            "position": pygame.Vector2(150, 350),
            "radius": 22,
            "speed": 260.0,
            "color_index": 0,
            "colors": [
                (70, 130, 220),
                (60, 180, 110),
                (220, 90, 80),
                (230, 175, 60),
            ],
        },
    }

# ------------------------------------------------------------
# Вспомогательные функции состояния
# ------------------------------------------------------------

def get_player_rect(state):
    """
    Возвращает прямоугольник клиента по его текущим координатам.
    """

    player = state["player"]
    radius = player["radius"]

    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = (
        round(player["position"].x),
        round(player["position"].y),
    )

    return rect


def get_message_color(message):
    # Ошибки показываем красным, успешные действия — зелёным,
    # обычные подсказки — нейтральным цветом.
    error_messages = {
        "Недостаточно денег",
        "Товар закончился",
        "Сначала завершите текущий заказ",
        "Сначала получите текущий заказ",
    }

    success_messages = {
        "Заказ принят",
        "Заказ готов",
        "Заказ получен",
    }

    if message in error_messages:
        return ERROR_COLOR

    if message in success_messages:
        return SUCCESS_COLOR

    return MUTED_TEXT_COLOR


def reset_completed_order(state):
    # После полученного заказа подготавливаем состояние к новому заказу.
    state["current_order"] = None
    state["order_state"] = NO_ORDER
    state["cook_time_left"] = 0.0
    state["cook_time_total"] = 0.0


def can_order(state):
    """
    Проверяет, может ли клиент сейчас открыть меню заказа.
    """

    if state["menu_open"]:
        return False

    # Если заказ готовится или уже готов, новый заказывать нельзя
    if state["order_state"] in (WAITING, READY):
        return False

    player_rect = get_player_rect(state)
    return player_rect.colliderect(COUNTER_INTERACTION_RECT)


def can_pickup(state):
    """
    Проверяет, может ли клиент сейчас получить заказ.
    """

    if state["order_state"] != READY:
        return False

    player_rect = get_player_rect(state)
    return player_rect.colliderect(PICKUP_INTERACTION_RECT)


def try_order(state, product_index):
    """
    Пытается оформить заказ выбранного товара.
    """

    # Если уже есть активный заказ, новый не оформляем
    if state["order_state"] in (WAITING, READY):
        state["message"] = "Сначала завершите текущий заказ"
        return

    product = state["products"][product_index]

    if product["stock"] <= 0:
        state["message"] = "Товар закончился"
        return

    if state["money"] < product["price"]:
        state["message"] = "Недостаточно денег"
        return

    # Успешный заказ
    state["money"] -= product["price"]
    product["stock"] -= 1

    state["current_order"] = product["name"]
    state["menu_open"] = False
    state["message"] = "Заказ принят"

    if product["cook_time"] > 0:
        state["order_state"] = WAITING
        state["cook_time_total"] = float(product["cook_time"])
        state["cook_time_left"] = float(product["cook_time"])
    else:
        state["order_state"] = READY
        state["cook_time_total"] = 0.0
        state["cook_time_left"] = 0.0

# ------------------------------------------------------------
# Обработка событий
# ------------------------------------------------------------

def handle_events(state):
    """
    Обрабатывает дискретные события:
    - закрытие окна;
    - Esc;
    - Space;
    - E;
    - выбор товара в меню.
    """

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False

        elif event.type == pygame.KEYDOWN:
            # Выход
            if event.key == pygame.K_ESCAPE:
                state["running"] = False

            # Смена цвета клиента
            elif event.key == pygame.K_SPACE:
                player = state["player"]
                player["color_index"] = (
                    player["color_index"] + 1
                ) % len(player["colors"])

            # Взаимодействие
            elif event.key == pygame.K_e:
                # Если меню открыто — закрываем его без покупки
                if state["menu_open"]:
                    state["menu_open"] = False
                    state["message"] = "Меню закрыто"

                # Если можно получить заказ — получаем
                elif can_pickup(state):
                    state["order_state"] = DONE
                    state["message"] = "Заказ получен"

                # Если предыдущий заказ уже получен, начинаем новый цикл заказа
                elif can_order(state):
                    if state["order_state"] == DONE:
                        reset_completed_order(state)

                    state["menu_open"] = True
                    state["message"] = "Выберите товар"

                else:
                    if state["order_state"] in (WAITING, READY):
                        state["message"] = "Сначала получите текущий заказ"
                    else:
                        state["message"] = "Подойдите к прилавку"

            # Выбор товара в меню
            elif state["menu_open"] and event.key in PRODUCT_KEYS:
                product_index = PRODUCT_KEYS[event.key]
                try_order(state, product_index)

# ------------------------------------------------------------
# Движение клиента
# ------------------------------------------------------------

def handle_movement(state, dt):
    """
    Обрабатывает непрерывное движение клиента.
    """

    # Пока меню открыто, клиент остаётся на месте.
    if state["menu_open"]:
        return

    keys = pygame.key.get_pressed()

    direction = pygame.Vector2(0, 0)

    if keys[pygame.K_w]:
        direction.y -= 1

    if keys[pygame.K_s]:
        direction.y += 1

    if keys[pygame.K_a]:
        direction.x -= 1

    if keys[pygame.K_d]:
        direction.x += 1

    if direction.length_squared() == 0:
        return

    # Нормализация, чтобы диагональ не была быстрее
    direction = direction.normalize()

    player = state["player"]
    radius = player["radius"]
    speed = player["speed"]
    position = player["position"]

    # --------------------------------------------------------
    # Движение по X
    # --------------------------------------------------------

    new_x = position.x + direction.x * speed * dt
    new_x = max(radius, min(WIDTH - radius, new_x))

    test_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    test_rect.center = (round(new_x), round(position.y))

    blocked_x = any(
        test_rect.colliderect(obstacle)
        for obstacle in OBSTACLES
    )

    if not blocked_x:
        position.x = new_x

    # --------------------------------------------------------
    # Движение по Y
    # --------------------------------------------------------

    new_y = position.y + direction.y * speed * dt
    new_y = max(UI_HEIGHT + radius, min(HEIGHT - radius, new_y))

    test_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    test_rect.center = (round(position.x), round(new_y))

    blocked_y = any(
        test_rect.colliderect(obstacle)
        for obstacle in OBSTACLES
    )

    if not blocked_y:
        position.y = new_y

# ------------------------------------------------------------
# Обновление заказа
# ------------------------------------------------------------

def update_order(state, dt):
    """
    Обновляет состояние заказа во времени.

    Здесь используется таймер без time.sleep().
    """

    if state["order_state"] == WAITING:
        state["cook_time_left"] -= dt

        if state["cook_time_left"] <= 0:
            state["cook_time_left"] = 0.0
            state["order_state"] = READY
            state["message"] = "Заказ готов"

# ------------------------------------------------------------
# Вспомогательные функции отрисовки
# ------------------------------------------------------------

def draw_label(screen, font, text, rect, text_color=TEXT_COLOR):
    """
    Рисует текст по центру прямоугольника.
    """

    label = font.render(text, True, text_color)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)


def draw_centered_text(screen, font, text, center, text_color=TEXT_COLOR):
    """
    Рисует текст с центрированием по точке.
    """

    label = font.render(text, True, text_color)
    label_rect = label.get_rect(center=center)
    screen.blit(label, label_rect)


def draw_zone(
    screen,
    font,
    rect,
    color,
    label,
    border_color=BORDER_COLOR,
):
    """
    Рисует зону с рамкой и подписью.
    """

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=12,
    )

    pygame.draw.rect(
        screen,
        border_color,
        rect,
        width=2,
        border_radius=12,
    )

    draw_label(screen, font, label, rect)

# ------------------------------------------------------------
# Отрисовка меню
# ------------------------------------------------------------

def draw_menu(screen, fonts, state):
    """
    Рисует меню заказа.
    """

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(MENU_OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    panel_width = 680
    panel_height = 420

    panel = pygame.Rect(0, 0, panel_width, panel_height)
    panel.center = (WIDTH // 2, HEIGHT // 2)

    pygame.draw.rect(
        screen,
        MENU_PANEL_COLOR,
        panel,
        border_radius=14,
    )

    pygame.draw.rect(
        screen,
        BORDER_COLOR,
        panel,
        width=2,
        border_radius=14,
    )

    title_font = fonts["title"]
    normal_font = fonts["normal"]
    small_font = fonts["small"]

    draw_centered_text(
        screen,
        title_font,
        "Меню заказа",
        (panel.centerx, panel.y + 35),
        TEXT_COLOR,
    )

    money_text = normal_font.render(
        f"Деньги: {state['money']} руб.",
        True,
        TEXT_COLOR,
    )

    screen.blit(money_text, (panel.x + 30, panel.y + 65))

    y = panel.y + 110

    for i, product in enumerate(state["products"]):
        line = (
            f"{i + 1}. {product['name']} — {product['price']} руб. | "
            f"Остаток: {product['stock']} | "
            f"Время: {product['cook_time']:.0f} с"
        )

        color = TEXT_COLOR if product["stock"] > 0 else ERROR_COLOR

        line_text = normal_font.render(line, True, color)
        screen.blit(line_text, (panel.x + 30, y))

        y += 42

    if state["message"]:
        message_text = small_font.render(
            state["message"],
            True,
            get_message_color(state["message"]),
        )

        screen.blit(
            message_text,
            message_text.get_rect(
                center=(panel.centerx, panel.bottom - 70)
            ),
        )

    hint_text = small_font.render(
        "1–4 — выбрать | E — закрыть без покупки",
        True,
        MUTED_TEXT_COLOR,
    )

    screen.blit(
        hint_text,
        hint_text.get_rect(
            center=(panel.centerx, panel.bottom - 35)
        ),
    )
# ------------------------------------------------------------
# Индикатор приготовления
# ------------------------------------------------------------

def draw_cooking_indicator(screen, fonts, state):
    """
    Отображает индикатор приготовления:
    - название товара;
    - оставшееся время;
    - графическую полосу прогресса.

    Функция только читает состояние, но не изменяет его.
    """

    if state["order_state"] == WAITING:
        panel = pygame.Rect(WIDTH // 2 - 180, 100, 360, 86)

        pygame.draw.rect(
            screen,
            MENU_PANEL_COLOR,
            panel,
            border_radius=10,
        )

        pygame.draw.rect(
            screen,
            BORDER_COLOR,
            panel,
            width=2,
            border_radius=10,
        )

        font = fonts["normal"]
        small_font = fonts["small"]

        title = font.render(
            f"Готовится: {state['current_order']}",
            True,
            TEXT_COLOR,
        )
        screen.blit(title, (panel.x + 14, panel.y + 8))

        time_label = small_font.render(
            f"Осталось: {state['cook_time_left']:.1f} с",
            True,
            MUTED_TEXT_COLOR,
        )
        screen.blit(time_label, (panel.x + 14, panel.y + 38))

        # Полоса прогресса
        bar_rect = pygame.Rect(
            panel.x + 14,
            panel.y + 62,
            panel.width - 28,
            14,
        )

        pygame.draw.rect(
            screen,
            (210, 210, 210),
            bar_rect,
            border_radius=6,
        )

        if state["cook_time_total"] > 0:
            progress = 1.0 - (
                state["cook_time_left"] / state["cook_time_total"]
            )
        else:
            progress = 1.0

        progress = max(0.0, min(1.0, progress))
        filled_width = int(bar_rect.width * progress)

        if filled_width > 0:
            fill_rect = pygame.Rect(
                bar_rect.x,
                bar_rect.y,
                filled_width,
                bar_rect.height,
            )

            pygame.draw.rect(
                screen,
                SUCCESS_COLOR,
                fill_rect,
                border_radius=6,
            )

    elif state["order_state"] == READY:
        font = fonts["normal"]

        label = font.render(
            f"Заказ готов: {state['current_order']}. Подойдите к зоне выдачи",
            True,
            SUCCESS_COLOR,
        )

        panel = pygame.Rect(WIDTH // 2 - 230, 100, 460, 40)

        pygame.draw.rect(
            screen,
            MENU_PANEL_COLOR,
            panel,
            border_radius=10,
        )

        pygame.draw.rect(
            screen,
            SUCCESS_COLOR,
            panel,
            width=2,
            border_radius=10,
        )

        screen.blit(label, label.get_rect(center=panel.center))


# ------------------------------------------------------------
# Отрисовка сцены
# ------------------------------------------------------------

def draw_scene(screen, fonts, state):
    """
    Рисует сцену пекарни.

    Эта функция только отображает состояние,
    но не изменяет его.
    """


    screen.fill(BG_COLOR)

    font = fonts["normal"]

    # Вход
    draw_zone(
        screen,
        font,
        ENTRANCE_RECT,
        ENTRANCE_COLOR,
        "Вход",
    )

    # Прилавок
    draw_zone(
        screen,
        font,
        COUNTER_RECT,
        COUNTER_COLOR,
        "Прилавок",
    )

    # Касса
    draw_zone(
        screen,
        font,
        CASHIER_RECT,
        CASHIER_COLOR,
        "Касса",
    )

    # Зона выдачи
    if state["order_state"] == READY:
        pickup_color = READY_PICKUP_COLOR
        pickup_label = "Выдача: готово"
        pickup_border = SUCCESS_COLOR
    else:
        pickup_color = PICKUP_COLOR
        pickup_label = "Зона выдачи"
        pickup_border = BORDER_COLOR

    draw_zone(
        screen,
        font,
        PICKUP_RECT,
        pickup_color,
        pickup_label,
        border_color=pickup_border,
    )

    # Клиент
    player = state["player"]

    player_pos = (
        round(player["position"].x),
        round(player["position"].y),
    )

    player_color = player["colors"][player["color_index"]]

    pygame.draw.circle(
        screen,
        player_color,
        player_pos,
        player["radius"],
    )

    pygame.draw.circle(
        screen,
        BORDER_COLOR,
        player_pos,
        player["radius"],
        width=2,
    )

    # Подсказка для заказа
    if can_order(state):
        draw_centered_text(
            screen,
            font,
            "E — сделать заказ",
            (
                COUNTER_INTERACTION_RECT.centerx,
                COUNTER_INTERACTION_RECT.top - 15,
            ),
            SUCCESS_COLOR,
        )

    # Подсказка для получения заказа
    if can_pickup(state):
        draw_centered_text(
            screen,
            font,
            "E — получить заказ",
            (
                PICKUP_INTERACTION_RECT.centerx,
                PICKUP_INTERACTION_RECT.top - 15,
            ),
            SUCCESS_COLOR,
        )

    # Меню заказа
    if state["menu_open"]:
        draw_menu(screen, fonts, state)






# ------------------------------------------------------------
# Получение текста доступного действия
# ------------------------------------------------------------

def get_action_text(state):
    """
    Возвращает текст доступного действия.
    """

    if state["menu_open"]:
        return "1–4 — выбрать | E — закрыть меню"

    if can_pickup(state):
        return "E — получить заказ"

    if can_order(state):
        return "E — сделать заказ"

    if state["order_state"] == READY:
        return "Подойдите к зоне выдачи"

    if state["order_state"] == WAITING:
        return "Ожидание приготовления заказа"

    if state["order_state"] == DONE:
        return "Заказ получен. Можно сделать новый заказ"

    return "Подойдите к прилавку"

# ------------------------------------------------------------
# Отрисовка интерфейса
# ------------------------------------------------------------

def draw_ui(screen, fonts, state):
    """
    Рисует информационную панель.

    Эта функция только отображает состояние,
    но не изменяет его.
    """

    panel_rect = pygame.Rect(0, 0, WIDTH, UI_HEIGHT)

    pygame.draw.rect(
        screen,
        UI_PANEL_COLOR,
        panel_rect,
    )

    pygame.draw.line(
        screen,
        UI_BORDER_COLOR,
        (0, UI_HEIGHT),
        (WIDTH, UI_HEIGHT),
        width=2,
    )

    font = fonts["normal"]
    small_font = fonts["small"]

    # Первая строка
    money_text = font.render(
        f"Money: {state['money']} ₽",
        True,
        TEXT_COLOR,
    )

    order_name = state["current_order"]
    if order_name is None:
        order_name = "-"

    order_text = font.render(
        f"Order: {order_name}",
        True,
        TEXT_COLOR,
    )

    state_text = font.render(
        f"State: {state['order_state']}",
        True,
        TEXT_COLOR,
    )

    if state["order_state"] == WAITING:
        cooking_text = font.render(
            f"Cooking: {state['cook_time_left']:.1f} s",
            True,
            TEXT_COLOR,
        )
    else:
        cooking_text = font.render(
            "Cooking: -",
            True,
            TEXT_COLOR,
        )

    screen.blit(money_text, (20, 12))
    screen.blit(order_text, (220, 12))
    screen.blit(state_text, (460, 12))
    screen.blit(cooking_text, (680, 12))

    # Вторая строка
    fps_text = small_font.render(
        f"FPS: {state['fps']:.0f}",
        True,
        MUTED_TEXT_COLOR,
    )

    action_text = small_font.render(
        f"Действие: {get_action_text(state)}",
        True,
        MUTED_TEXT_COLOR,
    )

    screen.blit(fps_text, (20, 52))
    screen.blit(action_text, (140, 52))

    # Сообщение внизу экрана, если меню закрыто
    if not state["menu_open"] and state["message"]:
        message_text = small_font.render(
            state["message"],
            True,
            get_message_color(state["message"]),
        )

        screen.blit(message_text, (20, HEIGHT - 32))

# ------------------------------------------------------------
# Главная функция
# ------------------------------------------------------------

def main():
    """
    Главная функция приложения.
    """

    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Симулятор пекарни. Этап 1")

    clock = pygame.time.Clock()

    fonts = {
        "normal": pygame.font.Font(None, 28),
        "small": pygame.font.Font(None, 22),
        "title": pygame.font.Font(None, 36),
    }

    state = create_initial_state()

    try:
        while state["running"]:
            dt = clock.tick(FPS) / 1000.0
            state["fps"] = clock.get_fps()

            # События
            handle_events(state)

            # Движение
            handle_movement(state, dt)

            # Обновление заказа
            update_order(state, dt)

            # Отрисовка сцены
            draw_scene(screen, fonts, state)

            # Индикатор приготовления / готовности заказа
            draw_cooking_indicator(screen, fonts, state)

            # Отрисовка интерфейса
            draw_ui(screen, fonts, state)

            # Показ кадра
            pygame.display.flip()

    finally:
        pygame.quit()


# ------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------

if __name__ == "__main__":
    main()