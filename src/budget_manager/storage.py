"""Read CSV transactions, rejecting invalid records at the import boundary."""

import csv
from pathlib import Path

from budget_manager.models import Transaction
from budget_manager.validation import TRANSACTION_FIELDS, ValidationError


def load_transactions(file_path: str | Path) -> list[Transaction]:
    """Read the whole file successfully or raise without returning partial data."""
    transactions = []
    seen_ids = set()
    with Path(file_path).open(newline="", encoding="utf-8-sig") as source:
        reader = csv.reader(source, strict=True)
        try:
            header = next(reader, None)
            if (
                header is None
                or len(header) != len(TRANSACTION_FIELDS)
                or set(header) != set(TRANSACTION_FIELDS)
            ):
                raise ValidationError(
                    "CSV header must contain each field exactly once: "
                    + ",".join(TRANSACTION_FIELDS)
                )
            for values in reader:
                try:
                    if len(values) != len(header):
                        raise ValidationError("expected exactly six CSV fields.")
                    transaction = Transaction.from_record(dict(zip(header, values)))
                    if transaction.id in seen_ids:
                        raise ValidationError(f"duplicate id {transaction.id!r}.")
                except ValidationError as error:
                    raise ValidationError(f"row {reader.line_num}: {error}") from error
                seen_ids.add(transaction.id)
                transactions.append(transaction)
        except csv.Error as error:
            raise ValidationError(
                f"row {reader.line_num}: malformed CSV: {error}"
            ) from error
    return transactions
