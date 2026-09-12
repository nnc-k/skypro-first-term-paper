"""Отчёты по транзакциям.

Содержит декоратор для сохранения результатов в файл
и три функции-отчёта: траты по категории, траты по дням недели,
траты в рабочий/выходной день.
"""

import functools
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def report_to_file(filename: Optional[str] = None) -> Callable:
    """Декоратор: сохраняет результат функции-отчёта в JSON-файл.

    Может использоваться как с параметром (имя файла), так и без него:
        @report_to_file()
        @report_to_file("my_report.json")

    :param filename: имя файла для сохранения. Если не задано,
                     используется <имя_функции>_report.json
    :return: декоратор
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            # Имя файла: из параметра или по умолчанию
            output_name = filename or f"{func.__name__}_report.json"

            # Приводим DataFrame к списку словарей для JSON
            if isinstance(result, pd.DataFrame):
                data_to_save: Any = result.to_dict(orient="records")
            else:
                data_to_save = result

            with open(output_name, "w", encoding="utf-8") as file:
                json.dump(
                    data_to_save,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

            logger.info("Отчёт сохранён: %s", output_name)
            return result

        return wrapper

    return decorator


# ---------------------- Вспомогательное ----------------------


def _parse_date(date: Optional[str]) -> datetime:
    """Преобразует строку 'DD.MM.YYYY' в datetime.

    Если date не задана — возвращает текущую дату.
    """
    if date is None:
        return datetime.now()
    return datetime.strptime(date, "%d.%m.%Y")


def _filter_last_3_months(
    df: pd.DataFrame, date: Optional[str]
) -> pd.DataFrame:
    """Оставляет транзакции за последние 3 месяца от указанной даты."""
    end = _parse_date(date)
    start = end - timedelta(days=90)
    return df[
        (df["Дата операции"] >= start) & (df["Дата операции"] <= end)
    ].copy()


def _only_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """Оставляет только расходы и приводит сумму к положительному числу."""
    expenses = df[df["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    return expenses


# ---------------------- Отчёт 1: траты по категории ----------------------


@report_to_file()
def spending_by_category(
    df: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
    """Траты по заданной категории за последние 3 месяца.

    :param df: DataFrame с транзакциями
    :param category: название категории
    :param date: дата в формате 'DD.MM.YYYY'. По умолчанию — текущая
    :return: DataFrame с тратами по категории
    """
    logger.info("Отчёт: траты по категории '%s' на %s", category, date)
    period = _filter_last_3_months(df, date)
    expenses = _only_expenses(period)
    result = expenses[expenses["Категория"] == category]
    return result[["Дата операции", "Сумма платежа", "Категория", "Описание"]]


# ---------------------- Отчёт 2: траты по дням недели ----------------------


WEEKDAY_RU = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}


@report_to_file()
def spending_by_weekday(
    df: pd.DataFrame, date: Optional[str] = None
) -> pd.DataFrame:
    """Средние траты по каждому дню недели за последние 3 месяца.

    :param df: DataFrame с транзакциями
    :param date: дата в формате 'DD.MM.YYYY'. По умолчанию — текущая
    :return: DataFrame с колонками weekday, average_spending
    """
    logger.info("Отчёт: средние траты по дням недели на %s", date)
    period = _filter_last_3_months(df, date)
    expenses = _only_expenses(period)

    if expenses.empty:
        return pd.DataFrame(columns=["weekday", "average_spending"])

    expenses["weekday_en"] = expenses["Дата операции"].dt.day_name()
    grouped = (
        expenses.groupby("weekday_en")["Сумма платежа"]
        .mean()
        .round(2)
        .reset_index()
    )
    grouped["weekday"] = grouped["weekday_en"].map(WEEKDAY_RU)
    result = grouped[["weekday", "Сумма платежа"]].rename(
        columns={"Сумма платежа": "average_spending"}
    )
    return result


# ---------------------- Отчёт 3: траты в рабочий/выходной ----------------------


@report_to_file()
def spending_by_workday(
    df: pd.DataFrame, date: Optional[str] = None
) -> pd.DataFrame:
    """Средние траты в рабочие и выходные дни за последние 3 месяца.

    :param df: DataFrame с транзакциями
    :param date: дата в формате 'DD.MM.YYYY'. По умолчанию — текущая
    :return: DataFrame с колонками day_type, average_spending
    """
    logger.info("Отчёт: средние траты в рабочий/выходной на %s", date)
    period = _filter_last_3_months(df, date)
    expenses = _only_expenses(period)

    if expenses.empty:
        return pd.DataFrame(columns=["day_type", "average_spending"])

    expenses["is_weekend"] = expenses["Дата операции"].dt.weekday >= 5
    grouped = (
        expenses.groupby("is_weekend")["Сумма платежа"]
        .mean()
        .round(2)
        .reset_index()
    )
    grouped["day_type"] = grouped["is_weekend"].map(
        {True: "Выходной", False: "Рабочий"}
    )
    result = grouped[["day_type", "Сумма платежа"]].rename(
        columns={"Сумма платежа": "average_spending"}
    )
    return result
