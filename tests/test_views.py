"""Тесты для модуля src.views."""

import json
from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

# noinspection PyProtectedMember
from src.views import (
    _filter_by_period,
    _get_cards_info,
    _get_expenses_block,
    _get_income_block,
    _get_period_range,
    _get_top_transactions,
    events_page,
    main_page,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Таблица с несколькими транзакциями для тестов."""
    return pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(
                [
                    "2021-12-01",
                    "2021-12-05",
                    "2021-12-10",
                    "2021-12-15",
                    "2021-12-20",
                ]
            ),
            "Номер карты": ["*5814", "*5814", "*7197", "*7197", "*7197"],
            "Сумма платежа": [-100.0, -200.0, -50.0, 5000.0, -300.0],
            "Категория": [
                "Супермаркеты",
                "Фастфуд",
                "Переводы",
                "Пополнение",
                "Наличные",
            ],
            "Описание": ["Лента", "KFC", "Валерий А.", "Зарплата", "Банкомат"],
        }
    )


@pytest.fixture
def settings() -> dict:
    """Настройки пользователя: пустые списки валют и акций."""
    return {"user_currencies": [], "user_stocks": []}


# ---------------------- _get_period_range ----------------------


def test_get_period_range_m() -> None:
    """Месяц — с 1-го числа."""
    dt = datetime(2021, 12, 15, 12, 0, 0)
    start, end = _get_period_range(dt, "M")
    assert start == datetime(2021, 12, 1, 0, 0, 0)
    assert end == dt


def test_get_period_range_w() -> None:
    """Неделя — с понедельника."""
    dt = datetime(2021, 12, 15, 12, 0, 0)
    start, end = _get_period_range(dt, "W")
    assert start == datetime(2021, 12, 13, 0, 0, 0)
    assert end == dt


def test_get_period_range_y() -> None:
    """Год — с 1 января."""
    dt = datetime(2021, 12, 15, 12, 0, 0)
    start, end = _get_period_range(dt, "Y")
    assert start == datetime(2021, 1, 1, 0, 0, 0)
    assert end == dt


def test_get_period_range_all() -> None:
    """ALL — начало с 1900 года."""
    dt = datetime(2021, 12, 15, 12, 0, 0)
    start, end = _get_period_range(dt, "ALL")
    assert start == datetime(1900, 1, 1)
    assert end == dt


def test_get_period_range_default() -> None:
    """Неизвестный тип — как месяц."""
    dt = datetime(2021, 12, 15, 12, 0, 0)
    start, end = _get_period_range(dt, "X")
    assert start == datetime(2021, 12, 1, 0, 0, 0)


# ---------------------- _filter_by_period ----------------------


def test_filter_by_period(sample_df: pd.DataFrame) -> None:
    """Фильтр по диапазону оставляет только нужные строки."""
    start = datetime(2021, 12, 1)
    end = datetime(2021, 12, 10)
    result = _filter_by_period(sample_df, start, end)
    assert len(result) == 3


# ---------------------- _get_cards_info ----------------------


def test_get_cards_info(sample_df: pd.DataFrame) -> None:
    """Информация по картам: last_digits, total_spent, cashback."""
    expenses = sample_df[sample_df["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    cards = _get_cards_info(expenses)
    assert len(cards) == 2
    for card in cards:
        assert "last_digits" in card
        assert "total_spent" in card
        assert "cashback" in card
        assert len(card["last_digits"]) == 4


# ---------------------- _get_top_transactions ----------------------


def test_get_top_transactions(sample_df: pd.DataFrame) -> None:
    """Топ-N по модулю суммы платежа."""
    expenses = sample_df[sample_df["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    top = _get_top_transactions(expenses, n=3)
    assert len(top) == 3
    assert top[0]["amount"] == 300.0
    assert top[0]["date"] == "20.12.2021"


# ---------------------- _get_expenses_block ----------------------


def test_get_expenses_block(sample_df: pd.DataFrame) -> None:
    """Блок расходов: топ-7 + Остальное, отдельно Переводы/Наличные."""
    expenses = sample_df[sample_df["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    block = _get_expenses_block(expenses)
    assert "total_amount" in block
    assert "main" in block
    assert "transfers_and_cash" in block
    transfer_cats = {item["category"] for item in block["transfers_and_cash"]}
    assert "Наличные" in transfer_cats
    assert "Переводы" in transfer_cats


def test_get_expenses_block_rest_category() -> None:
    """Если категорий больше 7 — появляется Остальное."""
    data = {
        "Дата операции": pd.to_datetime(["2021-12-01"] * 10),
        "Номер карты": ["*5814"] * 10,
        "Сумма платежа": [-100.0] * 10,
        "Категория": [f"Кат{i}" for i in range(10)],
        "Описание": ["x"] * 10,
    }
    df = pd.DataFrame(data)
    expenses = df[df["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    block = _get_expenses_block(expenses)
    cats = [item["category"] for item in block["main"]]
    assert "Остальное" in cats
    assert len(cats) == 8


# ---------------------- _get_income_block ----------------------


def test_get_income_block(sample_df: pd.DataFrame) -> None:
    """Блок поступлений."""
    income = sample_df[sample_df["Сумма платежа"] > 0].copy()
    block = _get_income_block(income)
    assert block["total_amount"] == 5000
    assert block["main"][0]["category"] == "Пополнение"


# ---------------------- main_page ----------------------


@patch("src.views.get_stock_prices", return_value=[])
@patch("src.views.get_currency_rates", return_value=[])
def test_main_page_structure(_mock_curr, _mock_stock, sample_df: pd.DataFrame, settings: dict) -> None:
    """Проверяет структуру JSON-ответа main_page."""
    result = json.loads(main_page("2021-12-20 12:00:00", sample_df, settings))
    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert "currency_rates" in result
    assert "stock_prices" in result
    assert result["greeting"] == "Добрый день"


# ---------------------- events_page ----------------------


@patch("src.views.get_stock_prices", return_value=[])
@patch("src.views.get_currency_rates", return_value=[])
def test_events_page_structure(_mock_curr, _mock_stock, sample_df: pd.DataFrame, settings: dict) -> None:
    """Проверяет структуру JSON-ответа events_page."""
    result = json.loads(events_page("2021-12-20 12:00:00", sample_df, settings, "M"))
    assert "expenses" in result
    assert "income" in result
    assert "currency_rates" in result
    assert "stock_prices" in result
    assert "total_amount" in result["expenses"]
    assert "main" in result["expenses"]
    assert "transfers_and_cash" in result["expenses"]
    assert "total_amount" in result["income"]
