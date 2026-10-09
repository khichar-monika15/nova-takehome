from datetime import date
from decimal import Decimal

from audit.rules import duplicate, overcharge, waiver
from audit.world import build
from fixtures import clause, email, invoice, ledger, line, msa, rec, tracking
from test_terms import RAE, amendment, notice

AS_OF = date(2032, 8, 31)


def by_key(cands):
    return {c.invoice_id: c for c in cands}


def oc_invoice(rate="6.69", amount="1612.29", fuel_base="1612.29", fuel="325.04", inv_id="INV-1", kg="241",
               lane="AAA-BBB", shipment="S1", date_="2032-01-02"):
    return invoice(inv_id, date_, [
        line(shipment, "2031-12-25", "Air freight", lane, kg, "kg", rate, amount,
             quote=f"1 {shipment} 2031-12-25 Air freight {lane} {kg} kg {rate} {amount}"),
        line(shipment, "2031-12-25", "Fuel surcharge", lane, fuel_base, "percent_of_base", "20.16", fuel)])


def test_overcharge_reprices_freight_and_the_fuel_on_it():
    w = build([msa(), oc_invoice(), tracking([("S1", "picked_up", "2031-12-25", "AAA")])], AS_OF)
    got = by_key(overcharge.run(w))["INV-1"]
    assert (got.verdict, got.amount) == ("finding", Decimal("196.92"))
    assert got.evidence[0]["quote"].startswith("1 S1 2031-12-25 Air freight")
    assert got.features["pickup_source"] == "tracking"


def test_band_edge_is_not_an_overcharge():
    inv = invoice("INV-2", "2032-01-20", [line("S2", "2032-01-18", "Air freight", "AAA-BBB", "44", "kg", "7.73",
                                               "340.12")])
    assert overcharge.run(build([msa(), inv], AS_OF)) == []


def test_dg_fee_on_a_refrigerant_only_declaration_is_an_overcharge():
    inv = invoice("INV-3", "2032-01-20", [line("S3", "2032-01-18", "DG handling", "AAA-BBB", "1", "shipment",
                                               "124.02", "124.02")])
    dgd = rec("batch_01/0030.eml#DGD-S3.pdf", "dgd",
              {"shipment": "S3", "un_numbers": ["UN1845"], "dangerous_goods_other_than_dry_ice": False,
               "dry_ice_refrigerant_only": True, **clause("UN1845 Dry ice 5.5 kg - refrigerant only", 1)})
    got = by_key(overcharge.run(build([msa(), inv, dgd], AS_OF)))["INV-3"]
    assert got.amount == Decimal("124.02")
    assert got.features["judgment"] is True


def test_conflict_gives_a_range_and_both_sources():
    inv = invoice("INV-4", "2032-03-05", [line("S4", "2032-03-01", "Air freight", "AAA-BBB", "113", "kg", "3.03",
                                               "342.39")])
    got = by_key(overcharge.run(build([msa(), amendment(), notice(RAE), inv], AS_OF)))["INV-4"]
    assert got.verdict == "conflict"
    assert got.amount_range == (Decimal("0.00"), Decimal("16.95"))
    docs = {e["doc"] for e in got.evidence}
    assert "batch_01/0002.eml#AMD-1.pdf" in docs and any(d.endswith(".eml") for d in docs)


def test_missing_cited_annex_gives_cannot_determine():
    inv = invoice("INV-5", "2032-03-05", [line("S5", "2032-03-01", "Air freight", "AAA-BBB", "113", "kg", "6.50",
                                               "734.50")])
    got = by_key(overcharge.run(build([msa(), amendment(cites="Annex A rev 2"), inv], AS_OF)))["INV-5"]
    assert got.verdict == "cannot_determine"
    assert got.missing_doc["name"] == "Annex A rev 2"


def test_duplicate_across_label_aliases_flags_the_later_invoice():
    a = invoice("INV-10", "2032-01-05", [line("S9", "2032-01-02", "Security surcharge", "AAA-BBB", "351", "kg",
                                              "0.12", "42.12")])
    b = invoice("INV-14", "2032-05-05", [line("S9", "2032-01-02", "Screening fee (adj.)", "AAA-BBB", "351", "kg",
                                              "0.12", "42.12")])
    got = duplicate.run(build([msa(), a, b], AS_OF))
    assert [(c.invoice_id, c.amount) for c in got] == [("INV-14", Decimal("42.12"))]


def resend_case(asks=True, copy=False, status="paid"):
    first = invoice("INV-20", "2032-02-01", [line("S7", "2032-01-28", "Air freight", "AAA-BBB", "10", "kg", "7.73",
                                                  "77.30")], ref="batch_01/0020.eml#INV-20.pdf", total="1259.23")
    again = invoice("INV-20", "2032-02-01", first["facts"]["lines"], ref="batch_01/0030.eml#INV-20.pdf",
                    received="2032-04-01T10:00:00+00:00", total="1259.23")
    cover = email("batch_01/0030.eml", "2032-04-01T10:00:00+00:00", ("Billing", "billing@carrier.example"),
                  intent="payment_request",
                  invoice_refs=[{"invoice_id": "INV-20", "asks_payment": asks, "marked_copy_or_reminder": copy,
                                 **clause("Please process payment at your earliest convenience.", 1)}])
    led = ledger([("INV-20", "2032-02-01", "2032-03-17", "1259.23", status, "2032-03-01" if status == "paid" else None)])
    return [msa(), first, again, cover, led]


def test_same_invoice_resent_after_payment_is_a_duplicate_of_the_total():
    got = duplicate.run(build(resend_case(), AS_OF))
    assert [(c.invoice_id, c.amount) for c in got] == [("INV-20", Decimal("1259.23"))]


def test_resend_marked_as_copy_or_unpaid_is_fine():
    assert duplicate.run(build(resend_case(copy=True), AS_OF)) == []
    assert duplicate.run(build(resend_case(status="open"), AS_OF)) == []


def waiver_mail(sender, shipments=("S1",), quoted=False, received="2031-12-20T10:00:00+00:00"):
    w = {"shipments": list(shipments), "months": [], "invoice_id": None, "charge": "Delivery fee",
         **clause("we waive the Delivery fee on AWB S1.", 1)}
    if quoted:
        return email("batch_01/0040.eml", received, sender, intent="waiver",
                     quoted_waivers=[{**w, "quoted_author_name": "Wes Waiver", "quoted_author_email": None}])
    return email("batch_01/0040.eml", received, sender, intent="waiver",
                 waivers=[{**w, "one_off": True, "conditional": False, "condition": None,
                           "condition_met": "not_applicable"}])


def dlv_invoice(shipment="S1", inv_id="INV-30"):
    return invoice(inv_id, "2032-01-10", [line(shipment, "2031-12-25", "Delivery fee", "AAA-BBB", "1", "shipment",
                                               "116.13", "116.13")])


WES = ("Wes Waiver", "wes@carrier.example")


def test_authorised_waiver_makes_the_named_line_a_finding():
    got = waiver.run(build([msa(), waiver_mail(WES), dlv_invoice()], AS_OF))
    assert [(c.invoice_id, c.verdict, c.amount) for c in got] == [("INV-30", "finding", Decimal("116.13"))]


def test_waiver_does_not_cover_another_shipment():
    assert waiver.run(build([msa(), waiver_mail(WES), dlv_invoice("S2", "INV-31")], AS_OF)) == []


def test_waiver_from_someone_without_authority_is_nothing():
    assert waiver.run(build([msa(), waiver_mail(("Kim Key", "kim@carrier.example")), dlv_invoice()], AS_OF)) == []


def test_waiver_seen_only_quoted_is_cannot_determine_asking_the_key_account_manager_or_sender():
    got = waiver.run(build([msa(), waiver_mail(("Ann Payables", "ann@shipper.example"), quoted=True),
                            dlv_invoice()], AS_OF))
    assert [(c.invoice_id, c.verdict) for c in got] == [("INV-30", "cannot_determine")]
    assert got[0].missing_doc["holder"]["person"] == "Wes Waiver"


def test_a_misread_lane_is_taken_from_the_waybill_of_the_shipment():
    awb = rec("batch_01/0003.eml#AWB-S1.pdf", "awb",
              {"shipment": "S1", "executed_date": "2031-12-25", "origin": "AAA", "destination": "BBB", "pieces": "1",
               "actual_kg": "240.6", "chargeable_kg": "241", "master_shipment": "", "house_shipments": [],
               "nature": "", "handling": "", **clause("AIR WAYBILL S1 Origin AAA Destination BBB", 1)})
    w = build([msa(), oc_invoice(lane="AA-BBB"), awb, tracking([("S1", "picked_up", "2031-12-25", "AAA")])], AS_OF)
    got = by_key(overcharge.run(w))["INV-1"]
    assert got.amount == Decimal("196.92")
    assert got.features["lane_from_record"] is True
