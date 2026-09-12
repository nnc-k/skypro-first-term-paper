"""Точка входа в приложение.

Запускает полный цикл: чтение данных, вызов всех сервисов и отчётов,
вывод результатов в консоль.
"""

import logging

from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)
from src.services import (
    cashback_categories,
    investment_bank,
    search_phone_numbers,
    search_transfers,
    simple_search,
)
from src.utils import (
    load_user_settings,
    read_transactions_from_excel,
    setup_logging,
)
from src.views import events_page, main_page

logger = logging.getLogger(__name__)


def main() -> None:
    """Запускает демонстрацию всех возможностей приложения."""
    setup_logging()
    logger.info("Приложение запущено")

    # ---------------------- Загрузка данных ----------------------
    df = read_transactions_from_excel("data/operations.xlsx")
    settings = load_user_settings()
    logger.info("Данные загружены: %d транзакций", len(df))

    # Фиксированная дата из данных (декабрь 2021), чтобы демонстрация
    # работала стабильно — в Excel данные именно за этот период
    demo_datetime = "2021-12-20 12:00:00"
    demo_year = 2021
    demo_month = 12
    demo_month_str = "2021-12"

    # ---------------------- Веб-страницы ----------------------
    print("=" * 80)
    print("ГЛАВНАЯ СТРАНИЦА")
    print("=" * 80)
    print(main_page(demo_datetime, df, settings))

    print()
    print("=" * 80)
    print("СТРАНИЦА СОБЫТИЙ (месяц)")
    print("=" * 80)
    print(events_page(demo_datetime, df, settings, "M"))

    print()
    print("=" * 80)
    print("СТРАНИЦА СОБЫТИЙ (неделя)")
    print("=" * 80)
    print(events_page(demo_datetime, df, settings, "W"))

    # ---------------------- Сервисы ----------------------
    print()
    print("=" * 80)
    print(f"КЕШБЭК-КАТЕГОРИИ за {demo_year}-{demo_month:02d}")
    print("=" * 80)
    print(cashback_categories(df, demo_year, demo_month))

    print()
    print("=" * 80)
    print(f"ИНВЕСТКОПИЛКА за {demo_month_str} (шаг 50 руб.)")
    print("=" * 80)
    transactions = df.to_dict(orient="records")
    print(investment_bank(demo_month_str, transactions, 50))

    print()
    print("=" * 80)
    print("ПРОСТОЙ ПОИСК: 'лента'")
    print("=" * 80)
    print(simple_search(df, "лента"))

    print()
    print("=" * 80)
    print("ПОИСК ТЕЛЕФОННЫХ НОМЕРОВ")
    print("=" * 80)
    print(search_phone_numbers(df))

    print()
    print("=" * 80)
    print("ПОИСК ПЕРЕВОДОВ ФИЗЛИЦАМ")
    print("=" * 80)
    print(search_transfers(df))

    # ---------------------- Отчёты ----------------------
    print()
    print("=" * 80)
    print("ОТЧЁТ: ТРАТЫ ПО КАТЕГОРИИ 'Супермаркеты'")
    print("=" * 80)
    report_category = spending_by_category(
        df, "Супермаркеты", date="20.12.2021"
    )
    print(report_category.to_string(index=False))

    print()
    print("=" * 80)
    print("ОТЧЁТ: СРЕДНИЕ ТРАТЫ ПО ДНЯМ НЕДЕЛИ")
    print("=" * 80)
    report_weekday = spending_by_weekday(df, date="20.12.2021")
    print(report_weekday.to_string(index=False))

    print()
    print("=" * 80)
    print("ОТЧЁТ: СРЕДНИЕ ТРАТЫ В РАБОЧИЙ/ВЫХОДНОЙ ДЕНЬ")
    print("=" * 80)
    report_workday = spending_by_workday(df, date="20.12.2021")
    print(report_workday.to_string(index=False))

    logger.info("Приложение завершено")


if __name__ == "__main__":
    main()
