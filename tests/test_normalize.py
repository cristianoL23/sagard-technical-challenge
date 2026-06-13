import pytest

from src.normalize import infer_scale_from_raw_value, normalize_metric_name, normalize_value, to_display_scale

GBP_SYMBOL = "\u00a3"


@pytest.mark.parametrize(
    "raw, unit_type, expected_value, expected_unit, expected_scale, expected_currency",
    [
        ("$8.4M", "currency", 8.4, "currency", "millions", "USD"),
        ("GBP 5.1M", "currency", 5.1, "currency", "millions", "GBP"),
        (f"{GBP_SYMBOL}5.1M", "currency", 5.1, "currency", "millions", "GBP"),
        ("8.4M", "currency", 8.4, "currency", "millions", None),
        ("($0.68M)", "currency", -0.68, "currency", "millions", "USD"),
        ("$84k", "currency", 84.0, "currency", "thousands", "USD"),
        ("78%", "percentage", 78.0, "percentage", "ones", None),
        ("5.8%", "percentage", 5.8, "percentage", "ones", None),
        ("1,042", "count", 1042.0, "count", "ones", None),
        ("1.28M", "count", 1.28, "count", "millions", None),
    ],
)
def test_normalize_value_display_scale(
    raw, unit_type, expected_value, expected_unit, expected_scale, expected_currency
):
    value, unit, scale, currency = normalize_value(raw, unit_type=unit_type)
    assert value == pytest.approx(expected_value)
    assert unit == expected_unit
    assert scale == expected_scale
    assert currency == expected_currency


def test_normalize_na_returns_none():
    value, unit, scale, currency = normalize_value("n/a", unit_type="currency")
    assert value is None
    assert unit is None
    assert scale == "unknown"
    assert currency is None


@pytest.mark.parametrize(
    "label, expected",
    [
        ("Annual Recurring Revenue", "arr"),
        ("FTE", "headcount"),
        ("NRR", "net_retention"),
        ("cash balance", "cash_balance"),
        ("Cash & Equivalents", "cash_balance"),
        ("revenue", "revenue"),
    ],
)
def test_normalize_metric_name(label, expected):
    assert normalize_metric_name(label) == expected


def test_infer_scale_from_raw_value():
    assert infer_scale_from_raw_value("8.4M") == "millions"
    assert infer_scale_from_raw_value("84k") == "thousands"
    assert infer_scale_from_raw_value("142") == "unknown"


def test_to_display_scale():
    assert to_display_scale(11.2, "millions") == 11.2
    assert to_display_scale(11_200_000, "millions") == 11.2
    assert to_display_scale(204, "unknown") == 204
