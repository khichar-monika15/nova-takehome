from datetime import date
from pathlib import Path

from audit import ingest, state

REPO = Path(__file__).resolve().parents[2]
OVER = REPO / "data/examples/overcharge/docs/batch_01"


def fake_extract(monkeypatch, fail=()):
    calls = []

    def run(doc, state_dir, deadline=None):
        calls.append(doc.ref)
        if doc.ref in fail:
            return {"kind": "invoice", "facts": {}, "ok": False}
        return {"kind": "email" if doc.kind_hint == "email" else "invoice", "facts": {"n": 1}, "ok": True}

    monkeypatch.setattr(ingest, "extract_doc", run)
    return calls


def test_ingest_stores_one_file_per_document(monkeypatch, tmp_path):
    calls = fake_extract(monkeypatch)
    ingest.ingest(OVER, tmp_path)
    assert len(calls) == 8
    docs = state.load_docs(tmp_path, date(2032, 8, 31))
    assert {d["ref"] for d in docs} == set(calls)
    inv = next(d for d in docs if d["ref"].endswith("TX-US-2032-5394.pdf"))
    assert inv["kind"] == "invoice" and inv["ok"] and inv["pages"][0].startswith("Tarrowby")


def test_second_ingest_makes_no_new_calls(monkeypatch, tmp_path):
    calls = fake_extract(monkeypatch)
    ingest.ingest(OVER, tmp_path)
    ingest.ingest(OVER, tmp_path)
    assert len(calls) == 8


def test_failed_docs_are_retried_later(monkeypatch, tmp_path):
    bad = "batch_01/0003.eml#TX-US-2032-5394.pdf"
    fake_extract(monkeypatch, fail={bad})
    ingest.ingest(OVER, tmp_path)
    fake_extract(monkeypatch)
    retried = ingest.retry_failed(tmp_path)
    assert retried == [bad]
    assert all(d["ok"] for d in state.load_docs(tmp_path, date(2032, 8, 31)))


def test_load_docs_respects_as_of(monkeypatch, tmp_path):
    fake_extract(monkeypatch)
    ingest.ingest(OVER, tmp_path)
    early = {d["ref"] for d in state.load_docs(tmp_path, date(2032, 1, 3))}
    assert "batch_01/0003.eml" in early
    assert "batch_01/0004.eml" not in early
