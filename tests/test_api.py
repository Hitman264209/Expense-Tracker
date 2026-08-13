"""
test_api.py
-----------
Unit + integration tests for the Expense Tracker API.

Run with:
    python -m unittest discover -s tests -v

Each test gets a fresh, isolated temporary SQLite database so tests
never interfere with each other or with real user data.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Database
import app.routes as routes_module


class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        # Point the shared `db` object at a fresh temp file for isolation.
        self.tmp_fd, self.tmp_path = tempfile.mkstemp(suffix=".db")
        routes_module.db = Database(db_path=self.tmp_path)

        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.tmp_fd)
        os.unlink(self.tmp_path)

    def _create_sample_expense(self, **overrides):
        payload = {
            "title": "Groceries",
            "amount": 45.50,
            "category": "Food",
            "date": "2026-08-01",
            "note": "Weekly shop",
        }
        payload.update(overrides)
        return self.client.post("/api/expenses", json=payload)

    # ---------- CRUD ----------

    def test_create_expense_success(self):
        res = self._create_sample_expense()
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["title"], "Groceries")
        self.assertEqual(data["amount"], 45.5)
        self.assertIn("id", data)

    def test_create_expense_missing_title(self):
        res = self._create_sample_expense(title="")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    def test_create_expense_invalid_amount(self):
        res = self._create_sample_expense(amount=-10)
        self.assertEqual(res.status_code, 400)

    def test_create_expense_invalid_category(self):
        res = self._create_sample_expense(category="NotACategory")
        self.assertEqual(res.status_code, 400)

    def test_create_expense_invalid_date(self):
        res = self._create_sample_expense(date="01-08-2026")
        self.assertEqual(res.status_code, 400)

    def test_get_expense(self):
        created = self._create_sample_expense().get_json()
        res = self.client.get(f"/api/expenses/{created['id']}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["title"], "Groceries")

    def test_get_expense_not_found(self):
        res = self.client.get("/api/expenses/9999")
        self.assertEqual(res.status_code, 404)

    def test_list_expenses(self):
        self._create_sample_expense()
        self._create_sample_expense(title="Bus fare", category="Transport", amount=12)
        res = self.client.get("/api/expenses")
        data = res.get_json()
        self.assertEqual(data["count"], 2)

    def test_list_expenses_filtered_by_category(self):
        self._create_sample_expense()
        self._create_sample_expense(title="Bus fare", category="Transport", amount=12)
        res = self.client.get("/api/expenses?category=Transport")
        data = res.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["expenses"][0]["category"], "Transport")

    def test_update_expense(self):
        created = self._create_sample_expense().get_json()
        res = self.client.patch(f"/api/expenses/{created['id']}", json={"amount": 99.99})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["amount"], 99.99)

    def test_update_nonexistent_expense(self):
        res = self.client.patch("/api/expenses/9999", json={"amount": 10})
        self.assertEqual(res.status_code, 404)

    def test_delete_expense(self):
        created = self._create_sample_expense().get_json()
        res = self.client.delete(f"/api/expenses/{created['id']}")
        self.assertEqual(res.status_code, 200)

        follow_up = self.client.get(f"/api/expenses/{created['id']}")
        self.assertEqual(follow_up.status_code, 404)

    def test_delete_nonexistent_expense(self):
        res = self.client.delete("/api/expenses/9999")
        self.assertEqual(res.status_code, 404)

    # ---------- Analytics ----------

    def test_analytics_summary(self):
        self._create_sample_expense(amount=50)
        self._create_sample_expense(title="Bus fare", category="Transport", amount=20)
        res = self.client.get("/api/analytics/summary")
        data = res.get_json()
        self.assertEqual(data["total_spent"], 70)
        self.assertEqual(len(data["by_category"]), 2)

    def test_analytics_monthly(self):
        self._create_sample_expense(date="2026-08-01")
        self._create_sample_expense(title="Rent", category="Housing", amount=500, date="2026-07-01")
        res = self.client.get("/api/analytics/monthly")
        data = res.get_json()
        months = [m["month"] for m in data["monthly"]]
        self.assertIn("2026-08", months)
        self.assertIn("2026-07", months)

    def test_categories_endpoint(self):
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Food", res.get_json()["categories"])


if __name__ == "__main__":
    unittest.main()
