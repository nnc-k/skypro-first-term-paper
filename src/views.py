"""Веб-страницы: Главная и События.

Формируют JSON-ответы для фронтенда на основе данных транзакций.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from src.utils import get_currency_rates, get_greeting, get_stock_prices

logger = logging.getLogger(__name__)


def _get_period_range(
    end_dt: datetime, range_type: str
) -> tuple[datetime, datetime]:
    """Возвращает (начало, конец) периода по типу диапазона.

    :param end_dt: конец периода (входящая дата)
    :param range_type: W — неделя, M — месяц, Y — год, ALL — всё до даты
    :return: кортеж (start, end)
    """
    if range_type == "W":
        start = end_dt - timedelta(days=end_dt.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, end_dt
    if range_type == "M":
        start = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, end_dt
    if range_type == "Y":
        start = end_dt.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return start, end_dt
    if range_type == "ALL":
        return datetime(1900, 1, 1), end_dt
    # По умолчанию — с начала месяца
    start = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, end_dt


def _filter_by_period(
    df: pd.DataFrame, start: datetime, end: datetime
) -> pd.DataFrame:
    """Оставляет только транзакции в диапазоне [start, end]."""
    return df[(df["Дата операции"] >= start) & (df["Дата операции"] <= end)]


# ---------------------- Главная страница ----------------------


def main_page(
    date_time_str: str, df: pd.DataFrame, settings: dict[str, Any]
) -> str:
    """Формирует JSON для главной страницы.

    :param date_time_str: дата и время в формате "YYYY-MM-DD HH:MM:SS"
    :param df: DataFrame с транзакциями
    :param settings: словарь с ключами user_currencies и user_stocks
    :return: JSON-строка
    """
    logger.info("Формирование главной страницы на %s", date_time_str)
    dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    start, end = _get_period_range(dt, "M")
    period = _filter_by_period(df, start, end)

    expenses = period[period["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()

    cards = _get_cards_info(expenses)
    top_transactions = _get_top_transactions(expenses, n=5)

    result = {
        "greeting": get_greeting(dt),
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": get_currency_rates(
            settings.get("user_currencies", [])
        ),
        "stock_prices": get_stock_prices(settings.get("user_stocks", [])),
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def _get_cards_info(expenses: pd.DataFrame) -> list[dict[str, Any]]:
    """Информация по каждой карте: последние 4 цифры, траты, кешбэк."""
    cards = []
    for card, group in expenses.groupby("Номер карты"):
        total = round(float(group["Сумма платежа"].sum()), 2)
        cards.append(
            {
                "last_digits": str(card).replace("*", "").strip()[-4:],
                "total_spent": total,
                "cashback": round(total / 100, 2),
            }
        )
    return cards


def _get_top_transactions(
    expenses: pd.DataFrame, n: int = 5
) -> list[dict[str, Any]]:
    """Топ-N транзакций по сумме платежа (по модулю)."""
    top = expenses.nlargest(n, "Сумма платежа")
    return [
        {
            "date": row["Дата операции"].strftime("%d.%m.%Y"),
            "amount": round(float(row["Сумма платежа"]), 2),
            "category": row["Категория"],
            "description": row["Описание"],
        }
        for _, row in top.iterrows()
    ]


# ---------------------- Страница События ----------------------


def events_page(
    date_time_str: str,
    df: pd.DataFrame,
    settings: dict[str, Any],
    range_type: str = "M",
) -> str:
    """Формирует JSON для страницы событий.

    :param date_time_str: дата и время в формате "YYYY-MM-DD HH:MM:SS"
    :param df: DataFrame с транзакциями
    :param settings: словарь с ключами user_currencies и user_stocks
    :param range_type: W, M, Y или ALL. По умолчанию M
    :return: JSON-строка
    """
    logger.info("Формирование страницы событий (%s)", range_type)
    dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    start, end = _get_period_range(dt, range_type)
    period = _filter_by_period(df, start, end)

    expenses = period[period["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    income = period[period["Сумма платежа"] > 0].copy()

    result = {
        "expenses": _get_expenses_block(expenses),
        "income": _get_income_block(income),
        "currency_rates": get_currency_rates(
            settings.get("user_currencies", [])
        ),
        "stock_prices": get_stock_prices(settings.get("user_stocks", [])),
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


SPECIAL_CATEGORIES = {"Наличные", "Переводы"}


def _get_expenses_block(expenses: pd.DataFrame) -> dict[str, Any]:
    """Блок расходов: total_amount, main (топ-7 + Остальное), transfers_and_cash."""
    total_amount = int(round(expenses["Сумма платежа"].sum()))

    # Суммы по категориям
    cat_totals = (
        expenses.groupby("Категория")["Сумма платежа"].sum().round().astype(int)
    )

    # Переводы и наличные — отдельно
    transfers = cat_totals[cat_totals.index.isin(SPECIAL_CATEGORIES)]
    transfers = transfers.sort_values(ascending=False)
    transfers_and_cash = [
        {"category": cat, "amount": int(amount)}
        for cat, amount in transfers.items()
    ]

    # Остальные категории: топ-7 + Остальное
    main_cats = cat_totals[~cat_totals.index.isin(SPECIAL_CATEGORIES)]
    main_cats = main_cats.sort_values(ascending=False)

    top7 = main_cats.head(7)
    main = [
        {"category": cat, "amount": int(amount)} for cat, amount in top7.items()
    ]

    rest_sum = int(main_cats.iloc[7:].sum())
    if rest_sum > 0:
        main.append({"category": "Остальное", "amount": rest_sum})

    return {
        "total_amount": total_amount,
        "main": main,
        "transfers_and_cash": transfers_and_cash,
    }


def _get_income_block(income: pd.DataFrame) -> dict[str, Any]:
    """Блок поступлений: total_amount и main (все категории)."""
    total_amount = int(round(income["Сумма платежа"].sum()))

    cat_totals = (
        income.groupby("Категория")["Сумма платежа"].sum().round().astype(int)
    )
    cat_totals = cat_totals.sort_values(ascending=False)

    main = [
        {"category": cat, "amount": int(amount)}
        for cat, amount in cat_totals.items()
    ]

    return {"total_amount": total_amount, "main": main}
