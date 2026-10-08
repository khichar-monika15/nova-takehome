from datetime import datetime, timezone
from pathlib import Path

from audit.docs import read_batch
from extract import Mailbox

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "data/examples/overcharge/docs"


def test_read_batch_lists_emails_and_attachments_with_refs():
    docs = read_batch(EXAMPLE / "batch_01")
    refs = [d.ref for d in docs]
    assert "batch_01/0003.eml" in refs
    assert "batch_01/0003.eml#TX-US-2032-5394.pdf" in refs
    assert "batch_01/0005.eml#tracking-2031-07-01.xlsx" in refs


def test_doc_fields_come_from_the_email():
    docs = {d.ref: d for d in read_batch(EXAMPLE / "batch_01")}
    inv = docs["batch_01/0003.eml#TX-US-2032-5394.pdf"]
    assert inv.received_at.date() == datetime(2032, 1, 3, tzinfo=timezone.utc).date()
    assert inv.email_ref == "batch_01/0003.eml"
    assert inv.kind_hint == "pdf"
    assert not inv.is_scan
    assert "TE56915687" in inv.pages[0]


def test_every_ref_resolves_in_the_grader_mailbox():
    mb = Mailbox(EXAMPLE)
    for d in read_batch(EXAMPLE / "batch_01"):
        pages, _ = mb.pages(d.ref)
        assert pages == d.pages
