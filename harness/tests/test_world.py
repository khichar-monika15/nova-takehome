from datetime import date

from audit.world import build, charge_code
from fixtures import email, invoice, line, msa, tracking

AS_OF = date(2032, 8, 31)


def test_pickup_from_tracking_beats_the_invoice_date():
    inv = invoice("INV-1", "2032-01-02", [line("S1", "2031-12-20", "Air freight", "AAA-BBB", "241", "kg", "6.69",
                                               "1612.29")])
    w = build([msa(), inv, tracking([("S1", "picked_up", "2031-12-25", "AAA")])], AS_OF)
    p = w.shipments["S1"].pickup
    assert (p.date, p.source) == (date(2031, 12, 25), "tracking")


def test_pickup_falls_back_to_status_email_then_invoice():
    inv = invoice("INV-1", "2032-01-02", [line("S1", "2031-12-20", "Air freight", "AAA-BBB", "1", "kg", "1", "1")])
    status = email("batch_01/0009.eml", "2031-12-21T10:00:00+00:00", ("Ops", "ops@carrier.example"),
                   statuses=[{"shipment": "S1", "event": "picked_up", "date": "2031-12-19", "station": "AAA",
                              "quote": "Shipment S1 was picked up", "page": 1, "quote_ok": True}])
    assert build([msa(), inv, status], AS_OF).shipments["S1"].pickup.source == "status_email"
    assert build([msa(), inv], AS_OF).shipments["S1"].pickup.source == "invoice"


def test_charge_codes_come_from_the_alias_table():
    c = build([msa()], AS_OF).contracts["C-1"]
    assert charge_code(c, "Screening fee (adj.)") == "SEC"
    assert charge_code(c, "screening  FEE") == "SEC"
    assert charge_code(c, "Air freight") == "FRT"
    assert charge_code(c, "Something unknown") is None


def test_invoice_links_to_its_contract_and_lines_get_codes():
    inv = invoice("INV-1", "2032-01-02", [line("S1", "2031-12-20", "DG handling", "AAA-BBB", "1", "shipment",
                                               "124.02", "124.02")])
    w = build([msa(), inv], AS_OF)
    got = w.invoices["INV-1"][0]
    assert got.contract.id == "C-1"
    assert got.lines[0].code == "DG"


def test_invoice_ids_are_normalised_for_keys():
    inv = invoice("tx-us 2035:0210#", "2032-01-02", [])
    assert "TX-US20350210" in build([msa(), inv], AS_OF).invoices


def test_amendment_attaches_to_its_parent_contract():
    amd = msa(cid="C-1", received="2032-02-01T09:00:00+00:00", doc_type="amendment", amendment_ref="C-1/AMD-1",
              effective_date="2032-02-01")
    amd["ref"] = "batch_01/0002.eml#AMD-1.pdf"
    c = build([msa(), amd], AS_OF).contracts["C-1"]
    assert [a.ref for a in c.amendments] == ["batch_01/0002.eml#AMD-1.pdf"]
    assert c.msa.ref == "batch_01/0001.eml#MSA-C-1.pdf"


def test_lanes_match_whatever_way_the_document_writes_them():
    from audit.world import norm_lane
    assert norm_lane("USTQM to INVKH") == "USTQM-INVKH"
    assert norm_lane("USNBR-USTQM") == "USNBR-USTQM"
    assert norm_lane("USNBR USTQM") == "USNBR-USTQM"
    assert norm_lane("USNBR → USTQM") == "USNBR-USTQM"
    assert norm_lane(None) is None


def test_lines_get_the_charge_kind_the_contract_gives_their_code():
    from fixtures import renamed_codes
    inv = invoice("INV-K", "2032-01-02", [line("S1", "2031-12-20", "FSC", "AAA to BBB", "100", "percent_of_base",
                                               "20.16", "20.16")])
    got = build([renamed_codes(msa()), inv], AS_OF).invoices["INV-K"][0].lines[0]
    assert (got.code, got.kind, got.lane) == ("FSC", "fuel", "AAA-BBB")
