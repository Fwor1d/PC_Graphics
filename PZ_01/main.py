from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, UnidentifiedImageError


BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "timka.png"
OUTPUT_DIR = BASE_DIR / "output"
TARGET_WIDTH = 800
DARK_DELTA = -55
LIGHT_DELTA = 55
DEFAULT_CUSTOM_ANGLE = 30.0


def load_image(path: Path) -> tuple[Image.Image, str]:
    """Загружает изображение полностью и возвращает его вместе с форматом файла."""
    if not path.is_file():
        raise FileNotFoundError(f"Файл не найден: {path.resolve()}")
    try:
        with Image.open(path) as source:
            image_format = source.format or "неизвестен"
            source.load()
            return source.copy(), image_format
    except UnidentifiedImageError as exc:
        raise ValueError(f"Файл не является поддерживаемым изображением: {path}") from exc


def print_image_info(path: Path, image: Image.Image, image_format: str) -> None:
    """Выводит свойства Pillow-изображения."""
    has_alpha = "A" in image.getbands()
    print("\n=== Задание 1. Свойства изображения ===")
    print(f"Имя файла: {path.name}")
    print(f"Формат: {image_format}")
    print(f"Размер image.size (ширина, высота): {image.size}")
    print(f"Цветовой режим Pillow: {image.mode}")
    print(f"Ширина: {image.width}")
    print(f"Высота: {image.height}")
    print(f"Альфа-канал: {'есть' if has_alpha else 'отсутствует'}")


def print_array_info(image_array: np.ndarray) -> None:
    """Выводит характеристики массива и RGB выбранных пикселей."""
    channel_count = 1 if image_array.ndim == 2 else image_array.shape[2]
    height, width = image_array.shape[:2]
    points = [(0, 0), (width // 2, height // 2), (width - 1, height - 1)]
    print("\n=== NumPy-представление RGB ===")
    print(f"shape (высота, ширина, каналы): {image_array.shape}")
    print(f"dtype: {image_array.dtype}")
    print(f"Минимум: {image_array.min()}")
    print(f"Максимум: {image_array.max()}")
    print(f"Количество каналов: {channel_count}")
    for x, y in points:
        print(f"RGB пикселя (x={x}, y={y}): {tuple(image_array[y, x])}")
    print("image.size хранит (ширину, высоту), а array.shape — "
          "(высоту, ширину, число каналов).")
    print("Поэтому пиксель массива читается как array[y, x], а не array[x, y].")


def extract_color_channels(image_array: np.ndarray) -> dict[str, np.ndarray]:
    """Выделяет R, G и B средствами NumPy и печатает статистику."""
    names = ("Красный", "Зелёный", "Синий")
    keys = ("red", "green", "blue")
    results: dict[str, np.ndarray] = {}
    print("\n=== Задание 2. Цветовые каналы ===")
    for index, (key, name) in enumerate(zip(keys, names)):
        channel = image_array[:, :, index]
        print(f"{name}: min={channel.min()}, max={channel.max()}, mean={channel.mean():.2f}")
        isolated = np.zeros_like(image_array)
        isolated[:, :, index] = channel
        results[key] = isolated
    return results


def change_brightness(image_array: np.ndarray, delta: int) -> np.ndarray:
    """Меняет яркость RGB без переполнения uint8."""
    working = image_array.astype(np.int16)
    return np.clip(working + delta, 0, 255).astype(np.uint8)


def resize_by_scale(image: Image.Image, scale: float) -> Image.Image:
    """Масштабирует изображение в заданное число раз."""
    if scale <= 0:
        raise ValueError("Коэффициент масштаба должен быть положительным")
    new_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(new_size, resample=Image.Resampling.LANCZOS)


def resize_keep_aspect(image: Image.Image, new_width: int) -> Image.Image:
    """Меняет ширину и самостоятельно вычисляет высоту с сохранением пропорций."""
    if new_width <= 0:
        raise ValueError("Новая ширина должна быть положительной")
    new_height = max(1, round(image.height * new_width / image.width))
    return image.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)


def rotate_image(image: Image.Image, angle: float, expand: bool) -> Image.Image:
    """Поворачивает изображение, задавая интерполяцию и цвет новых областей."""
    return image.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=expand,
        fillcolor=(255, 255, 255),
    )


def to_grayscale_numpy(image_array: np.ndarray) -> np.ndarray:
    """Вычисляет воспринимаемую яркость по взвешенной формуле RGB."""
    rgb = image_array.astype(np.float32)
    gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    return np.clip(np.rint(gray), 0, 255).astype(np.uint8)


def process_region(image_array: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    """Переводит только прямоугольный срез массива в оттенки серого."""
    height, width = image_array.shape[:2]
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError("Координаты области выходят за границы изображения")
    result = image_array.copy()
    gray_region = to_grayscale_numpy(result[y1:y2, x1:x2])
    result[y1:y2, x1:x2] = gray_region[:, :, np.newaxis]
    return result


def save_result(image: Image.Image | np.ndarray, filename: str) -> Path:
    """Сохраняет Pillow-изображение или массив NumPy в папку output."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = Image.fromarray(image) if isinstance(image, np.ndarray) else image
    path = OUTPUT_DIR / filename
    result.save(path)
    print(f"Сохранено: {path.name} — {result.size}")
    return path


def create_composition(items: list[tuple[Image.Image, str]]) -> Path:
    """Формирует итоговую композицию 2 x 3 с понятными заголовками."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for axis, (image, title) in zip(axes.flat, items):
        axis.imshow(image, cmap="gray" if image.mode == "L" else None)
        axis.set_title(title)
        axis.axis("off")
    fig.tight_layout()
    output_path = OUTPUT_DIR / "16_composition.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Сохранено: {output_path.name}")
    return output_path


def ask_custom_angle() -> float:
    """Запрашивает у пользователя произвольный угол; Enter выбирает 30 градусов."""
    try:
        raw_value = input(
            f"\nВведите произвольный угол поворота (Enter = {DEFAULT_CUSTOM_ANGLE:g}°): "
        ).strip()
    except EOFError:
        raw_value = ""
    if not raw_value:
        return DEFAULT_CUSTOM_ANGLE
    try:
        return float(raw_value.replace(",", "."))
    except ValueError:
        print(f"Некорректный угол. Используется {DEFAULT_CUSTOM_ANGLE:g}°.")
        return DEFAULT_CUSTOM_ANGLE


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    original, image_format = load_image(INPUT_PATH)
    print_image_info(INPUT_PATH, original, image_format)

    rgb_image = original.convert("RGB")
    image_array = np.array(rgb_image, copy=True)
    print_array_info(image_array)

    channel_images = extract_color_channels(image_array)
    save_result(channel_images["red"], "01_red_channel.png")
    save_result(channel_images["green"], "02_green_channel.png")
    save_result(channel_images["blue"], "03_blue_channel.png")

    print("\n=== Задание 3. Яркость ===")
    darker_array = change_brightness(image_array, DARK_DELTA)
    brighter_array = change_brightness(image_array, LIGHT_DELTA)
    darker = Image.fromarray(darker_array)
    brighter = Image.fromarray(brighter_array)
    save_result(darker, "04_darker.png")
    save_result(brighter, "05_brighter.png")
    print("Вычисления выполнены во временном int16, затем применён clip [0, 255].")

    print("\n=== Задание 4. Изменение размера ===")
    half_size = resize_by_scale(rgb_image, 0.5)
    one_and_half_size = resize_by_scale(rgb_image, 1.5)
    fixed_width = resize_keep_aspect(rgb_image, TARGET_WIDTH)
    save_result(half_size, "06_scaled_50_percent.png")
    save_result(one_and_half_size, "07_scaled_150_percent.png")
    save_result(fixed_width, f"08_width_{TARGET_WIDTH}.png")
    print("Ресэмплинг пересчитывает пиксели; простое изменение формы массива "
          "не является корректным изменением разрешения.")

    print("\n=== Задание 5. Поворот ===")
    custom_angle = ask_custom_angle()
    rotated_45 = rotate_image(rgb_image, 45, expand=True)
    rotated_90 = rotate_image(rgb_image, 90, expand=True)
    rotated_custom_crop = rotate_image(rgb_image, custom_angle, expand=False)
    rotated_custom_full = rotate_image(rgb_image, custom_angle, expand=True)
    save_result(rotated_45, "09_rotated_45.png")
    save_result(rotated_90, "10_rotated_90.png")
    save_result(rotated_custom_crop, "11_rotated_custom_expand_false.png")
    save_result(rotated_custom_full, "12_rotated_custom_expand_true.png")
    print(f"Произвольный угол: {custom_angle:g}°")
    print("expand=False сохраняет размер холста и обрезает углы; "
          "expand=True увеличивает холст и сохраняет изображение полностью.")

    print("\n=== Задание 6. Оттенки серого ===")
    gray_pillow = rgb_image.convert("L")
    gray_numpy_array = to_grayscale_numpy(image_array)
    gray_numpy = Image.fromarray(gray_numpy_array, mode="L")
    save_result(gray_pillow, "13_gray_pillow.png")
    save_result(gray_numpy, "14_gray_numpy.png")
    pillow_array = np.asarray(gray_pillow, dtype=np.int16)
    difference = np.abs(pillow_array - gray_numpy_array.astype(np.int16))
    print(f"Средняя абсолютная разница Pillow/NumPy: {difference.mean():.4f}")
    print(f"Максимальная разница Pillow/NumPy: {difference.max()}")
    print("Простое среднее RGB неверно передаёт воспринимаемую яркость: "
          "глаз наиболее чувствителен к зелёному и наименее — к синему.")

    print("\n=== Задание 7. Локальная обработка ===")
    x1, y1 = rgb_image.width // 4, rgb_image.height // 4
    x2, y2 = rgb_image.width * 3 // 4, rgb_image.height * 3 // 4
    region_array = process_region(image_array, x1, y1, x2, y2)
    region_image = Image.fromarray(region_array)
    save_result(region_image, "15_local_region_gray.png")
    print(f"Обработан NumPy-срез array[{y1}:{y2}, {x1}:{x2}].")

    print("\n=== Задание 8. Итоговая композиция ===")
    create_composition([
        (rgb_image, "Исходное"),
        (half_size, "Размер 50 %"),
        (rotated_45, "Поворот 45°"),
        (gray_numpy, "Grayscale (NumPy)"),
        (brighter, f"Яркость +{LIGHT_DELTA}"),
        (region_image, "Grayscale в области"),
    ])
    print(f"\nГотово. Все результаты находятся в: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
