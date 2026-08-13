# Expense Tracker

A personal expense tracking application: a Flask REST API backed by SQLite,
with a live web dashboard and a full automated test suite.

## Features

- **REST API** — full CRUD for expenses (`POST`, `GET`, `PATCH`, `DELETE`)
- **Analytics endpoints** — total spend, spend-by-category, monthly summaries
- **Input validation** — clean 400 errors for bad titles, amounts, categories, dates
- **Web dashboard** — add expenses, filter by category, see a live doughnut chart
- **16 automated tests** — `unittest`, using an isolated temp database per test
- **Clean architecture** — storage (`models.py`), validation (`validators.py`), and
  HTTP (`routes.py`) are separated so each piece can be tested or swapped independently

## Project structure

```
expense_tracker/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── models.py        # SQLite data-access layer
│   ├── routes.py        # API endpoints (Blueprint)
│   └── validators.py    # Request payload validation
├── static/
│   ├── style.css
│   └── app.js
├── templates/
│   └── index.html       # Dashboard UI
├── tests/
│   └── test_api.py      # 16 unit/integration tests
├── run.py                # Entry point
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:5000** in your browser. The SQLite database
(`expenses.db`) is created automatically on first run.

## Running tests

```bash
python -m unittest discover -s tests -v
```

## API reference

| Method | Endpoint                     | Description                          |
|--------|-------------------------------|---------------------------------------|
| GET    | `/api/expenses`               | List expenses (filters: `category`, `start_date`, `end_date`) |
| GET    | `/api/expenses/<id>`          | Get a single expense                  |
| POST   | `/api/expenses`               | Create an expense                     |
| PATCH  | `/api/expenses/<id>`          | Update an expense (partial)           |
| DELETE | `/api/expenses/<id>`          | Delete an expense                     |
| GET    | `/api/analytics/summary`      | Total spend + breakdown by category   |
| GET    | `/api/analytics/monthly`      | Spend grouped by month                |
| GET    | `/api/categories`              | List valid expense categories         |

### Example: create an expense

```bash
curl -X POST http://127.0.0.1:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 45.50, "category": "Food", "date": "2026-08-01"}'
```

## Design decisions (useful to mention in an interview)

- **Why raw `sqlite3` instead of an ORM?** Keeps the data layer transparent and
  dependency-light, while still isolating all SQL behind a `Database` class so
  swapping to Postgres/SQLAlchemy later only touches `models.py`.
- **Why a Blueprint?** Keeps routing decoupled from app creation, which makes the
  app testable via a factory function (`create_app()`) — each test gets a fresh
  app instance and a fresh temp database, so tests never leak state into each other.
- **Validation is centralized** in `validators.py` rather than scattered across
  route handlers, so every endpoint gets consistent error messages and it's
  trivial to unit-test validation rules in isolation.
- **Indexes** on `date` and `category` in the schema, since those are the columns
  the analytics queries filter/group on.

## Possible extensions

- Auth (per-user expenses)
- Recurring expenses / budgets with alerts
- Export to CSV
- Swap SQLite for Postgres via SQLAlchemy for multi-user deployment
