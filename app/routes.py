"""
routes.py
---------
All HTTP endpoints for the Expense Tracker API, registered as a Flask
Blueprint. Business/storage logic lives in models.py; this file is only
responsible for translating HTTP <-> Python calls and error handling.
"""

from flask import Blueprint, jsonify, request, render_template

from .models import Database, VALID_CATEGORIES
from .validators import ValidationError, validate_expense_payload

api = Blueprint("api", __name__)
db = Database()


# ---------- Frontend ----------

@api.route("/")
def dashboard():
    return render_template("index.html", categories=sorted(VALID_CATEGORIES))


# ---------- Expense CRUD ----------

@api.route("/api/expenses", methods=["GET"])
def list_expenses():
    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    expenses = db.list_expenses(category=category, start_date=start_date, end_date=end_date)
    return jsonify({"count": len(expenses), "expenses": expenses})


@api.route("/api/expenses/<int:expense_id>", methods=["GET"])
def get_expense(expense_id: int):
    expense = db.get_expense(expense_id)
    if not expense:
        return jsonify({"error": f"Expense {expense_id} not found."}), 404
    return jsonify(expense)


@api.route("/api/expenses", methods=["POST"])
def create_expense():
    try:
        data = validate_expense_payload(request.get_json(force=True, silent=True) or {})
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    expense = db.create_expense(**data)
    return jsonify(expense), 201


@api.route("/api/expenses/<int:expense_id>", methods=["PUT", "PATCH"])
def update_expense(expense_id: int):
    if not db.get_expense(expense_id):
        return jsonify({"error": f"Expense {expense_id} not found."}), 404

    try:
        data = validate_expense_payload(
            request.get_json(force=True, silent=True) or {}, partial=True
        )
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    expense = db.update_expense(expense_id, **data)
    return jsonify(expense)


@api.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id: int):
    deleted = db.delete_expense(expense_id)
    if not deleted:
        return jsonify({"error": f"Expense {expense_id} not found."}), 404
    return jsonify({"message": f"Expense {expense_id} deleted."}), 200


# ---------- Analytics ----------

@api.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    return jsonify({
        "total_spent": db.total_spent(start_date, end_date),
        "by_category": db.spending_by_category(start_date, end_date),
    })


@api.route("/api/analytics/monthly", methods=["GET"])
def analytics_monthly():
    return jsonify({"monthly": db.monthly_summary()})


@api.route("/api/categories", methods=["GET"])
def categories():
    return jsonify({"categories": sorted(VALID_CATEGORIES)})


# ---------- Error handlers ----------

@api.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found."}), 404


@api.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed."}), 405
