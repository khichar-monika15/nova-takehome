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
