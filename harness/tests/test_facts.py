from pathlib import Path

from audit import facts
from audit.docs import read_batch

REPO = Path(__file__).resolve().parents[2]
OVER = REPO / "data/examples/overcharge/docs/batch_01"


def docs_by_ref():
    return {d.ref: d for d in read_batch(OVER)}


def fake_calls(monkeypatch, replies):
    seen = []

    def call(task, system, content, schema, *, state_dir, model=None, **kw):
        seen.append(task)
        return replies[task](content) if callable(replies[task]) else replies[task]

    monkeypatch.setattr(facts, "call_json", call)
    return seen


def test_email_goes_to_the_email_task(monkeypatch, tmp_path):
    seen = fake_calls(monkeypatch, {"email": {"intent": "invoice_cover", "waivers": []}})
    out = facts.extract_doc(docs_by_ref()["batch_01/0003.eml"], tmp_path)
    assert seen == ["email"]
    assert out["kind"] == "email"
    assert out["facts"]["intent"] == "invoice_cover"


def test_invoice_quotes_are_repaired_to_page_text(monkeypatch, tmp_path):
    line = {"shipment": "TE56915687", "quote": "1 TE56915687 2031-12-25 Air  freight USE2-INE2 241kg 6.69 1612.29",
            "page": 1, "amount": "1612.29"}
    seen = fake_calls(monkeypatch, {"classify": {"kind": "invoice", "reason": ""},
                                    "invoice": {"invoice_id": "TX-US-2032-5394", "lines": [line]}})
    out = facts.extract_doc(docs_by_ref()["batch_01/0003.eml#TX-US-2032-5394.pdf"], tmp_path)
    assert seen == ["classify", "invoice"]
    got = out["facts"]["lines"][0]
    assert got["quote"] == "1 TE56915687 2031-12-25 Air freight USE2-INE2 241 kg 6.69 1612.29"
    assert got["quote_ok"] is True


def test_contract_runs_three_calls_and_merges_them(monkeypatch, tmp_path):
    seen = fake_calls(monkeypatch, {"classify": {"kind": "contract", "reason": ""},
                                    "contract_terms": {"contract_id": "C-1"},
                                    "contract_rates": {"rows": []},
                                    "contract_tables": {"fuel": []}})
    out = facts.extract_doc(docs_by_ref()["batch_01/0002.eml#MSA-TBX-US-EXP-E60.pdf"], tmp_path)
    assert sorted(seen) == ["classify", "contract_rates", "contract_tables", "contract_terms"]
    assert out["facts"]["terms"]["contract_id"] == "C-1"
    assert out["facts"]["rates"] == {"rows": []}


def test_tracking_table_rows_are_read_in_code_with_grader_quotes(monkeypatch, tmp_path):
    mapping = {"table_kind": "tracking", "sheet": 1, "header_row": 0,
               "columns": {"shipment": 0, "event": 1, "event_date": 2, "station": 3, "reason": 4,
                           "invoice_id": None, "invoice_date": None, "due_date": None, "amount": None,
                           "status": None, "paid_date": None},
               "date_format": None, "paid_status_words": [],
               "event_names": {"picked_up": "PICKED_UP", "arrived_facility": "ARRIVED_FACILITY",
                               "delivered": "DELIVERED", "collected_by_consignee": "COLLECTED_BY_CONSIGNEE"}}
    fake_calls(monkeypatch, {"classify": {"kind": "table", "reason": ""}, "table": mapping})
    out = facts.extract_doc(docs_by_ref()["batch_01/0005.eml#tracking-2031-07-01.xlsx"], tmp_path)
    rows = [r for r in out["facts"]["tracking"] if r["shipment"] == "TE56915687" and r["event"] == "picked_up"]
    assert rows == [{"shipment": "TE56915687", "event": "picked_up", "date": "2031-12-25", "station": "USE2",
                     "reason": "-", "quote": "TE56915687 | PICKED_UP | 2031-12-25 | USE2 | -", "page": 1,
                     "quote_ok": True}]
