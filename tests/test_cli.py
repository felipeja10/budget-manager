import pytest

from budget_manager.cli import main


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
