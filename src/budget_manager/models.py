"""Transaction model: invalid values cannot enter the domain layer."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Self

from budget_manager.validation import (
    TRANSACTION_FIELDS,
    ValidationError,
    validate_amount,
    validate_category,
    validate_currency,
    validate_date,
    validate_id,
    validate_kind,
)


@dataclass(frozen=True)
class Transaction:
    id: str
    date: date
    kind: str
    category: str
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        # Frozen records stay valid after construction, regardless of their source.
        for field, validator in (
            ("id", validate_id),
            ("date", validate_date),
            ("kind", validate_kind),
            ("category", validate_category),
            ("amount", validate_amount),
            ("currency", validate_currency),
        ):
            object.__setattr__(self, field, validator(getattr(self, field)))

    @classmethod
    def from_record(cls, record: Mapping[str, str]) -> Self:
        """Validate an external record before it can be used as a transaction."""
        missing = set(TRANSACTION_FIELDS) - record.keys()
        unexpected = record.keys() - set(TRANSACTION_FIELDS)
        if missing:
            raise ValidationError(f"missing fields: {', '.join(sorted(missing))}.")
        if unexpected:
            raise ValidationError(
                f"unexpected fields: {', '.join(sorted(unexpected))}."
            )
        return cls(
            id=record["id"],
            date=validate_date(record["date"]),
            kind=record["kind"],
            category=record["category"],
            amount=validate_amount(record["amount"]),
            currency=record["currency"],
        )
