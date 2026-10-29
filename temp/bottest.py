import hashlib
import json
import re
import time
import unicodedata

from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

import pdfplumber
import requests
from bs4 import BeautifulSoup


PAGE_URL = (
    "https://www.timacad.ru/about/sveden/document/"
    "rezhim-zaniatii-obuchaiushchikhsia"
)

INSTITUTE_NAME = "Институт экономики и управления АПК"

TARGET_GROUPS = [
    "ДЭ 23-24",
    "ДЭ 24-24",
]

STATE_FILE = Path("schedule_monitor_state.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def normalize_text(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", str(text))

    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")

    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace("−", "-")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def add_cache_buster(url):
    parts = urlsplit(url)

    query = parse_qsl(
        parts.query,
        keep_blank_values=True
    )

    query.append(
        ("monitor", str(int(time.time() * 1000)))
    )

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )


def make_hash(data):
    text = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def find_pdf_url():
    print("1. Открываю страницу расписания...")

    response = requests.get(
        add_cache_buster(PAGE_URL),
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Сначала ищем по имени файла.
    # Сейчас PDF 3 курса ИЭиУ имеет ieiu-3 в URL.
    for link in soup.find_all(
        "a",
        href=True
    ):
        href = link["href"]

        if (
            "ieiu-3" in href.lower()
            and ".pdf" in href.lower()
        ):
            url = urljoin(
                PAGE_URL,
                href
            )

            print("   Найден PDF:")
            print("  ", url)

            return url

    raise RuntimeError(
        "Не удалось найти PDF ИЭиУ АПК 3 курса"
    )


def download_pdf(url):
    print("\n2. Скачиваю PDF...")

    response = requests.get(
        add_cache_buster(url),
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()

    data = response.content

    if not data.startswith(b"%PDF"):
        raise RuntimeError(
            "Сайт вернул не PDF"
        )

    print(
        f"   Размер: {len(data) / 1024:.1f} КБ"
    )

    return data


def extract_groups(pdf_data):
    print("\n3. Ищу группы ДЭ 23-24 и ДЭ 24-24...")

    result = {}

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 4,
        "join_tolerance": 4,
        "intersection_tolerance": 5,
        "text_x_tolerance": 2,
        "text_y_tolerance": 2,
    }

    with pdfplumber.open(
        BytesIO(pdf_data)
    ) as pdf:

        print(
            f"   Страниц: {len(pdf.pages)}"
        )

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):
            text = normalize_text(
                page.extract_text() or ""
            )

            if not all(
                group in text
                for group in TARGET_GROUPS
            ):
                continue

            print(
                f"   Обе группы найдены на странице {page_number}"
            )

            tables = page.extract_tables(
                table_settings
            )

            print(
                f"   Таблиц на странице: {len(tables)}"
            )

            for table in tables:
                clean_table = []

                for row in table:
                    if not row:
                        continue

                    clean_table.append(
                        [
                            normalize_text(cell)
                            for cell in row
                        ]
                    )

                for row_index, row in enumerate(
                    clean_table
                ):
                    group_columns = {}

                    for group in TARGET_GROUPS:
                        for column_index, cell in enumerate(
                            row
                        ):
                            if group in cell:
                                group_columns[group] = column_index
                                break

                    if len(group_columns) != 2:
                        continue

                    print(
                        "   Найдены колонки:",
                        group_columns
                    )

                    rows_after_header = clean_table[
                        row_index + 1:
                    ]

                    for group in TARGET_GROUPS:
                        column = group_columns[group]

                        group_data = []

                        for row in rows_after_header:
                            if column < len(row):
                                cell = row[column]
                            else:
                                cell = ""

                            group_data.append(cell)

                        result[group] = {
                            "rows": group_data,
                            "hash": make_hash(group_data)
                        }

                    return result

    raise RuntimeError(
        "Не удалось извлечь наши группы из таблицы"
    )


def load_state():
    if not STATE_FILE.exists():
        return None

    return json.loads(
        STATE_FILE.read_text(
            encoding="utf-8"
        )
    )


def save_state(groups, pdf_url):
    data = {
        "pdf_url": pdf_url,
        "groups": groups
    }

    STATE_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )


def compare_groups(old_state, new_groups):
    changed = []

    old_groups = old_state.get(
        "groups",
        {}
    )

    for group in TARGET_GROUPS:
        old_hash = (
            old_groups
            .get(group, {})
            .get("hash")
        )

        new_hash = new_groups[group]["hash"]

        if old_hash != new_hash:
            changed.append(group)

    return changed


def print_group_preview(groups):
    print("\n4. Что удалось извлечь:")

    for group in TARGET_GROUPS:
        print()
        print("=" * 60)
        print(group)
        print("=" * 60)

        for row in groups[group]["rows"]:
            if row:
                print(row)


def main():
    print()
    print("=" * 60)
    print("ПРОВЕРКА РАСПИСАНИЯ")
    print("=" * 60)

    pdf_url = find_pdf_url()

    pdf_data = download_pdf(
        pdf_url
    )

    groups = extract_groups(
        pdf_data
    )

    print_group_preview(
        groups
    )

    old_state = load_state()

    print()
    print("=" * 60)

    if old_state is None:
        print("ПЕРВЫЙ ЗАПУСК")
        print()
        print(
            "Предыдущее расписание ещё не сохранено."
        )
        print(
            "Сохраняю текущее как контрольную версию."
        )

        save_state(
            groups,
            pdf_url
        )

    else:
        changed = compare_groups(
            old_state,
            groups
        )

        if not changed:
            print(
                "✅ Расписание ДЭ 23-24 и ДЭ 24-24 "
                "НЕ изменилось."
            )

        else:
            print(
                "⚠️ РАСПИСАНИЕ ИЗМЕНИЛОСЬ!"
            )

            for group in changed:
                print(
                    f"   Изменена группа: {group}"
                )

            print()
            print(
                "В боевой версии здесь бот "
                "отправит уведомление в Telegram."
            )

        # После проверки сохраняем новую версию
        save_state(
            groups,
            pdf_url
        )

    print("=" * 60)


if __name__ == "__main__":
    main()