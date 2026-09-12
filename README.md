# Первая курсовая работа: анализ транзакций

Приложение на Python для анализа банковских транзакций из Excel-файла.
Генерирует JSON для веб-страниц, формирует JSON-отчёты, предоставляет сервисы поиска и аналитики.

---

## 📋 Возможности

### Веб-страницы (JSON-ответы для фронтенда)

- **Главная** — приветствие по времени суток, информация по картам, топ-5 транзакций, курсы валют, цены акций
- **События** — расходы и поступления по категориям за период (неделя / месяц / год / всё время)

### Сервисы

- **Кешбэк-категории** — какие категории выгодны для повышенного кешбэка в заданном месяце
- **Инвесткопилка** — сумма, которую можно отложить через округление трат (шаг 10/50/100 ₽)
- **Простой поиск** — поиск по подстроке в описании или категории (регистронезависимо)
- **Поиск телефонов** — находит транзакции с мобильными номерами
- **Поиск переводов физлицам** — переводы с именем и инициалом (например, «Валерий А.»)

### Отчёты

- **Траты по категории** — за последние 3 месяца от указанной даты
- **Траты по дням недели** — средние траты в каждый день недели
- **Траты в рабочий/выходной день** — сравнение средних трат

Все отчёты сохраняются в JSON-файл через **декоратор** (с параметром и без).

### Внешние API

- **Курсы валют** — [ЦБ РФ](https://www.cbr-xml-daily.ru/daily_json.js) (без ключа)
- **Цены акций S&P 500** — [Finnhub](https://finnhub.io/) (нужен бесплатный ключ)

---

## 🛠 Стек технологий

| Категория             | Технология                 |
|-----------------------|----------------------------|
| Язык                  | Python 3.14                |
| Менеджер зависимостей | Poetry 2.x                 |
| Обработка данных      | pandas, openpyxl           |
| HTTP-запросы          | requests                   |
| Переменные окружения  | python-dotenv              |
| Тестирование          | pytest, pytest-cov         |
| Качество кода         | flake8, black, isort, mypy |

---

## 📁 Структура проекта

```
coursework_1/
├── data/
│   ├── .gitkeep
│   └── operations.xlsx             # не коммитится (персональные данные)
├── src/
│   ├── __init__.py
│   ├── utils.py                    # чтение Excel, приветствие, API
│   ├── views.py                    # веб-страницы «Главная», «События»
│   ├── services.py                 # 5 сервисов
│   ├── reports.py                  # 3 отчёта + декоратор
│   └── main.py                     # точка входа
├── tests/
│   ├── __init__.py
│   ├── test_utils.py               # 26 тестов
│   ├── test_views.py               # 13 тестов
│   ├── test_services.py            # 12 тестов
│   └── test_reports.py             # 14 тестов
├── .env                            # секреты (не коммитится)
├── .env_template                   # шаблон .env
├── .flake8                         # настройки flake8
├── .gitignore
├── poetry.lock
├── poetry.toml
├── pyproject.toml                  # зависимости и настройки
├── README.md
└── user_settings.json              # валюты и акции для отображения
```

---

## 🚀 Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/nnc-k/skypro-first-term-paper.git
cd skypro-first-term-paper
```

### 2. Установить Poetry

Если Poetry не установлен:

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Инструкция для других ОС: https://python-poetry.org/docs/#installation

### 3. Включить создание `.venv` в папке проекта

```bash
poetry config virtualenvs.in-project true
```

### 4. Установить зависимости

```bash
poetry install
```

### 5. Настроить переменные окружения

Скопируй `.env_template` в `.env`:

```bash
copy .env_template .env
```

Открой `.env` и вставь **свой API-ключ Finnhub**:

```
STOCK_API_KEY=твой_ключ_с_https://finnhub.io/register
```

### 6. Положить Excel-файл

Скопируй `operations.xlsx` из задания в папку `data/`:

```
data/operations.xlsx
```

---

## ▶️ Запуск

```bash
poetry run python -m src.main
```

Терминал выведет:

- JSON главной страницы
- JSON страницы событий (за месяц и за неделю)
- Кешбэк по категориям
- Сумму для Инвесткопилки
- Результаты поиска (по подстроке, телефонам, переводам)
- Три отчёта (сохраняются в `*_report.json`)

---

## 🧪 Тестирование

### Запустить все тесты

```bash
poetry run pytest
```

### С покрытием и HTML-отчётом

```bash
poetry run pytest --cov=src --cov-report=html:htmlcov
```

Отчёт откроется в `htmlcov/index.html`.

**Текущий результат:**

- ✅ **65 тестов**
- ✅ **Покрытие 100%** (для всех модулей в `src/`, кроме `main.py`)

---

## 🧹 Качество кода

### Стиль (flake8)

```bash
poetry run flake8 src tests
```

### Форматирование (black)

```bash
poetry run black src tests
```

### Сортировка импортов (isort)

```bash
poetry run isort src tests
```

### Проверка типов (mypy)

```bash
poetry run mypy src
```

---

## 📊 Формат JSON-ответов

### Главная страница

```json
{
  "greeting": "Добрый день",
  "cards": [
    {
      "last_digits": "5814",
      "total_spent": 1262.00,
      "cashback": 12.62
    }
  ],
  "top_transactions": [
    {
      "date": "21.12.2021",
      "amount": 1198.23,
      "category": "Переводы",
      "description": "Перевод Кредитная карта"
    }
  ],
  "currency_rates": [
    {"currency": "USD", "rate": 84.26},
    {"currency": "EUR", "rate": 97.87}
  ],
  "stock_prices": [
    {"stock": "AAPL", "price": 332.27}
  ]
}
```

### Страница События

```json
{
  "expenses": {
    "total_amount": 46715,
    "main": [
      {"category": "ЖКХ", "amount": 14216},
      {"category": "Остальное", "amount": 5227}
    ],
    "transfers_and_cash": [
      {"category": "Переводы", "amount": 5986}
    ]
  },
  "income": {
    "total_amount": 5986,
    "main": [
      {"category": "Пополнения", "amount": 3500}
    ]
  },
  "currency_rates": [],
  "stock_prices": []
}
```

---

## ⚙️ Настройки

### `user_settings.json`

```json
{
  "user_currencies": ["USD", "EUR"],
  "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
}
```

- `user_currencies` — коды валют для отображения (ЦБ РФ отдаёт USD, EUR, CNY, GBP, JPY и др.)
- `user_stocks` — тикеры акций S&P 500 для Finnhub

### `.env`

```
STOCK_API_KEY=ваш_ключ_finnhub
```

---

## 🔒 Безопасность

В репозиторий **не попадают**:

- ❌ `.env` — API-ключи
- ❌ `data/operations.xlsx` — персональные данные транзакций
- ❌ `*_report.json` — отчёты (генерируются автоматически)
- ❌ `.venv/`, `.idea/`, `__pycache__/`, `htmlcov/`, `logs/`

Всё это защищено `.gitignore`.

---

## 📝 Лицензия

Учебный проект. Свободное использование в образовательных целях.

---

## 👤 Автор

**nnc-k** — первая курсовая работа, 2026 г.