from datetime import date
from decimal import Decimal

from audit.rules import cashback, expiry, late_fees
from audit.world import build
from fixtures import clause, email, invoice, ledger, line, msa

WES = ("Wes Waiver", "wes@carrier.example")


def fee_line(target, amount, n=14):
    return line(None, None, f"Late fee on {target}: overdue, month 1 @ 1.98%", None, "1", "month", "1.98", amount,
                quote=f"{n} - - Late fee on {target}: month 1 @ 1.98% {amount}", refers=target)


def extension(target, new_due, received):
    return email(f"batch_01/0{abs(hash(target + new_due)) % 90 + 10}.eml", f"{received}T10:00:00+00:00", WES,
                 intent="due_date_extension",
                 extensions=[{"invoice_id": target, "new_due_date": new_due,
                              **clause(f"We extend the due date of invoice {target} to {new_due}.", 1)}])


def late_case(extended_to, paid, billed, grace="0", principal="683.82"):
    base = msa(late_fee={"rate_pct": "1.98", "grace_days": grace, "compounding": True, "clause": clause()})
    target = invoice("INV-A", "2032-06-01", [line("S1", "2032-05-28", "Air freight", "AAA-BBB", "1", "kg",
                                                  principal, principal)], due="2032-07-16", total=principal)
    fee_inv = invoice("INV-B", "2032-09-01", [fee_line("INV-A", billed)])
    led = ledger([("INV-A", "2032-06-01", "2032-07-16", principal, "paid", paid)],
                 received="2032-09-20T10:00:00+00:00")
    return [base, target, fee_inv, led, extension("INV-A", extended_to, "2032-07-10")]


def test_late_fee_not_owed_after_an_extension():
    got = late_fees.run(build(late_case("2032-08-25", "2032-08-17", "12.65"), date(2032, 9, 30)), [])
    assert [(c.cls, c.invoice_id, c.amount) for c in got] == [("late_fee_not_owed", "INV-B", Decimal("12.65"))]


def test_late_fee_owed_when_paid_after_grace():
    records = late_case("2032-07-20", "2032-08-09", "78.12", grace="5", principal="3945.45")
    # 20 days late, grace 5 -> 1 month at 1.98% of 3945.45 = 78.12: billed correctly
    assert late_fees.run(build(records, date(2032, 9, 30)), []) == []


def test_late_fee_compounds_over_months():
    records = late_case("2032-07-16", "2032-08-20", "30.00", principal="1000.00")
    # 35 days -> 2 months: 19.80 + 1.98% x 1019.80 = 20.19 -> 39.99 owed; 30.00 billed is not too much
    assert late_fees.run(build(records, date(2032, 9, 30)), []) == []


def test_late_fee_risk_for_an_unpaid_invoice_due_within_14_days():
    inv = invoice("INV-R", "2035-08-22", [line("S1", "2035-08-20", "Air freight", "AAA-BBB", "1", "kg", "990.33",
                                               "990.33")], due="2035-10-06", total="990.33")
    led = ledger([("INV-R", "2035-08-22", "2035-10-06", "990.33", "open", None)], received="2035-09-30T10:00:00+00:00")
    got = late_fees.run(build([msa(), inv, led], date(2035, 9, 30)), [])
    assert [(c.cls, c.amount, c.deadline) for c in got] == [("late_fee_risk", Decimal("19.61"), date(2035, 10, 6))]


def test_no_risk_when_due_more_than_14_days_out_or_paid():
    inv = invoice("INV-R", "2035-08-22", [], due="2035-10-20", total="990.33")
    led = ledger([("INV-R", "2035-08-22", "2035-10-20", "990.33", "open", None)], received="2035-09-30T10:00:00+00:00")
    assert late_fees.run(build([msa(), inv, led], date(2035, 9, 30)), []) == []


def rebate_msa():
    return msa(effective_date="2033-01-01", end_date="2033-12-31",
               rebate={"applies": True, "tiers": [{"threshold": "55000", "pct": "5"}, {"threshold": "90000",
                                                                                        "pct": "7.5"}],
                       "threshold_currency": "USD", "period": "quarter", "credit_due_days": "45",
                       "clause": clause("7.1 Volume rebate tiers", 3)})


def spend(inv_id, d, amount, duty="0"):
    lines = [line(f"S{inv_id}", d, "Air freight", "AAA-BBB", "1", "kg", amount, amount)]
    if duty != "0":
        lines.append(line(f"S{inv_id}", d, "Import duty (disbursement)", "AAA-BBB", "1", "shipment", duty, duty))
    return invoice(inv_id, d, lines)


def test_quarterly_rebate_is_earned_on_qualifying_spend_and_claimed_when_due():
    records = [rebate_msa(), spend("Q2-1", "2033-04-10", "40000.00", duty="9000"), spend("Q2-2", "2033-06-20",
                                                                                         "25566.99")]
    got = cashback.run(build(records, date(2033, 11, 30)))
    assert [(c.period, c.credit_type, c.amount) for c in got] == [("2033-Q2", "rebate", Decimal("3278.35"))]
    assert got[0].due == date(2033, 8, 14)


def test_rebate_below_the_first_tier_is_nothing():
    got = cashback.run(build([rebate_msa(), spend("Q3-1", "2033-07-10", "51381.39", duty="8890.50")],
                             date(2033, 11, 30)))
    assert got == []


def test_expiry_inside_60_days_alerts_and_outside_is_absent():
    c = msa(end_date="2034-03-20", auto_renews=False, term=clause("2.2 Initial term ends 2034-03-20", 3))
    got = expiry.run(build([c], date(2034, 2, 28)))
    assert [(c.contract_id, c.deadline) for c in got] == [("C-1", date(2034, 3, 20))]
    assert expiry.run(build([c], date(2033, 8, 31))) == []


def test_auto_renewing_contract_uses_the_notice_deadline():
    c = msa(end_date="2034-06-30", auto_renews=True, non_renewal_notice_days="90")
    got = expiry.run(build([c], date(2034, 2, 28)))
    assert [c.deadline for c in got] == [date(2034, 4, 1)]


def test_risk_principal_leaves_out_what_we_dispute_on_the_invoice():
    from audit.rules import overcharge
    from fixtures import tracking
    inv = invoice("INV-D", "2032-01-02", [
        line("S1", "2031-12-25", "Air freight", "AAA-BBB", "241", "kg", "6.69", "1612.29"),
        line("S1", "2031-12-25", "Fuel surcharge", "AAA-BBB", "1612.29", "percent_of_base", "20.16", "325.04")],
        due="2032-02-10", total="1937.33")
    led = ledger([("INV-D", "2032-01-02", "2032-02-10", "1937.33", "open", None)], received="2032-02-01T10:00:00+00:00")
    w = build([msa(), inv, led, tracking([("S1", "picked_up", "2031-12-25", "AAA")])], date(2032, 2, 1))
    disputes = overcharge.run(w)
    risk = [c for c in late_fees.run(w, disputes) if c.cls == "late_fee_risk"]
    # 1.98% x (1937.33 - 196.92) = 34.46
    assert [c.amount for c in risk] == [Decimal("34.46")]


def test_inr_spend_converts_per_invoice_rounded_to_cents():
    base = msa(currency="INR", effective_date="2030-01-12", end_date="2032-01-11",
               improvement_credit={"applies": True, "pct": "0.83", "due_days_after_anniversary": "60",
                                   "clause": clause("9.1 Annual improvement credit 0.83%", 4)})
    base["facts"]["tables"]["fx"] = [{"month": "2030-03", "inr_per_usd": "89.59", **clause("2030-03 89.59", 11)},
                                     {"month": "2030-08", "inr_per_usd": "87.97", **clause("2030-08 87.97", 11)}]
    a = invoice("IN-1", "2030-03-10", [line("S1", "2030-03-08", "Air freight", "AAA-BBB", "1", "kg", "54710.92",
                                            "54710.92")], currency="INR")
    b = invoice("IN-2", "2030-08-10", [line("S2", "2030-08-08", "Air freight", "AAA-BBB", "1", "kg", "90556.09",
                                            "90556.09")], currency="INR")
    got = cashback.run(build([base, a, b], date(2031, 2, 28)))
    # 610.68 + 1029.40 = 1640.08 USD; 0.83% = 13.61
    assert [(c.period, c.credit_type, c.amount) for c in got] == [("CY1", "promised_credit", Decimal("13.61"))]


def test_inr_spend_total_is_the_sum_of_per_invoice_rounded_usd():
    base = msa(currency="INR", effective_date="2030-01-12")
    base["facts"]["tables"]["fx"] = [{"month": "2030-03", "inr_per_usd": "89.59", **clause("2030-03 89.59", 11)},
                                     {"month": "2030-08", "inr_per_usd": "87.97", **clause("2030-08 87.97", 11)}]
    a = invoice("IN-1", "2030-03-10", [line("S1", "2030-03-08", "Air freight", "AAA-BBB", "1", "kg", "54710.92",
                                            "54710.92")], currency="INR")
    b = invoice("IN-2", "2030-08-10", [line("S2", "2030-08-08", "Air freight", "AAA-BBB", "1", "kg", "90556.09",
                                            "90556.09")], currency="INR")
    w = build([base, a, b], date(2031, 2, 28))
    assert cashback._spend(w, w.contracts["C-1"], date(2030, 1, 12), date(2031, 1, 11)) == Decimal("1640.08")


def test_late_fee_not_owed_when_only_the_ledger_holds_the_target_invoice():
    records = [r for r in late_case("2032-08-25", "2032-08-17", "12.65") if r["facts"].get("invoice_id") != "INV-A"]
    got = late_fees.run(build(records, date(2032, 9, 30)), [])
    assert [(c.cls, c.invoice_id, c.amount) for c in got] == [("late_fee_not_owed", "INV-B", Decimal("12.65"))]


def test_extension_email_from_someone_without_notices_authority_does_not_move_the_end():
    c = msa(end_date="2034-03-20", auto_renews=False, term=clause("2.2 Initial term ends 2034-03-20", 3))
    change = {"contract_id": "C-1", "change": "extension", "new_end_date": "2035-03-20", "signed_by_both": True,
              **clause("Both parties signed the extension to 2035-03-20.", 1)}
    outsider = email("batch_02/0009.eml", "2034-02-01T10:00:00+00:00", ("Ops", "ops@carrier.example"),
                     contract_changes=[change])
    insider = email("batch_02/0010.eml", "2034-02-01T10:00:00+00:00", ("Kim Key", "kim@carrier.example"),
                    contract_changes=[change])
    assert [x.contract_id for x in expiry.run(build([c, outsider], date(2034, 2, 28)))] == ["C-1"]
    assert expiry.run(build([c, insider], date(2034, 2, 28))) == []


def test_inr_late_fee_converts_once_per_finding():
    base = msa(currency="INR", late_fee={"rate_pct": "1.98", "grace_days": "0", "compounding": True,
                                         "clause": clause()})
    base["facts"]["tables"]["fx"] = [{"month": "2032-09", "inr_per_usd": "7.00", **clause("2032-09 7.00", 11)}]
    target = invoice("INV-A", "2032-06-01", [], due="2032-07-16", total="100.00", currency="INR")
    fee_inv = invoice("INV-B", "2032-09-01", [fee_line("INV-A", "0.10", 13), fee_line("INV-A", "0.10", 14)],
                      currency="INR")
    led = ledger([("INV-A", "2032-06-01", "2032-07-16", "100.00", "paid", "2032-07-10")],
                 received="2032-09-20T10:00:00+00:00")
    got = late_fees.run(build([base, target, fee_inv, led], date(2032, 9, 30)), [])
    # 0.20 INR / 7.00 = 0.0286 -> 0.03 USD once; per line it would be 0.01 + 0.01
    assert [(c.invoice_id, c.amount) for c in got] == [("INV-B", Decimal("0.03"))]
