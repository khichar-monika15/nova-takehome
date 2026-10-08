"""The same rules on a contract that names its charge codes and lanes its own way."""
from datetime import date
from decimal import Decimal

from audit.rules import cashback, late_fees, overcharge
from audit.world import build
from fixtures import renamed_codes, tracking
from test_rules_invoice import oc_invoice
from test_rules_portfolio import late_case, rebate_msa, spend


def test_overcharge_with_the_carriers_own_codes_and_lane_format():
    w = build([renamed_codes(__import__("fixtures").msa()), oc_invoice(lane="AAA BBB"),
               tracking([("S1", "picked_up", "2031-12-25", "AAA")])], date(2032, 8, 31))
    got = overcharge.run(w)
    assert [(c.invoice_id, c.amount) for c in got] == [("INV-1", Decimal("196.92"))]


def test_late_fee_not_owed_with_a_renamed_late_fee_code():
    records = late_case("2032-08-25", "2032-08-17", "12.65")
    records[0] = renamed_codes(records[0])
    got = late_fees.run(build(records, date(2032, 9, 30)), [])
    assert [(c.cls, c.amount) for c in got] == [("late_fee_not_owed", Decimal("12.65"))]


def test_rebate_spend_with_renamed_codes_still_leaves_out_duty():
    records = [renamed_codes(rebate_msa()), spend("Q2-1", "2033-04-10", "40000.00", duty="9000"),
               spend("Q2-2", "2033-06-20", "25566.99")]
    got = cashback.run(build(records, date(2033, 11, 30)))
    assert [c.amount for c in got] == [Decimal("3278.35")]
