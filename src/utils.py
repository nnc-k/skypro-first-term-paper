"""Вспомогательные функции: чтение Excel, настройки, приветствие, API."""

import json
import logging
import os
from datetime import datetime
from typing import Any, cast

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Настраивает логирование: пишет в logs/app.log и в консоль."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(f"{log_dir}/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger.info("Логирование настроено")


def read_transactions_from_excel(path: str) -> pd.DataFrame:
    """Читает транзакции из Excel и приводит дату к типу datetime."""
    logger.info("Чтение транзакций из %s", path)
    df = pd.read_excel(path)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    logger.info("Прочитано %d транзакций", len(df))
    return df


def load_user_settings(path: str = "user_settings.json") -> dict[str, Any]:
    """Загружает пользовательские настройки (валюты, акции)."""
    logger.info("Загрузка настроек из %s", path)
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
        return cast(dict[str, Any], data)


def get_greeting(dt: datetime) -> str:
    """Приветствие по времени суток."""
    hour = dt.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def get_currency_rates(currencies: list[str]) -> list[dict[str, Any]]:
    """Курсы валют к рублю через API ЦБ РФ."""
    result: list[dict[str, Any]] = []
    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10)
        response.raise_for_status()
        data = response.json().get("Valute", {})

        for code in currencies:
            if code in data:
                rate = data[code].get("Value")
                if isinstance(rate, (int, float)) and rate > 0:
                    result.append({"currency": code, "rate": round(float(rate), 2)})
    except requests.RequestException as exc:
        logger.error("Ошибка получения курсов валют: %s", exc)
    except (ValueError, KeyError) as exc:
        logger.error("Некорректный ответ API валют: %s", exc)

    return result


def get_stock_prices(stocks: list[str]) -> list[dict[str, Any]]:
    """Цены акций через API Finnhub.

    :param stocks: список тикеров, например ["AAPL", "MSFT"]
    :return: список словарей вида [{"stock": "AAPL", "price": 150.12}, ...]
    """
    result: list[dict[str, Any]] = []
    api_key = os.getenv("STOCK_API_KEY")

    if not api_key:
        logger.error("STOCK_API_KEY не найден в переменных окружения")
        return result

    for ticker in stocks:
        try:
            url = f"https://finnhub.io/api/v1/quote" f"?symbol={ticker}&token={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Finnhub возвращает поле "c" = current price
            price = data.get("c")
            if isinstance(price, (int, float)) and price > 0:
                result.append({"stock": ticker, "price": round(float(price), 2)})
            else:
                logger.warning("Нет цены для %s (ответ: %s)", ticker, data)

        except requests.RequestException as exc:
            logger.error("Ошибка получения цены %s: %s", ticker, exc)

    return result
