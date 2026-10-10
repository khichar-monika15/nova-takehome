from datetime import date
from decimal import Decimal

from audit.money import D, ceil_div, cents, fmt, parse_date


def test_cents_rounds_half_up():
    assert cents(Decimal("0.125")) == Decimal("0.13")
    assert cents(Decimal("292.0034")) == Decimal("292.00")


def test_D_strips_currency_and_thousand_separators():
    assert D("1,701.31") == Decimal("1701.31")
    assert D("USD 1259.23") == Decimal("1259.23")
    assert D("18.38%") == Decimal("18.38")
    assert D(7) == Decimal(7)


def test_fmt_has_two_decimals():
    assert fmt(Decimal("196.9")) == "196.90"


def test_parse_date_formats():
    assert parse_date("2035-07-01") == date(2035, 7, 1)
    assert parse_date("01 Jul 2035") == date(2035, 7, 1)
    assert parse_date("5 March 2041") == date(2041, 3, 5)
    assert parse_date("03/06/2030", "%d/%m/%Y") == date(2030, 6, 3)
    assert parse_date("due 2035-01-10") == date(2035, 1, 10)
    assert parse_date("-") is None


def test_ceil_div():
    assert ceil_div(31, 30) == 2
    assert ceil_div(30, 30) == 1


def test_an_impossible_iso_date_is_no_date():
    assert parse_date("2040-02-30") is None
