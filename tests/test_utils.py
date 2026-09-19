"""Тесты для модуля src.utils."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils import (
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_user_settings,
    read_transactions_from_excel,
    setup_logging,
)

# ---------------------- get_greeting ----------------------


@pytest.mark.parametrize(
    "hour,expected",
    [
        (6, "Доброе утро"),
        (9, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (15, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (21, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (0, "Доброй ночи"),
        (5, "Доброй ночи"),
    ],
)
def test_get_greeting(hour: int, expected: str) -> None:
    """Приветствие соответствует временному интервалу."""
    dt = datetime(2024, 1, 1, hour, 0, 0)
    assert get_greeting(dt) == expected


# ---------------------- load_user_settings ----------------------


def test_load_user_settings_success() -> None:
    """Загружает корректный JSON-файл с настройками."""
    settings = load_user_settings("user_settings.json")
    assert "user_currencies" in settings
    assert "user_stocks" in settings
    assert isinstance(settings["user_currencies"], list)
    assert isinstance(settings["user_stocks"], list)


def test_load_user_settings_file_not_found() -> None:
    """При отсутствии файла выбрасывает FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_user_settings("nonexistent_file.json")


# ---------------------- read_transactions_from_excel ----------------------


def test_read_transactions_from_excel_success() -> None:
    """Читает Excel и корректно парсит дату."""
    df = read_transactions_from_excel("data/operations.xlsx")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "Дата операции" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Дата операции"])


def test_read_transactions_from_excel_not_found() -> None:
    """При отсутствии файла выбрасывает FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_transactions_from_excel("data/nonexistent.xlsx")


# ---------------------- setup_logging ----------------------


def test_setup_logging_creates_logs_dir(tmp_path, monkeypatch) -> None:
    """Проверяет, что setup_logging создаёт папку logs и файл app.log."""
    import logging

    monkeypatch.chdir(tmp_path)

    # Сбрасываем все существующие handlers root-логгера
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    setup_logging()

    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "logs" / "app.log").is_file()


# ---------------------- get_currency_rates ----------------------


def test_get_currency_rates_success() -> None:
    """Возвращает курсы валют в нужном формате."""
    rates = get_currency_rates(["USD", "EUR"])
    assert isinstance(rates, list)
    assert len(rates) > 0
    for rate in rates:
        assert "currency" in rate
        assert "rate" in rate
        assert isinstance(rate["currency"], str)
        assert isinstance(rate["rate"], float)
        assert rate["rate"] > 0


def test_get_currency_rates_empty_list() -> None:
    """Пустой список валют — пустой результат."""
    assert get_currency_rates([]) == []


@patch("src.utils.requests.get")
def test_get_currency_rates_request_error(mock_get) -> None:
    """Проверяет, что RequestException обрабатывается без падения."""
    import requests

    mock_get.side_effect = requests.RequestException("Сеть недоступна")
    assert get_currency_rates(["USD"]) == []


@patch("src.utils.requests.get")
def test_get_currency_rates_value_error(mock_get) -> None:
    """Проверяет, что ValueError при парсинге JSON обрабатывается."""
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.side_effect = ValueError("Некорректный JSON")
    assert get_currency_rates(["USD"]) == []


# ---------------------- get_stock_prices ----------------------


def test_get_stock_prices_no_api_key(monkeypatch) -> None:
    """Проверяет, что без STOCK_API_KEY возвращается пустой список."""
    monkeypatch.delenv("STOCK_API_KEY", raising=False)
    assert get_stock_prices(["AAPL"]) == []


def test_get_stock_prices_empty_list(monkeypatch) -> None:
    """Пустой список акций — пустой результат."""
    monkeypatch.setenv("STOCK_API_KEY", "test_key")
    assert get_stock_prices([]) == []


@patch("src.utils.requests.get")
def test_get_stock_prices_success(mock_get, monkeypatch) -> None:
    """Проверяет успешное получение цены акции через Finnhub."""
    monkeypatch.setenv("STOCK_API_KEY", "test_key")
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"c": 150.12}

    result = get_stock_prices(["AAPL"])
    assert result == [{"stock": "AAPL", "price": 150.12}]


@patch("src.utils.requests.get")
def test_get_stock_prices_no_price(mock_get, monkeypatch) -> None:
    """Проверяет, что при c=0 тикер пропускается."""
    monkeypatch.setenv("STOCK_API_KEY", "test_key")
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"c": 0}
    assert get_stock_prices(["AAPL"]) == []


@patch("src.utils.requests.get")
def test_get_stock_prices_request_error(mock_get, monkeypatch) -> None:
    """Проверяет, что RequestException обрабатывается, тикер пропускается."""
    import requests

    monkeypatch.setenv("STOCK_API_KEY", "test_key")
    mock_get.side_effect = requests.RequestException("Finnhub недоступен")
    assert get_stock_prices(["AAPL"]) == []
