import csv
from decimal import Decimal

import pytest

from budget_manager.storage import load_transactions
from budget_manager.validation import ValidationError


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def test_load_valid_csv_without_changing_input(tmp_path, valid_record):
    path = tmp_path / "transactions.csv"
    write_csv(path, [valid_record])
    original = path.read_bytes()
    transactions = load_transactions(path)
    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("18.50")
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", ""),
        ("date", "2026-02-30"),
        ("amount", "-1"),
        ("amount", "0"),
        ("amount", "NaN"),
        ("kind", "shopping"),
        ("category", "unknown"),
        ("currency", "USD"),
    ],
)
def test_import_rejects_invalid_record_with_row_number(
    tmp_path, valid_record, field, value
):
    path = tmp_path / "transactions.csv"
    invalid_record = {**valid_record, "id": "T002", field: value}
    write_csv(path, [valid_record, invalid_record])
    original = path.read_bytes()
    with pytest.raises(ValidationError, match=f"row 3: .*{field}"):
        load_transactions(path)
    assert path.read_bytes() == original


def test_duplicate_ids_are_rejected_after_trimming(tmp_path, valid_record):
    path = tmp_path / "transactions.csv"
    write_csv(path, [valid_record, {**valid_record, "id": " T001 "}])
    with pytest.raises(ValidationError, match="row 3: duplicate id 'T001'"):
        load_transactions(path)


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "id,date\n",
        "id,date,kind,category,amount,amount\n",
        "id,date,kind,category,amount,currency,extra\n",
    ],
)
def test_invalid_headers(tmp_path, contents):
    path = tmp_path / "transactions.csv"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValidationError, match="CSV header"):
        load_transactions(path)


@pytest.mark.parametrize(
    "row",
    [
        "T001,2026-09-04,expense,food,18.50\n",
        "T001,2026-09-04,expense,food,18.50,EUR,extra\n",
        'T001,2026-09-04,expense,food,18.50,"EUR\n',
    ],
)
def test_malformed_rows(tmp_path, row):
    path = tmp_path / "transactions.csv"
    path.write_text("id,date,kind,category,amount,currency\n" + row, encoding="utf-8")
    with pytest.raises(ValidationError, match="row 2"):
        load_transactions(path)


def test_reordered_headers_and_utf8_bom(tmp_path):
    path = tmp_path / "transactions.csv"
    path.write_text(
        "currency,amount,category,kind,date,id\nEUR,18.50,food,expense,2026-09-04,T001\n",
        encoding="utf-8-sig",
    )
    assert load_transactions(path)[0].id == "T001"


def test_header_only_file_is_valid(tmp_path):
    path = tmp_path / "transactions.csv"
    path.write_text("id,date,kind,category,amount,currency\n", encoding="utf-8")
    assert load_transactions(path) == []
