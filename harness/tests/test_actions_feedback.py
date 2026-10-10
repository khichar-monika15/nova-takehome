import json
from datetime import date
from decimal import Decimal

from audit import actions, confidence, feedback, terms
from audit.rules import Candidate, waiver
from audit.world import build
from fixtures import email, invoice, line, msa
from test_rules_invoice import WES, waiver_mail

AS_OF = date(2032, 8, 31)


def oc(inv="INV-1", amount="100.00", pickup="tracking", lanes=("AAA-BBB",), verdict="finding", cls="overcharge"):
    return Candidate(cls=cls, verdict=verdict, invoice_id=inv, contract_id="C-1",
                     amount=Decimal(amount) if amount else None, evidence=[{"doc": "d", "page": 1, "quote": "q"}],
                     features={"pickup_source": pickup, "judgment": False, "inr": False, "lanes": set(lanes)})


def act(cands, mode):
    actions.assign(cands, mode, AS_OF)
    return [c.action for c in cands]


def test_supervised_drafts_and_never_executes():
    assert act([oc()], "supervised") == ["draft:dispute"]


def test_autonomous_executes_only_when_the_unattended_test_passes():
    assert act([oc()], "autonomous") == ["execute:dispute"]
    assert act([oc(pickup="invoice")], "autonomous") == ["human_review"]
    assert act([oc(pickup="awb")], "autonomous") == ["human_review"]


def test_five_thousand_or_more_on_one_invoice_is_human_review_in_both_modes():
    assert act([oc(amount="5000.00")], "supervised") == ["human_review"]
    assert act([oc(amount="3000.00"), oc(amount="2000.00", cls="duplicate")], "autonomous") == ["human_review"] * 2
    assert act([oc(amount="4999.99")], "autonomous") == ["execute:dispute"]


def test_conflict_escalates_and_blocks_execution_on_the_same_contract_and_lane():
    cands = [oc("INV-9", None, verdict="conflict"), oc("INV-1"), oc("INV-2", lanes=("CCC-DDD",))]
    assert act(cands, "autonomous") == ["escalate", "human_review", "execute:dispute"]


def test_cannot_determine_requests_the_document():
    cd = oc(amount=None, verdict="cannot_determine")
    assert act([cd], "supervised") == ["draft:request_document"]
    assert act([oc(amount=None, verdict="cannot_determine")], "autonomous") == ["execute:request_document"]


def test_portfolio_actions():
    due = Candidate(cls="cashback", verdict="finding", contract_id="C-1", period="2032-Q1", credit_type="rebate",
                    amount=Decimal("10.00"), due=date(2032, 5, 15), features={})
    not_due = Candidate(cls="cashback", verdict="finding", contract_id="C-1", period="2032-Q2",
                        credit_type="rebate", amount=Decimal("10.00"), due=date(2032, 9, 15), features={})
    exp = Candidate(cls="expiry", verdict="finding", contract_id="C-1", deadline=date(2032, 9, 20), features={})
    risk = Candidate(cls="late_fee_risk", verdict="finding", invoice_id="X", amount=Decimal("1.00"), features={})
    assert act([due, not_due, exp, risk], "supervised") == ["draft:claim_credit", "internal:track_credit",
                                                            "internal:alert", "internal:payment_reminder"]


def test_confidence_is_lower_for_weaker_evidence():
    strong, weak = oc(), oc(pickup="invoice")
    weak.features["judgment"] = True
    assert 0 < confidence.score(weak) < confidence.score(strong) < 1


def fb_file(tmp_path, items, after="batch_01"):
    f = tmp_path / "fb.json"
    f.write_text(json.dumps({"schema_version": "1.0", "after_batch": after, "decided_at": "2032-09-01T10:00:00Z",
                             "items": items}))
    return f


def item(item_id, decision, key, fact=None, scope=None):
    return {"item_id": item_id, "finding_key": key, "solicited": True, "decision": decision,
            "fact": fact or {"type": "dispute_closed", "subject": {}, "value": {}},
            "scope": scope or {"kind": "one_off", "applies_to": {"invoice_id": key.get("invoice_id")},
                               "valid_from": "2032-09-01", "valid_to": None}}


def test_feedback_close_and_reject_drop_only_their_key(tmp_path):
    feedback.store(fb_file(tmp_path, [item("fb-1", "close", {"invoice_id": "INV-1", "class": "overcharge"}),
                                      item("fb-2", "reject", {"invoice_id": "INV-2", "class": "overcharge"})]),
                   tmp_path)
    got = feedback.apply([oc("INV-1"), oc("INV-2"), oc("INV-3")], feedback.load(tmp_path))
    assert [c.invoice_id for c in got] == ["INV-3"]


def test_feedback_override_amount_sets_amount_and_learned_at(tmp_path):
    fact = {"type": "dispute_closed", "subject": {}, "value": {"status": "settled", "amount_usd": "212.40"}}
    feedback.store(fb_file(tmp_path, [item("fb-7", "override_amount", {"invoice_id": "INV-1",
                                                                       "class": "overcharge"}, fact)]), tmp_path)
    got = feedback.apply([oc("INV-1")], feedback.load(tmp_path))
    assert (got[0].amount, got[0].learned_at) == (Decimal("212.40"), {"feedback_item_id": "fb-7",
                                                                      "batch": "batch_01"})


def test_one_off_waiver_approval_covers_only_its_month(tmp_path):
    statement = invoice("ST-10", "2032-11-01", [
        line(None, None, "Storage programme fee", None, "1", "month", "678.00", "678.00", refers=None),
        line(None, None, "Storage programme fee", None, "1", "month", "678.00", "678.00", refers=None)])
    statement["facts"]["lines"][0]["refers_to_period"] = "2032-10"
    statement["facts"]["lines"][1]["refers_to_period"] = "2032-11"
    kim = ("Kim Key", "kim@carrier.example")
    mail = email("batch_01/0050.eml", "2032-10-05T10:00:00+00:00", kim, intent="waiver",
                 waivers=[{"shipments": [], "months": ["2032-10", "2032-11"], "invoice_id": None,
                           "charge": "Storage programme fee", "one_off": False, "conditional": False,
                           "condition": None, "condition_met": "not_applicable",
                           "quote": "we waive the storage programme fee for October and November", "page": 1,
                           "quote_ok": True}])
    base = msa()
    base["facts"]["tables"]["aliases"].append({"code": "SPROG", "labels": ["Storage programme fee"],
                                                "quote": "x", "page": 1, "quote_ok": True})
    base["facts"]["tables"]["accessorials"].append({"code": "SPROG", "name": "Storage programme fee",
                                                     "fee": "678.00", "basis": "month", "months": [],
                                                     "quote": "x", "page": 1, "quote_ok": True})
    fb = [{"item_id": "fb-4", "batch": "batch_01", "decision": "one_off_approval",
           "finding_key": {"invoice_id": "ST-10", "class": "waived_but_billed"},
           "fact": {"type": "waiver_scope", "subject": {"person": "Kim Key", "party": "CAR-US"},
                    "value": {"months": ["2032-10"]}},
           "scope": {"kind": "one_off", "applies_to": {"invoice_id": "ST-10"}, "valid_from": "2032-11-30",
                     "valid_to": None}}]
    got = waiver.run(build([base, mail, statement], date(2032, 12, 31), fb))
    assert [(c.invoice_id, c.amount, c.learned_at["feedback_item_id"]) for c in got] == [
        ("ST-10", Decimal("678.00"), "fb-4")]


def test_standing_authority_for_one_category_does_not_cover_another():
    fb = [{"item_id": "fb-3", "batch": "batch_01", "decision": "confirm",
           "finding_key": {"invoice_id": "X", "class": "waived_but_billed"},
           "fact": {"type": "sender_authority", "subject": {"person": "Kim Key", "party": "CAR-US"},
                    "value": {"categories": ["waivers"]}},
           "scope": {"kind": "standing", "applies_to": {"contract_id": "C-1", "person": "Kim Key",
                                                        "category": "waivers"},
                     "valid_from": "2032-01-01", "valid_to": None}}]
    w = build([msa()], AS_OF, fb)
    c = w.contracts["C-1"]
    assert terms.authorised(w, c, "", "Kim Key", "waivers", date(2032, 3, 1))
    assert not terms.authorised(w, c, "", "Kim Key", "rates", date(2032, 3, 1))
    assert not terms.authorised(w, c, "", "Kim Key", "waivers", date(2031, 12, 1))


def test_feedback_granted_waiver_authority_turns_a_waiver_into_a_finding_with_learned_at():
    from test_rules_invoice import dlv_invoice
    fb = [{"item_id": "fb-5", "batch": "batch_01", "decision": "confirm",
           "finding_key": {"invoice_id": "INV-30", "class": "waived_but_billed"},
           "fact": {"type": "sender_authority", "subject": {"person": "Kim Key", "party": "CAR-US"},
                    "value": {"categories": ["waivers"]}},
           "scope": {"kind": "standing", "applies_to": {"contract_id": "C-1", "person": "Kim Key",
                                                        "category": "waivers"},
                     "valid_from": "2031-12-01", "valid_to": None}}]
    got = waiver.run(build([msa(), waiver_mail(("Kim Key", "kim@carrier.example")), dlv_invoice()], AS_OF, fb))
    assert [(c.invoice_id, c.learned_at["feedback_item_id"]) for c in got] == [("INV-30", "fb-5")]
    assert WES


def test_autonomous_needs_a_schedule_1_recipient_to_execute():
    no_contact = oc()
    no_contact.features["recipient"] = False
    assert act([no_contact], "autonomous") == ["human_review"]


def test_report_marks_whether_schedule_1_names_the_dispute_recipient():
    from audit.report import _candidates
    from fixtures import tracking
    from test_rules_invoice import oc_invoice
    base = msa()
    w = build([base, oc_invoice(), tracking([("S1", "picked_up", "2031-12-25", "AAA")])], AS_OF)
    assert [c.features["recipient"] for c in _candidates(w)] == [True]
    for row in base["facts"]["terms"]["schedule1"]:
        row["categories"] = [x for x in row["categories"] if x != "billing_disputes"]
    w = build([base, oc_invoice(), tracking([("S1", "picked_up", "2031-12-25", "AAA")])], AS_OF)
    assert [c.features["recipient"] for c in _candidates(w)] == [False]


def test_a_malformed_feedback_item_is_skipped():
    c = Candidate(cls="overcharge", verdict="finding", invoice_id="INV-1", amount=Decimal("10.00"))
    items = [{"item_id": "fb-x", "decision": "override_amount", "finding_key": {"invoice_id": "INV-1",
                                                                                "class": "overcharge"}, "fact": None},
             {"item_id": "fb-y", "decision": "override_amount", "finding_key": {"invoice_id": "INV-1",
                                                                                "class": "overcharge"},
              "fact": {"value": {"amount_usd": "USD 212.40"}}}]
    out = feedback.apply([c], items)
    assert len(out) == 1 and out[0].amount in (Decimal("10.00"), Decimal("212.40"))


def test_one_off_authority_changes_only_its_own_key():
    from test_rules_invoice import dlv_invoice
    fb = [{"item_id": "fb-6", "batch": "batch_01", "decision": "confirm",
           "finding_key": {"invoice_id": "INV-30", "class": "waived_but_billed"},
           "fact": {"type": "sender_authority", "subject": {"person": "Kim Key", "party": "CAR-US"},
                    "value": {"categories": ["waivers"]}},
           "scope": {"kind": "one_off", "applies_to": {"contract_id": "C-1", "person": "Kim Key",
                                                       "category": "waivers"},
                     "valid_from": "2031-12-01", "valid_to": None}}]
    mail = waiver_mail(("Kim Key", "kim@carrier.example"), shipments=("S1", "S2"))
    got = waiver.run(build([msa(), mail, dlv_invoice("S1", "INV-30"), dlv_invoice("S2", "INV-31")], AS_OF, fb))
    assert [c.invoice_id for c in got if c.verdict == "finding"] == ["INV-30"]
