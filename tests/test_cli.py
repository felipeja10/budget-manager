import csv
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from budget_manager.cli import main
from budget_manager.storage import load_transactions, save_transactions


def test_valid_csv(tmp_path, capsys):
    path = tmp_path / "transactions.csv"
    path.write_text(
        "id,date,kind,category,amount,currency\n"
        "T001,2026-09-04,expense,food,18.50,EUR\n",
        encoding="utf-8",
    )
    main(["validate", str(path)])
    output = capsys.readouterr()
    assert output.out == "Validated 1 transactions.\n"
    assert output.err == ""


@pytest.mark.parametrize(
    "record",
    [
        "T001,2026-02-30,expense,food,18.50,EUR",
        "T001,2026-09-04,expense,food,-1,EUR",
        "T001,2026-09-04,shopping,food,18.50,EUR",
        "T001,2026-09-04,expense,unknown,18.50,EUR",
        "T001,2026-09-04,expense,food,18.50,USD",
    ],
)
def test_invalid_input_exits_with_stderr(tmp_path, capsys, record):
    path = tmp_path / "transactions.csv"
    path.write_text(
        "id,date,kind,category,amount,currency\n" + record + "\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as error:
        main(["validate", str(path)])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "row 2" in output.err


def test_missing_file_exits_with_io_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(["validate", str(tmp_path / "missing.csv")])
    assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Error:" in output.err


def test_invalid_encoding_exits_with_io_error(tmp_path, capsys):
    path = tmp_path / "transactions.csv"
    path.write_bytes(b"\xff")
    with pytest.raises(SystemExit) as error:
        main(["validate", str(path)])
    assert error.value.code == 1
    assert "Error:" in capsys.readouterr().err


def test_missing_csv_argument(capsys):
    with pytest.raises(SystemExit) as error:
        main(["validate"])
    assert error.value.code == 2
    assert "file" in capsys.readouterr().err


def add_args(path, amount="18.50", **options):
    values = {"date": "2026-09-04", "kind": "expense", "category": "food", **options}
    args = ["add", amount, "--file", str(path)]
    for key, value in values.items():
        args.extend([f"--{key}", value])
    return args


def test_add_list_summary_end_to_end(tmp_path, capsys):
    path = tmp_path / "data" / "transactions.csv"
    main(add_args(path, "2000.00", kind="income", category="salary"))
    assert capsys.readouterr().out == "Added transaction T001.\n"
    main(add_args(path, "150.00"))
    main(add_args(path, "50.00", category="transport"))
    capsys.readouterr()

    main(["list", "--file", str(path), "--category", "food", "--kind", "expense"])
    output = capsys.readouterr()
    records = list(csv.DictReader(io.StringIO(output.out)))
    assert [record["id"] for record in records] == ["T002"]
    assert output.err == ""

    main(["--file", str(path), "summary"])
    output = capsys.readouterr()
    assert (
        output.out
        == "Income: 2000.00 EUR\nExpenses: 200.00 EUR\nBalance: 1800.00 EUR\n"
    )
    assert output.err == ""
    assert len(load_transactions(path)) == 3


@pytest.mark.parametrize(
    ("amount", "options"),
    [
        ("-1", {}),
        ("0", {}),
        ("NaN", {}),
        ("abc", {}),
        ("18.50", {"date": "2026-02-30"}),
        ("18.50", {"kind": "invalid"}),
        ("18.50", {"category": "invalid"}),
        ("18.50", {"currency": "USD"}),
        ("18.50", {"id": " "}),
    ],
)
def test_invalid_add_never_creates_file(tmp_path, capsys, amount, options):
    path = tmp_path / "new" / "transactions.csv"
    with pytest.raises(SystemExit) as error:
        main(add_args(path, amount, **options))
    assert error.value.code == 2
    assert not path.parent.exists()
    assert capsys.readouterr().out == ""


def test_duplicate_explicit_id_preserves_csv(tmp_path, capsys):
    path = tmp_path / "transactions.csv"
    main(add_args(path, id="custom"))
    capsys.readouterr()
    original = path.read_bytes()
    with pytest.raises(SystemExit) as error:
        main(add_args(path, id="custom"))
    assert error.value.code == 2
    assert path.read_bytes() == original
    output = capsys.readouterr()
    assert output.out == ""
    assert "duplicate id" in output.err


def test_add_does_not_overwrite_malformed_existing_csv(tmp_path, capsys):
    path = tmp_path / "transactions.csv"
    original = b"id,date,kind,category,amount,currency\nT001,bad,expense,food,1,EUR\n"
    path.write_bytes(original)
    with pytest.raises(SystemExit) as error:
        main(add_args(path))
    assert error.value.code == 2
    assert path.read_bytes() == original
    assert capsys.readouterr().out == ""


def test_add_failure_returns_io_error_without_success_message(
    tmp_path, capsys, monkeypatch
):
    from budget_manager import storage

    path = tmp_path / "transactions.csv"
    main(add_args(path))
    capsys.readouterr()
    original = path.read_bytes()

    def fail(*args):
        raise PermissionError("cannot replace file")

    monkeypatch.setattr(storage.os, "replace", fail)
    with pytest.raises(SystemExit) as error:
        main(add_args(path))
    assert error.value.code == 1
    assert path.read_bytes() == original
    output = capsys.readouterr()
    assert output.out == ""
    assert "cannot replace file" in output.err


@pytest.mark.parametrize("command", ["list", "summary"])
def test_read_commands_do_not_create_missing_file(tmp_path, capsys, command):
    path = tmp_path / "missing.csv"
    with pytest.raises(SystemExit) as error:
        main([command, "--file", str(path)])
    assert error.value.code == 1
    assert not path.exists()
    assert capsys.readouterr().out == ""


def test_default_file_uses_current_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(
        [
            "add",
            "0.001",
            "--date",
            "2026-09-04",
            "--kind",
            "expense",
            "--category",
            "food",
        ]
    )
    capsys.readouterr()
    assert (tmp_path / "data" / "transactions.csv").exists()
    main(["summary"])
    assert "Balance: -0.001 EUR" in capsys.readouterr().out


def test_empty_csv_summary_and_list(tmp_path, capsys):
    path = tmp_path / "transactions.csv"
    save_transactions(path, [])
    main(["summary", "--file", str(path)])
    assert (
        capsys.readouterr().out
        == "Income: 0.00 EUR\nExpenses: 0.00 EUR\nBalance: 0.00 EUR\n"
    )
    main(["list", "--file", str(path)])
    assert capsys.readouterr().out == "id,date,kind,category,amount,currency\n"


def test_absolute_path_works_after_process_restart_from_another_directory(tmp_path):
    path = tmp_path / "data" / "transactions.csv"
    environment = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
    }
    command = [sys.executable, "-c", "from budget_manager.cli import main; main()"]
    add = subprocess.run(
        [*command, *add_args(path)],
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert add.returncode == 0, add.stderr
    assert add.stderr == ""
    another_directory = tmp_path / "another"
    another_directory.mkdir()
    summary = subprocess.run(
        [*command, "summary", "--file", str(path), "--verbose"],
        cwd=another_directory,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert summary.returncode == 0, summary.stderr
    assert "Balance: -18.50 EUR" in summary.stdout
    assert str(path.resolve()) in summary.stderr
    assert "DEBUG" not in summary.stdout


def test_help_lists_supported_commands(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    assert error.value.code == 0
    output = capsys.readouterr().out
    for command in ("add", "list", "summary", "validate"):
        assert command in output
    assert "backup" not in output
