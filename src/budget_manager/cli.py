"""Non-interactive command-line entry point."""

import argparse
import csv
import logging
import sys
from decimal import Decimal
from pathlib import Path

from budget_manager.models import Transaction
from budget_manager.services import (
    add_transaction,
    calculate_totals,
    list_transactions,
    next_transaction_id,
)
from budget_manager.storage import load_transactions, save_transactions
from budget_manager.validation import (
    ALLOWED_CATEGORIES,
    ALLOWED_CURRENCIES,
    ALLOWED_KINDS,
    TRANSACTION_FIELDS,
    ValidationError,
    validate_amount,
    validate_date,
    validate_id,
)

logger = logging.getLogger(__name__)


def _argument_type(validator):
    def parse(value):
        try:
            return validator(value)
        except ValidationError as error:
            raise argparse.ArgumentTypeError(str(error)) from error

    return parse


def _common_options(parser, *, root=False):
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/transactions.csv") if root else argparse.SUPPRESS,
        help="Transaction CSV (default: data/transactions.csv in the current directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False if root else argparse.SUPPRESS,
        help="Write diagnostic logging to stderr",
    )


def _build_parser():
    parser = argparse.ArgumentParser(description="Personal budget manager")
    _common_options(parser, root=True)
    commands = parser.add_subparsers(dest="command")

    add = commands.add_parser("add", help="Add and save a transaction")
    _common_options(add)
    add.add_argument("amount", type=_argument_type(validate_amount))
    add.add_argument("--date", required=True, type=_argument_type(validate_date))
    add.add_argument("--kind", required=True, choices=sorted(ALLOWED_KINDS))
    add.add_argument("--category", required=True, choices=sorted(ALLOWED_CATEGORIES))
    add.add_argument("--currency", default="EUR", choices=sorted(ALLOWED_CURRENCIES))
    add.add_argument(
        "--id", type=_argument_type(validate_id), help="Default: next T-number"
    )

    listing = commands.add_parser("list", help="List transactions as CSV")
    _common_options(listing)
    listing.add_argument("--category", choices=sorted(ALLOWED_CATEGORIES))
    listing.add_argument("--kind", choices=sorted(ALLOWED_KINDS))

    summary = commands.add_parser("summary", help="Show income, expenses, and balance")
    _common_options(summary)

    validate = commands.add_parser(
        "validate", help="Validate a CSV without changing it"
    )
    validate.add_argument("file", type=Path, help="CSV to validate")
    validate.add_argument(
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Write diagnostic logging to stderr",
    )
    return parser


def _format_amount(amount: Decimal) -> str:
    """Show at least two decimal places without discarding smaller fractions."""
    whole, _, fraction = format(amount, "f").partition(".")
    return f"{whole}.{fraction.ljust(2, '0')}"


def _print_transactions(transactions):
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(TRANSACTION_FIELDS)
    for transaction in transactions:
        writer.writerow(
            [
                transaction.id,
                transaction.date.isoformat(),
                transaction.kind,
                transaction.category,
                _format_amount(transaction.amount),
                transaction.currency,
            ]
        )


def _add(args, file_path):
    try:
        transactions = load_transactions(file_path)
    except FileNotFoundError:
        transactions = []
    transaction = Transaction(
        id=args.id if args.id is not None else next_transaction_id(transactions),
        date=args.date,
        kind=args.kind,
        category=args.category,
        amount=args.amount,
        currency=args.currency,
    )
    save_transactions(file_path, add_transaction(transactions, transaction))
    logger.debug("Saved %d transactions", len(transactions) + 1)
    print(f"Added transaction {transaction.id}.")


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return
    logging.basicConfig(format="%(levelname)s: %(message)s")
    logger.setLevel(logging.DEBUG if args.verbose else logging.WARNING)
    try:
        file_path = args.file.expanduser().resolve()
        logger.debug("Using transaction file: %s", file_path)
        if args.command == "add":
            _add(args, file_path)
            return
        transactions = load_transactions(file_path)
        if args.command == "validate":
            print(f"Validated {len(transactions)} transactions.")
        elif args.command == "list":
            _print_transactions(
                list_transactions(transactions, args.category, args.kind)
            )
        else:
            totals = calculate_totals(transactions)
            balance = totals["income"] - totals["expenses"]
            print(f"Income: {_format_amount(totals['income'])} EUR")
            print(f"Expenses: {_format_amount(totals['expenses'])} EUR")
            print(f"Balance: {_format_amount(balance)} EUR")
    except ValidationError as error:
        parser.error(str(error))
    except (OSError, UnicodeError) as error:
        logger.debug("Command failed", exc_info=True)
        parser.exit(1, f"Error: {error}\n")
