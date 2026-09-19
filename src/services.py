"""Сервисы для анализа транзакций.

Содержит 5 сервисов: кешбэк-категории, инвесткопилка,
простой поиск, поиск телефонов, поиск переводов физлицам.
"""

import json
import logging
import re
from functools import reduce
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------- Кешбэк-категории ----------------------


def cashback_categories(df: pd.DataFrame, year: int, month: int) -> str:
    """Анализирует, сколько на каждой категории можно заработать кешбэка.

    :param df: DataFrame с транзакциями
    :param year: год для анализа
    :param month: месяц для анализа
    :return: JSON со словарём {категория: сумма кешбэка}
    """
    logger.info("Анализ кешбэка за %d-%02d", year, month)

    mask = (df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month)
    period = df[mask & (df["Сумма платежа"] < 0)].copy()
    period["Сумма платежа"] = period["Сумма платежа"].abs()

    # Функциональный подход: groupby + map для расчёта кешбэка
    grouped = period.groupby("Категория")["Сумма платежа"].sum()

    def to_cashback(amount: float) -> float:
        """Возвращает кешбэк: 1 рубль на 100 рублей суммы."""
        return round(amount / 100, 2)

    # map через apply, sort_values — по убыванию
    result = grouped.apply(to_cashback).sort_values(ascending=False).to_dict()
    return json.dumps(result, ensure_ascii=False, indent=2)


# ---------------------- Инвесткопилка ----------------------


def investment_bank(month: str, transactions: list[dict[str, Any]], limit: int) -> float:
    """Считает сумму, которую удалось бы отложить в «Инвесткопилку».

    :param month: месяц в формате 'YYYY-MM'
    :param transactions: список словарей с транзакциями
    :param limit: шаг округления (10, 50 или 100)
    :return: отложенная сумма (float)
    """
    logger.info("Расчёт инвесткопилки за %s с шагом %d", month, limit)

    def round_up(amount: float) -> float:
        """Округляет вверх до ближайшего кратного limit."""
        return ((amount + limit - 1) // limit) * limit

    def extract_savings(tx: dict[str, Any]) -> float:
        """Возвращает сумму округления для одной транзакции."""
        date_str = str(tx.get("Дата операции", ""))[:10]
        if not date_str.startswith(month):
            return 0.0
        amount = float(tx.get("Сумма операции", 0))
        if amount >= 0:
            return 0.0
        abs_amount = abs(amount)
        return float(round_up(abs_amount) - abs_amount)

    # Функциональный подход: map + reduce
    savings = map(extract_savings, transactions)
    total = reduce(lambda acc, x: acc + x, savings, 0.0)
    return round(total, 2)


# ---------------------- Простой поиск ----------------------


def _df_to_json(df: pd.DataFrame) -> str:
    """Преобразует DataFrame в JSON-строку с нужными полями."""
    result = [
        {
            "date": row["Дата операции"].strftime("%d.%m.%Y"),
            "amount": round(float(row["Сумма платежа"]), 2),
            "category": row["Категория"],
            "description": row["Описание"],
        }
        for _, row in df.iterrows()
    ]
    return json.dumps(result, ensure_ascii=False, indent=2)


def simple_search(df: pd.DataFrame, query: str) -> str:
    """Ищет транзакции по подстроке в описании или категории (без регистра).

    :param df: DataFrame с транзакциями
    :param query: строка поиска
    :return: JSON со списком найденных транзакций
    """
    logger.info("Простой поиск: %s", query)
    q = query.lower()
    mask = df["Описание"].str.lower().str.contains(q, na=False) | df["Категория"].str.lower().str.contains(q, na=False)
    return _df_to_json(df[mask])


# ---------------------- Поиск телефонов ----------------------


PHONE_PATTERN = re.compile(r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{2,3}[\s\-]?\d{2}[\s\-]?\d{2}")


def search_phone_numbers(df: pd.DataFrame) -> str:
    """Возвращает транзакции, в описании которых есть телефонные номера.

    :param df: DataFrame с транзакциями
    :return: JSON со списком найденных транзакций
    """
    logger.info("Поиск транзакций с телефонными номерами")
    descriptions = df["Описание"].astype(str)

    # Функциональный подход: filter через map + list comprehension
    mask = descriptions.map(lambda text: bool(PHONE_PATTERN.search(text)))
    return _df_to_json(df[mask])


# ---------------------- Поиск переводов физлицам ----------------------


TRANSFER_PATTERN = re.compile(r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.")


def search_transfers(df: pd.DataFrame) -> str:
    """Возвращает переводы физическим лицам.

    Категория «Переводы» + в описании есть имя и первая буква
    фамилии с точкой, например «Валерий А.».
    """
    logger.info("Поиск переводов физлицам")
    descriptions = df["Описание"].astype(str)

    mask = (df["Категория"] == "Переводы") & descriptions.map(lambda text: bool(TRANSFER_PATTERN.search(text)))
    return _df_to_json(df[mask])
