"""
models.py
---------
Data-access layer for the Expense Tracker application.

This module wraps all raw SQLite access behind a small `Database` class
so the rest of the app never has to write SQL directly. Keeping this
separate from routes.py is a deliberate separation-of-concerns choice:
it makes the storage engine swappable (e.g. to Postgres) without
touching any API code.
"""

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "expenses.db"

VALID_CATEGORIES = {
    "Food", "Transport", "Housing", "Utilities", "Entertainment",
    "Health", "Shopping", "Education", "Travel", "Other",
}


class Database:
    """Thin wrapper around sqlite3 for the expenses table."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT NOT NULL,
                    amount      REAL NOT NULL CHECK (amount > 0),
                    category    TEXT NOT NULL,
                    note        TEXT,
                    date        TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)"
            )

    # ---------- CRUD ----------

    def create_expense(
        self, title: str, amount: float, category: str,
        date: str, note: Optional[str] = None,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO expenses (title, amount, category, note, date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (title, amount, category, note, date, datetime.now(UTC).isoformat()),
            )
            new_id = cur.lastrowid
        # Read happens on a fresh connection after the insert has committed
        # (the `with` block above commits on __exit__), so the row is visible.
        return self.get_expense(new_id)

    def get_expense(self, expense_id: int) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_expenses(
        self, category: Optional[str] = None,
        start_date: Optional[str] = None, end_date: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM expenses WHERE 1=1"
        params: list[Any] = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date DESC, id DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def update_expense(self, expense_id: int, **fields: Any) -> Optional[dict[str, Any]]:
        if not fields:
            return self.get_expense(expense_id)

        allowed = {"title", "amount", "category", "note", "date"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_expense(expense_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [expense_id]

        with self._connect() as conn:
            conn.execute(f"UPDATE expenses SET {set_clause} WHERE id = ?", params)
        return self.get_expense(expense_id)

    def delete_expense(self, expense_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cur.rowcount > 0

    # ---------- Analytics ----------

    def total_spent(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> float:
        query = "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE 1=1"
        params: list[Any] = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        with self._connect() as conn:
            return conn.execute(query, params).fetchone()["total"]

    def spending_by_category(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        query = """
            SELECT category, SUM(amount) AS total, COUNT(*) AS count
            FROM expenses WHERE 1=1
        """
        params: list[Any] = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " GROUP BY category ORDER BY total DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def monthly_summary(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT strftime('%Y-%m', date) AS month,
                       SUM(amount) AS total,
                       COUNT(*) AS count
                FROM expenses
                GROUP BY month
                ORDER BY month
                """
            ).fetchall()
            return [dict(r) for r in rows]
