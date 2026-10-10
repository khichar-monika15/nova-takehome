import json
from datetime import date
from pathlib import Path

import jsonschema
from audit.report import build_report
from fixtures import msa, tracking
from test_rules_invoice import oc_invoice

REPO = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((REPO / "grader/schema/report.schema.json").read_text())
TRACK = tracking([("S1", "picked_up", "2031-12-25", "AAA")])


def test_report_matches_the_schema_and_lists_the_finding():
    rep, _ = build_report([msa(), oc_invoice(), TRACK], [], date(2032, 8, 31), "supervised", {})
    jsonschema.validate(rep, SCHEMA)
    item = rep["findings"][0]
    assert (item["id"], item["invoice_id"], item["amount_usd"], item["action"]) == (
        "overcharge:INV-1", "INV-1", "196.92", "draft:dispute")
    assert all(len("".join(e["quote"].split())) >= 12 for e in item["evidence"])


def test_autonomous_mode_executes_a_clean_case():
    rep, _ = build_report([msa(), oc_invoice(), TRACK], [], date(2032, 8, 31), "autonomous", {})
    assert rep["findings"][0]["action"] == "execute:dispute"


def test_ids_stay_stable_and_a_change_supersedes_the_old_id():
    rep1, hist = build_report([msa(), oc_invoice(), TRACK], [], date(2032, 8, 31), "supervised", {})
    rep2, hist = build_report([msa(), oc_invoice(), TRACK], [], date(2032, 9, 30), "supervised", hist)
    assert rep2["findings"][0]["id"] == rep1["findings"][0]["id"]
    assert rep2["findings"][0]["supersedes"] == []
    changed = oc_invoice(rate="6.89", amount="1660.49", fuel_base="1660.49", fuel="334.75")
    rep3, _ = build_report([msa(), changed, TRACK], [], date(2032, 10, 31), "supervised", hist)
    assert rep3["findings"][0]["id"] != rep1["findings"][0]["id"]
    assert rep3["findings"][0]["supersedes"] == [rep1["findings"][0]["id"]]


def test_documents_received_after_as_of_do_not_count():
    rep, _ = build_report([msa(), oc_invoice(), TRACK], [], date(2031, 12, 31), "supervised", {})
    assert rep["findings"] == []


def test_failed_documents_are_left_out_and_the_report_is_still_valid():
    bad = oc_invoice()
    bad["ok"] = False
    rep, _ = build_report([msa(), bad, TRACK], [], date(2032, 8, 31), "supervised", {})
    jsonschema.validate(rep, SCHEMA)
    assert rep["findings"] == []


def test_a_crashing_rule_drops_only_its_own_items(monkeypatch):
    from audit.rules import cashback

    def boom(w):
        raise AttributeError("'NoneType' object has no attribute 'strftime'")

    monkeypatch.setattr(cashback, "run", boom)
    rep, _ = build_report([msa(), oc_invoice(), TRACK], [], date(2032, 8, 31), "supervised", {})
    jsonschema.validate(rep, SCHEMA)
    assert [f["invoice_id"] for f in rep["findings"]] == ["INV-1"]


def test_report_command_prints_an_empty_valid_report_when_building_fails(monkeypatch, tmp_path):
    from audit import report as report_mod

    monkeypatch.setattr(report_mod, "build_report", lambda *a, **k: 1 / 0)
    rep = report_mod.report("2032-08-31", "supervised", str(tmp_path))
    jsonschema.validate(rep, SCHEMA)
    assert rep["findings"] == [] and rep["mode"] == "supervised"


def test_inr_credit_note_without_a_date_does_not_crash_cashback():
    from audit.rules import cashback
    from audit.world import build
    from fixtures import invoice, line
    from test_rules_portfolio import rebate_msa, spend
    cn = invoice("CN-1", "", [line(None, None, "Credit", None, "1", "other", "10", "-10")], currency="INR",
                 received="2033-07-01T10:00:00+00:00",
                 doc_type="credit_note", credit={"credits_invoice": None, "period": "2033-Q2", "credit_type": "rebate"})
    records = [rebate_msa(), spend("Q2-1", "2033-04-10", "70000.00"), cn]
    assert [c.period for c in cashback.run(build(records, date(2033, 11, 30)))] == ["2033-Q2"]


def test_cannot_determine_with_no_holder_is_not_a_known_recipient():
    from audit import report
    from audit.rules import Candidate
    c = Candidate(cls="waived_but_billed", verdict="cannot_determine", invoice_id="X-1",
                  missing_doc={"name": "original waiver email", "holder": None})
    assert report._recipient_known(None, c) is False
