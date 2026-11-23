from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal

import pytest

from budget_manager.models import Transaction
from budget_manager.validation import (
    ValidationError,
    validate_amount,
    validate_category,
    validate_currency,
    validate_date,
    validate_kind,
)


def test_valid_record_becomes_typed_transaction(valid_record):
    transaction = Transaction.from_record(valid_record)
    assert transaction.date == date(2026, 9, 4)
    assert transaction.amount == Decimal("18.50")
    assert transaction.currency == "EUR"


def test_valid_leap_day():
    assert validate_date("2024-02-29") == date(2024, 2, 29)


@pytest.mark.parametrize(
    "value",
    [
        "2026-02-30",
        "2025-02-29",
        "2026-13-01",
        "2026-00-01",
        "2026-09-00",
        "0000-01-01",
        "2026-9-04",
        "20260904",
        "2026-W36-5",
        "04/09/2026",
        "2026-09-04T12:00:00",
        "",
        None,
        datetime(2026, 9, 4, 12),
    ],
)
def test_invalid_dates(value):
    with pytest.raises(ValidationError, match="date"):
        validate_date(value)


@pytest.mark.parametrize("value", ["0.01", "18.50", Decimal("12.34"), 2])
def test_positive_amounts(value):
    assert validate_amount(value) == Decimal(value)


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "0.00",
        "-0",
        "-10",
        "-0.01",
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
        "abc",
        "",
        "18,50",
        None,
        True,
        False,
        18.5,
        Decimal("NaN"),
        Decimal(-1),
    ],
)
def test_invalid_amounts(value):
    with pytest.raises(ValidationError, match="amount"):
        validate_amount(value)


@pytest.mark.parametrize("value", ["income", "expense"])
def test_valid_kinds(value):
    assert validate_kind(value) == value


@pytest.mark.parametrize("value", ["shopping", "Income", "", None])
def test_invalid_kinds(value):
    with pytest.raises(ValidationError, match="kind"):
        validate_kind(value)


@pytest.mark.parametrize("value", ["housing", "other", "rent", "refund", "food"])
def test_categories_from_notes_and_sample(value):
    assert validate_category(value) == value


@pytest.mark.parametrize("value", ["unknown", "Food", "", None])
def test_invalid_categories(value):
    with pytest.raises(ValidationError, match="category"):
        validate_category(value)


@pytest.mark.parametrize("value", ["USD", "GBP", "eur", "EURO", "", None])
def test_invalid_currencies(value):
    with pytest.raises(ValidationError, match="currency"):
        validate_currency(value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", " "),
        ("date", "2026-02-30"),
        ("amount", Decimal(-1)),
        ("kind", "invalid"),
        ("category", "invalid"),
        ("currency", "USD"),
    ],
)
def test_direct_construction_also_rejects_invalid_fields(valid_record, field, value):
    valid_record[field] = value
    with pytest.raises(ValidationError, match=field):
        Transaction(**valid_record)


def test_missing_record_field(valid_record):
    del valid_record["amount"]
    with pytest.raises(ValidationError, match="missing fields: amount"):
        Transaction.from_record(valid_record)


def test_unexpected_record_field(valid_record):
    valid_record["extra"] = "value"
    with pytest.raises(ValidationError, match="unexpected fields: extra"):
        Transaction.from_record(valid_record)


def test_validated_transaction_cannot_be_mutated(valid_record):
    transaction = Transaction.from_record(valid_record)
    with pytest.raises(FrozenInstanceError):
        transaction.amount = Decimal(-1)
