"""Pure operations on validated transactions; no terminal or filesystem access."""

import re
from collections.abc import Iterable
from decimal import Decimal

from budget_manager.models import Transaction
from budget_manager.validation import (
    ValidationError,
    validate_category,
    validate_kind,
)


def validate_transactions(transactions: Iterable[Transaction]) -> list[Transaction]:
    """Materialize a collection and reject duplicate IDs before making changes."""
    result = []
    seen_ids = set()
    for transaction in transactions:
        if not isinstance(transaction, Transaction):
            raise ValidationError("transactions must contain Transaction objects.")
        if transaction.id in seen_ids:
            raise ValidationError(f"duplicate id {transaction.id!r}.")
        seen_ids.add(transaction.id)
        result.append(transaction)
    return result


def add_transaction(
    transactions: Iterable[Transaction], transaction: Transaction
) -> list[Transaction]:
    """Return a new collection, leaving the caller's collection unchanged."""
    return validate_transactions([*transactions, transaction])


def next_transaction_id(transactions: Iterable[Transaction]) -> str:
    """Choose the next T-number without reusing an existing ID."""
    highest = 0
    for transaction in transactions:
        match = re.fullmatch(r"T([0-9]+)", transaction.id)
        if match:
            highest = max(highest, int(match[1]))
    return f"T{highest + 1:03d}"


def list_transactions(
    transactions: Iterable[Transaction],
    category: str | None = None,
    kind: str | None = None,
) -> list[Transaction]:
    if category is not None:
        validate_category(category)
    if kind is not None:
        validate_kind(kind)
    return [
        transaction
        for transaction in transactions
        if (category is None or transaction.category == category)
        and (kind is None or transaction.kind == kind)
    ]


def calculate_totals(transactions: Iterable[Transaction]) -> dict[str, Decimal]:
    totals = {"income": Decimal(0), "expenses": Decimal(0)}
    for transaction in transactions:
        key = "income" if transaction.kind == "income" else "expenses"
        totals[key] += transaction.amount
    return totals


def calculate_balance(transactions: Iterable[Transaction]) -> Decimal:
    totals = calculate_totals(transactions)
    return totals["income"] - totals["expenses"]
