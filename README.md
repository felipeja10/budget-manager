# budget-manager

Python 3.14+ CLI personal budget manager with validated transactions, CSV storage,
filtering, and income/expense/balance summaries. Commands run without interactive
prompts.

Install dependencies from the repository directory:

```bash
uv sync
uv run budget --help
```

Add transactions, list them, and calculate a summary:

```bash
uv run budget add 2000.00 --kind income --category salary --date 2026-09-04
uv run budget add 18.50 --kind expense --category food --date 2026-09-05
uv run budget list
uv run budget list --category food --kind expense
uv run budget summary
```

`add` creates `data/transactions.csv` and its directory if they are missing. IDs
default to the next number after the highest existing `T`-number, starting at
`T001`. Use `--id CUSTOM-ID` to supply your own unique ID, and `--currency EUR`
to specify the currency explicitly. Date, kind, and category are required.

Use `--file` before or after the subcommand to select another CSV:

```bash
uv run budget --file ./data/demo.csv add 18.50 --kind expense --category food --date 2026-09-05
uv run budget list --file ./data/demo.csv
uv run budget summary --file ./data/demo.csv
uv run budget validate ./data/demo.csv
```

`list` writes CSV with a header, preserving transaction order. `summary` prints
income, expenses, and balance in EUR. Listing and summaries never change the
file. A valid header-only CSV gives an empty list and zero totals. Missing files
are errors for read commands; only `add` creates a new file.

If this repository belongs to a parent uv workspace, select this package with
`uv run --package budget-manager budget ...` (and `uv sync --package budget-manager`).

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
code 0. The same exit codes apply to all commands, with results on stdout and
errors on stderr.

Saves validate the complete collection, write and flush a temporary file in the
destination directory, then atomically replace the destination. Invalid existing
CSV data is rejected before `add` writes anything. Failed writes leave the old
file intact and clean up the temporary file. Saves preserve decimal amounts
without converting them to floats.

For automation, supply an absolute `--file` path. Relative paths, including the
default `data/transactions.csv`, are resolved from the current working directory.
After `uv sync`, a WSL/Linux scheduler can invoke the installed command directly:

```bash
/absolute/path/budget-manager/.venv/bin/budget --file /absolute/path/budget-manager/data/transactions.csv summary
```

An optional daily cron example (replace every path before using it):

```cron
0 20 * * * /absolute/path/budget-manager/.venv/bin/budget --file /absolute/path/budget-manager/data/transactions.csv summary >> /absolute/path/budget-manager/summary.log 2>&1
```

On native Windows, the executable is `.venv\Scripts\budget.exe`. Test the exact
command manually before configuring your scheduler. Add `--verbose` for diagnostic
logging on stderr, including the resolved CSV path. These instructions do not
install or enable a scheduled task.

Run writes sequentially: concurrent writers are not locked and can overwrite each
other's changes. No currency conversion or interactive menu is implemented.

Run checks:

```bash
uv run pytest
uv run ruff check .
```
