"""Validated CSV reads and atomic saves."""

import csv
import os
from collections.abc import Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile

from budget_manager.models import Transaction
from budget_manager.services import validate_transactions
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


def save_transactions(
    file_path: str | Path, transactions: Iterable[Transaction]
) -> None:
    """Replace a CSV only after validating and fully writing its new contents."""
    records = validate_transactions(transactions)
    destination = Path(file_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # The same directory keeps os.replace on the same filesystem.
        with NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary = Path(output.name)
            writer = csv.writer(output)
            writer.writerow(TRANSACTION_FIELDS)
            for transaction in records:
                writer.writerow(
                    [
                        transaction.id,
                        transaction.date.isoformat(),
                        transaction.kind,
                        transaction.category,
                        str(transaction.amount),
                        transaction.currency,
                    ]
                )
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
