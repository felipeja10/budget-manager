import pytest


@pytest.fixture
def valid_record():
    return {
        "id": "T001",
        "date": "2026-09-04",
        "kind": "expense",
        "category": "food",
        "amount": "18.50",
        "currency": "EUR",
    }
