# Design

The application separates the command line, domain operations, and CSV storage.

- `validation.py` defines the accepted dates, amounts, kinds, categories, currencies,
  and IDs. `models.py` applies these checks at construction and creates immutable
  transactions with `date` and `Decimal` values.
- `services.py` adds transactions, checks collection-level ID uniqueness, generates
  IDs, filters records, and calculates totals and balances. These functions have no
  terminal or filesystem access and do not mutate the caller's collection.
- `storage.py` validates CSV imports and reports row numbers. Saves validate the
  complete collection before writing to a temporary file in the destination
  directory. The temporary file is flushed, synchronized, and closed before
  `os.replace` commits the new contents. Failed saves clean up temporary files.
- `cli.py` uses `argparse` for `add`, `list`, `summary`, and `validate`. Inputs are
  validated before writes; results use stdout, errors and diagnostics use stderr.
  Exit codes are 0 for success, 1 for file errors, and 2 for invalid input.

The default store is `data/transactions.csv` relative to the current working
directory. `--file` provides an explicit override; absolute paths are required in
the documented scheduler examples so execution does not depend on its directory.
Commands never request interactive input. No scheduler is configured automatically.

Atomic replacement protects a previous file from incomplete writes but does not
coordinate simultaneous writers. The first version expects sequential writes and
supports EUR only. Tests cover validation, calculations, persistence, failed saves,
and CLI execution across separate processes and working directories.
