"""Тесты для модуля src.reports."""

import json
from datetime import datetime

import pandas as pd
import pytest

from src.reports import (
    _filter_last_3_months,
    _only_expenses,
    _parse_date,
    report_to_file,
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Таблица с транзакциями за декабрь 2021."""
    return pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(
                [
                    "2021-12-01",  # среда
                    "2021-12-04",  # суббота
                    "2021-12-06",  # понедельник
                    "2021-12-10",  # пятница
                    "2021-12-15",  # среда
                    "2021-12-20",  # понедельник
                ]
            ),
            "Номер карты": ["*5814"] * 6,
            "Сумма платежа": [-100.0, -200.0, -300.0, -400.0, 5000.0, -500.0],
            "Категория": [
                "Супермаркеты",
                "Супермаркеты",
                "Фастфуд",
                "Супермаркеты",
                "Пополнение",
                "Переводы",
            ],
            "Описание": ["Лента", "Магнит", "KFC", "Пятёрочка", "Зарплата", "Друг"],
        }
    )


# ---------------------- _parse_date ----------------------


def test_parse_date_from_string() -> None:
    """Парсит строку в формате DD.MM.YYYY."""
    result = _parse_date("20.12.2021")
    assert result == datetime(2021, 12, 20)


def test_parse_date_none() -> None:
    """Без даты — возвращает текущую."""
    result = _parse_date(None)
    assert isinstance(result, datetime)
    assert result.date() == datetime.now().date()


# ---------------------- _filter_last_3_months ----------------------


def test_filter_last_3_months(sample_df: pd.DataFrame) -> None:
    """Оставляет только транзакции за 3 месяца до указанной даты."""
    result = _filter_last_3_months(sample_df, "20.12.2021")
    # Все 6 транзакций попадают в диапазон 21.09.2021 — 20.12.2021
    assert len(result) == 6


def test_filter_last_3_months_out_of_range(sample_df: pd.DataFrame) -> None:
    """Дата вне диапазона — пустой результат."""
    result = _filter_last_3_months(sample_df, "20.12.2022")
    assert len(result) == 0


# ---------------------- _only_expenses ----------------------


def test_only_expenses(sample_df: pd.DataFrame) -> None:
    """Оставляет только расходы и переводит в положительные."""
    result = _only_expenses(sample_df)
    assert len(result) == 5
    assert all(result["Сумма платежа"] > 0)


# ---------------------- report_to_file ----------------------


def test_report_to_file_default_name(tmp_path, monkeypatch) -> None:
    """Декоратор без параметра сохраняет в <имя>_report.json."""
    monkeypatch.chdir(tmp_path)

    @report_to_file()
    def my_func() -> dict:
        return {"key": "value"}

    result = my_func()

    assert result == {"key": "value"}
    saved = tmp_path / "my_func_report.json"
    assert saved.is_file()
    with open(saved, "r", encoding="utf-8") as file:
        data = json.load(file)
    assert data == {"key": "value"}


def test_report_to_file_custom_name(tmp_path, monkeypatch) -> None:
    """Декоратор с параметром сохраняет в указанный файл."""
    monkeypatch.chdir(tmp_path)

    @report_to_file("custom.json")
    def my_func() -> dict:
        return {"a": 1}

    my_func()

    saved = tmp_path / "custom.json"
    assert saved.is_file()


def test_report_to_file_with_dataframe(tmp_path, monkeypatch) -> None:
    """Декоратор умеет сохранять DataFrame."""
    monkeypatch.chdir(tmp_path)

    @report_to_file("df_report.json")
    def my_func() -> pd.DataFrame:
        return pd.DataFrame({"x": [1, 2], "y": [3, 4]})

    result = my_func()

    assert isinstance(result, pd.DataFrame)
    saved = tmp_path / "df_report.json"
    assert saved.is_file()
    with open(saved, "r", encoding="utf-8") as file:
        data = json.load(file)
    assert data == [{"x": 1, "y": 3}, {"x": 2, "y": 4}]


# ---------------------- spending_by_category ----------------------


def test_spending_by_category_found(sample_df: pd.DataFrame, tmp_path, monkeypatch) -> None:
    """Траты по категории Супермаркеты."""
    monkeypatch.chdir(tmp_path)
    result = spending_by_category(sample_df, "Супермаркеты", date="20.12.2021")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert all(result["Категория"] == "Супермаркеты")


def test_spending_by_category_empty(sample_df: pd.DataFrame, tmp_path, monkeypatch) -> None:
    """Несуществующая категория — пустой результат."""
    monkeypatch.chdir(tmp_path)
    result = spending_by_category(sample_df, "Несуществующая", date="20.12.2021")
    assert len(result) == 0


# ---------------------- spending_by_weekday ----------------------


def test_spending_by_weekday(sample_df: pd.DataFrame, tmp_path, monkeypatch) -> None:
    """Средние траты по дням недели."""
    monkeypatch.chdir(tmp_path)
    result = spending_by_weekday(sample_df, date="20.12.2021")
    assert isinstance(result, pd.DataFrame)
    assert "weekday" in result.columns
    assert "average_spending" in result.columns
    assert len(result) > 0


def test_spending_by_weekday_empty(tmp_path, monkeypatch) -> None:
    """Пустой DataFrame — пустой результат."""
    monkeypatch.chdir(tmp_path)
    empty_df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime([]),
            "Сумма платежа": [],
            "Категория": [],
            "Описание": [],
        }
    )
    result = spending_by_weekday(empty_df, date="20.12.2021")
    assert len(result) == 0


# ---------------------- spending_by_workday ----------------------


def test_spending_by_workday(sample_df: pd.DataFrame, tmp_path, monkeypatch) -> None:
    """Средние траты в рабочий и выходной день."""
    monkeypatch.chdir(tmp_path)
    result = spending_by_workday(sample_df, date="20.12.2021")
    assert isinstance(result, pd.DataFrame)
    assert "day_type" in result.columns
    assert "average_spending" in result.columns
    types = set(result["day_type"])
    assert "Рабочий" in types
    assert "Выходной" in types


def test_spending_by_workday_empty(tmp_path, monkeypatch) -> None:
    """Пустой DataFrame — пустой результат."""
    monkeypatch.chdir(tmp_path)
    empty_df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime([]),
            "Сумма платежа": [],
            "Категория": [],
            "Описание": [],
        }
    )
    result = spending_by_workday(empty_df, date="20.12.2021")
    assert len(result) == 0
