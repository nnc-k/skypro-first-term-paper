"""Тесты для модуля src.services."""

import json

import pandas as pd
import pytest

from src.services import (
    cashback_categories,
    investment_bank,
    search_phone_numbers,
    search_transfers,
    simple_search,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Таблица с транзакциями для тестов."""
    return pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(
                [
                    "2021-12-01",
                    "2021-12-05",
                    "2021-12-10",
                    "2021-12-15",
                    "2021-12-20",
                    "2022-01-10",
                ]
            ),
            "Номер карты": ["*5814"] * 6,
            "Сумма платежа": [-100.0, -200.0, -50.0, -300.0, -400.0, -500.0],
            "Сумма операции": [-100, -200, -50, -300, -400, -500],
            "Категория": [
                "Супермаркеты",
                "Фастфуд",
                "Переводы",
                "Супермаркеты",
                "Переводы",
                "Фастфуд",
            ],
            "Описание": [
                "Лента",
                "KFC",
                "Валерий А.",
                "Магнит",
                "МТС +7 921 11-22-33",
                "Бургер Кинг",
            ],
        }
    )


# ---------------------- cashback_categories ----------------------


def test_cashback_categories_success(sample_df: pd.DataFrame) -> None:
    """Кешбэк по категориям за декабрь 2021."""
    result = json.loads(cashback_categories(sample_df, 2021, 12))
    assert isinstance(result, dict)
    assert "Супермаркеты" in result
    assert result["Супермаркеты"] == 4.0


def test_cashback_categories_empty_period(
    sample_df: pd.DataFrame,
) -> None:
    """За месяц без транзакций — пустой словарь."""
    result = json.loads(cashback_categories(sample_df, 2020, 1))
    assert result == {}


# ---------------------- investment_bank ----------------------


def test_investment_bank_with_limit_50() -> None:
    """Округление до 50: 1712 → 1750, отложено 38."""
    transactions = [
        {"Дата операции": "2021-12-01", "Сумма операции": -1712},
        {"Дата операции": "2021-12-05", "Сумма операции": -248},
    ]
    assert investment_bank("2021-12", transactions, 50) == 40.0


def test_investment_bank_ignores_other_months() -> None:
    """Транзакции других месяцев игнорируются."""
    transactions = [
        {"Дата операции": "2021-12-01", "Сумма операции": -1712},
        {"Дата операции": "2022-01-01", "Сумма операции": -1000},
    ]
    result = investment_bank("2021-12", transactions, 50)
    assert result == 38.0


def test_investment_bank_ignores_income() -> None:
    """Поступления не учитываются."""
    transactions = [
        {"Дата операции": "2021-12-01", "Сумма операции": 1712},
    ]
    assert investment_bank("2021-12", transactions, 50) == 0.0


# ---------------------- simple_search ----------------------


def test_simple_search_case_insensitive(sample_df: pd.DataFrame) -> None:
    """Поиск нечувствителен к регистру."""
    result = json.loads(simple_search(sample_df, "ЛЕНТА"))
    assert len(result) == 1
    assert result[0]["description"] == "Лента"


def test_simple_search_by_category(sample_df: pd.DataFrame) -> None:
    """Поиск работает по категории тоже."""
    result = json.loads(simple_search(sample_df, "супермаркеты"))
    assert len(result) == 2


def test_simple_search_no_results(sample_df: pd.DataFrame) -> None:
    """Если ничего не найдено — пустой список."""
    result = json.loads(simple_search(sample_df, "нетТакого"))
    assert result == []


# ---------------------- search_phone_numbers ----------------------


def test_search_phone_numbers_found(sample_df: pd.DataFrame) -> None:
    """Находит транзакцию с телефоном в описании."""
    result = json.loads(search_phone_numbers(sample_df))
    assert len(result) == 1
    assert "+7 921 11-22-33" in result[0]["description"]


def test_search_phone_numbers_empty() -> None:
    """Если телефонов нет — пустой список."""
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2021-12-01"]),
            "Сумма платежа": [-100.0],
            "Категория": ["Супермаркеты"],
            "Описание": ["Лента"],
        }
    )
    result = json.loads(search_phone_numbers(df))
    assert result == []


# ---------------------- search_transfers ----------------------


def test_search_transfers_found(sample_df: pd.DataFrame) -> None:
    """Находит переводы физлицам."""
    result = json.loads(search_transfers(sample_df))
    assert len(result) == 1
    assert result[0]["description"] == "Валерий А."


def test_search_transfers_empty() -> None:
    """Если переводов физлицам нет — пустой список."""
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2021-12-01"]),
            "Сумма платежа": [-100.0],
            "Категория": ["Переводы"],
            "Описание": ["Перевод на карту"],
        }
    )
    result = json.loads(search_transfers(df))
    assert result == []
