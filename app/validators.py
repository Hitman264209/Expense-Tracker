"""
validators.py
-------------
Small, dependency-free validation helpers for incoming request payloads.
Each function either returns the cleaned value or raises a ValidationError,
which routes.py converts into a proper HTTP 400 response.
"""

from datetime import datetime
from typing import Any

from .models import VALID_CATEGORIES


class ValidationError(Exception):
    """Raised when incoming data fails validation."""


def validate_expense_payload(data: dict[str, Any], partial: bool = False) -> dict[str, Any]:
    """
    Validate and normalize an expense payload.

    :param data: raw JSON body from the client
    :param partial: if True, missing fields are allowed (used for PATCH/update)
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")

    cleaned: dict[str, Any] = {}

    # title
    if "title" in data or not partial:
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("`title` is required and must be a non-empty string.")
        cleaned["title"] = title.strip()

    # amount
    if "amount" in data or not partial:
        amount = data.get("amount")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValidationError("`amount` is required and must be a number.")
        if amount <= 0:
            raise ValidationError("`amount` must be greater than 0.")
        cleaned["amount"] = round(amount, 2)

    # category
    if "category" in data or not partial:
        category = data.get("category")
        if category not in VALID_CATEGORIES:
            raise ValidationError(
                f"`category` must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        cleaned["category"] = category

    # date
    if "date" in data or not partial:
        date = data.get("date")
        if not isinstance(date, str):
            raise ValidationError("`date` is required and must be an ISO string (YYYY-MM-DD).")
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("`date` must be in YYYY-MM-DD format.")
        cleaned["date"] = date

    # note (optional, always allowed)
    if "note" in data:
        note = data.get("note")
        if note is not None and not isinstance(note, str):
            raise ValidationError("`note` must be a string.")
        cleaned["note"] = note

    return cleaned
