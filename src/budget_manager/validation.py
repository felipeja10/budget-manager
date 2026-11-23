"""Validation shared by transaction construction, CLI input, and CSV imports."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

TRANSACTION_FIELDS = ("id", "date", "kind", "category", "amount", "currency")
ALLOWED_KINDS = frozenset({"income", "expense"})
ALLOWED_CATEGORIES = frozenset(
    {
        "entertainment",
        "food",
        "freelance",
        "gift",
        "health",
        "housing",
        "other",
        "refund",
        "rent",
        "salary",
        "shopping",
        "transport",
        "travel",
        "utilities",
    }
)
ALLOWED_CURRENCIES = frozenset({"EUR"})


class ValidationError(ValueError):
    """A transaction contains invalid input."""


def validate_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("id must be a non-empty string.")
    return value.strip()


def validate_date(value: str | date) -> date:
    """Accept a calendar date or a strict YYYY-MM-DD string."""
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise ValidationError(f"date {value!r} must be a valid date in YYYY-MM-DD format.")


def validate_amount(value: str | Decimal | int) -> Decimal:
    """Parse money without binary floating point; require a finite positive value."""
    if isinstance(value, bool) or not isinstance(value, (str, Decimal, int)):
        raise ValidationError(
            "amount must be a number supplied as text, Decimal, or integer."
        )
    try:
        amount = Decimal(value)
    except InvalidOperation, ValueError:
        raise ValidationError(f"amount {value!r} must be a valid number.") from None
    if not amount.is_finite() or amount <= 0:
        raise ValidationError("amount must be finite and greater than 0.")
    return amount


def _validate_choice(value: str, field: str, allowed: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValidationError(
            f"{field} {value!r} is not allowed; choose from: {choices}."
        )
    return value


def validate_kind(value: str) -> str:
    return _validate_choice(value, "kind", ALLOWED_KINDS)


def validate_category(value: str) -> str:
    return _validate_choice(value, "category", ALLOWED_CATEGORIES)


def validate_currency(value: str) -> str:
    return _validate_choice(value, "currency", ALLOWED_CURRENCIES)
