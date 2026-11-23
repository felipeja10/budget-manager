from decimal import Decimal

import pytest

from budget_manager.models import Transaction
from budget_manager.services import (
    add_transaction,
    calculate_balance,
    calculate_totals,
    list_transactions,
    next_transaction_id,
)
from budget_manager.validation import ValidationError


@pytest.fixture
def transactions(valid_record):
    return [
        Transaction.from_record(
            {
                **valid_record,
                "id": "T001",
                "kind": "income",
                "category": "salary",
                "amount": "2000.00",
            }
        ),
        Transaction.from_record({**valid_record, "id": "T002", "amount": "150.00"}),
        Transaction.from_record(
            {
                **valid_record,
                "id": "T003",
                "category": "transport",
                "amount": "50.00",
            }
        ),
    ]


def test_totals_and_balance(transactions):
    assert calculate_totals(iter(transactions)) == {
        "income": Decimal("2000.00"),
        "expenses": Decimal("200.00"),
    }
    assert calculate_balance(iter(transactions)) == Decimal("1800.00")


def test_empty_totals_and_balance():
    assert calculate_totals([]) == {"income": Decimal(0), "expenses": Decimal(0)}
    assert calculate_balance([]) == Decimal(0)


def test_negative_balance_and_decimal_accuracy(valid_record):
    transactions = [
        Transaction.from_record({**valid_record, "id": "T001", "amount": "0.10"}),
        Transaction.from_record({**valid_record, "id": "T002", "amount": "0.20"}),
    ]
    assert calculate_balance(transactions) == Decimal("-0.30")


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ({}, ["T001", "T002", "T003"]),
        ({"kind": "income"}, ["T001"]),
        ({"category": "food"}, ["T002"]),
        ({"category": "food", "kind": "expense"}, ["T002"]),
        ({"category": "food", "kind": "income"}, []),
    ],
)
def test_filters_preserve_order(transactions, filters, expected):
    assert [
        item.id for item in list_transactions(iter(transactions), **filters)
    ] == expected


@pytest.mark.parametrize("filters", [{"kind": "invalid"}, {"category": "invalid"}])
def test_invalid_service_filters(transactions, filters):
    with pytest.raises(ValidationError):
        list_transactions(transactions, **filters)


def test_add_returns_new_collection(transactions, valid_record):
    transaction = Transaction.from_record({**valid_record, "id": "T004"})
    result = add_transaction(iter(transactions), transaction)
    assert result == [*transactions, transaction]
    assert len(transactions) == 3


def test_add_rejects_duplicate_id(transactions):
    with pytest.raises(ValidationError, match="duplicate id"):
        add_transaction(transactions, transactions[0])
    assert len(transactions) == 3


@pytest.mark.parametrize(
    ("ids", "expected"),
    [
        ([], "T001"),
        (["T002", "T009", "custom"], "T010"),
        (["T999"], "T1000"),
    ],
)
def test_generated_ids_follow_highest_existing_number(valid_record, ids, expected):
    transactions = [
        Transaction.from_record({**valid_record, "id": item}) for item in ids
    ]
    assert next_transaction_id(transactions) == expected
