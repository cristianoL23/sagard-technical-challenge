import pytest

from src.llm_parsing import map_period_type, map_scale, map_unit


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("quarter", "quarter"),
        ("LTM", "ltm"),
        ("unknown", "unknown"),
        (None, "unknown"),
        ("invalid", "unknown"),
    ],
)
def test_map_period_type(raw, expected):
    assert map_period_type(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("currency", "currency"),
        ("USD", "currency"),
        ("%", "percentage"),
        (None, "unknown"),
    ],
)
def test_map_unit(raw, expected):
    assert map_unit(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("millions", "millions"),
        ("M", "unknown"),
        (None, "unknown"),
    ],
)
def test_map_scale(raw, expected):
    assert map_scale(raw) == expected
