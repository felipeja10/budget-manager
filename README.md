# budget-manager

Python CLI personal budget manager. Transaction validation is implemented; financial
services and CSV writes are still to come.

Install dependencies and validate a CSV without modifying it:

```bash
uv sync
uv run budget validate path/to/transactions.csv
```

CSV files must have these six columns (in any order, with no duplicates):

```csv
id,date,kind,category,amount,currency
T001,2026-09-04,expense,food,18.50,EUR
```

Validation runs when constructing a `Transaction` and when importing CSV records:

- IDs must be non-empty and unique within an imported file.
- Dates must be real calendar dates in `YYYY-MM-DD` format.
- Amounts must be finite and strictly greater than zero. Money uses `Decimal`;
  pass text, integers, or `Decimal` values rather than Python floats.
- Kinds are `income` and `expense`.
- Categories are `entertainment`, `food`, `freelance`, `gift`, `health`, `housing`,
  `other`, `refund`, `rent`, `salary`, `shopping`, `transport`, `travel`, and
  `utilities`. These include the conversation's suggestions and sample CSV values.
- Currency must be `EUR`. Choice values are case-sensitive.

Invalid CSV records report their row number. Invalid input exits with code 2;
file access/encoding errors exit with code 1. Successful validation exits with
code 0. Validation never writes to the input file.

Run checks:

```bash
uv run pytest
uv run ruff check .
```
