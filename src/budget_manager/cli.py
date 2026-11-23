import argparse

from budget_manager.storage import load_transactions
from budget_manager.validation import ValidationError


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Personal budget manager")
    commands = parser.add_subparsers(dest="command")
    validate = commands.add_parser(
        "validate", help="Validate a transaction CSV without changing it"
    )
    validate.add_argument(
        "file", help="CSV containing id,date,kind,category,amount,currency"
    )
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return
    try:
        transactions = load_transactions(args.file)
    except ValidationError as error:
        parser.error(str(error))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Validated {len(transactions)} transactions.")
