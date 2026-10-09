"""Stage 1: turn one document into typed facts with quotes the grader can find."""
from __future__ import annotations

import base64
import io
import time
from pathlib import Path

from . import prompts, schemas
from .docs import Doc, gx, page_png
from .llm import FALLBACK_MODEL, MODEL, call_json, run_parallel
from .money import parse_date
from .quotes import locate

MODEL_FOR = {
    "classify": FALLBACK_MODEL,
    "email": MODEL,
    "contract_terms": MODEL,
    "contract_rates": MODEL,
    "contract_tables": MODEL,
    "invoice": MODEL,
    "awb": FALLBACK_MODEL,
    "dgd": FALLBACK_MODEL,
    "table": FALLBACK_MODEL,
}
CLASSIFY_CHARS = 2500
PREVIEW_ROWS = 8


def _text_block(doc: Doc, limit: int | None = None) -> dict:
    text = "\n".join(f"=== page {i} ===\n{p}" for i, p in enumerate(doc.pages, 1))
    head = f"Document: {doc.name}\nReceived: {doc.received_at:%Y-%m-%d}\n\n"
    return {"type": "text", "text": head + (text[:limit] if limit else text)}


def _image_blocks(doc: Doc) -> list[dict]:
    blocks = []
    for i in range(1, len(doc.pages) + 1):
        png = base64.standard_b64encode(page_png(doc.data, i)).decode()
        blocks.append({"type": "text", "text": f"=== page {i} === (scanned image, no text layer)"})
        blocks.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": png}})
    return blocks


def _content(doc: Doc, task: str, limit: int | None = None) -> list[dict]:
    body = _image_blocks(doc) if doc.is_scan else [_text_block(doc, limit)]
    return body + [{"type": "text", "text": prompts.TASK[task]}]


def _call(task: str, doc: Doc, state_dir: Path, limit: int | None = None, deadline: float | None = None):
    return call_json(task, prompts.SYSTEM, _content(doc, task, limit), schemas.ALL[task], state_dir=state_dir,
                     model=MODEL_FOR[task], deadline=deadline)


def _repair_quotes(node, doc: Doc) -> None:
    """Walk the facts; every object with quote/page gets the page text's own wording and a quote_ok flag."""
    if isinstance(node, list):
        for x in node:
            _repair_quotes(x, doc)
        return
    if not isinstance(node, dict):
        return
    if isinstance(node.get("quote"), str) and isinstance(node.get("page"), int):
        if doc.is_scan:
            node["quote_ok"] = 1 <= node["page"] <= len(doc.pages)
        else:
            hit = locate(doc.pages, node["page"], node["quote"])
            node["quote_ok"] = hit is not None
            if hit:
                node["page"], node["quote"] = hit
    for v in node.values():
        if isinstance(v, (dict, list)):
            _repair_quotes(v, doc)


def classify(doc: Doc, state_dir: Path, deadline: float | None = None) -> str | None:
    """-> the document kind, or None when the call failed (the document is then retried later)."""
    if doc.kind_hint == "email":
        return "email"
    out = _call("classify", doc, state_dir, CLASSIFY_CHARS, deadline)
    return out["kind"] if out else None


# ---- spreadsheets: the model maps the columns, code reads every row ---------------------------------------------------
def _sheet_rows(data: bytes):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    return [[[gx._cell_text(c) for c in row] for row in ws.iter_rows()] for ws in wb.worksheets]


def _row_text(cells: list[str]) -> str:
    return gx.SEP.join(t for t in cells if t != "")


def _table_preview(sheets) -> str:
    out = []
    for s, rows in enumerate(sheets, 1):
        out.append(f"=== sheet {s} ===")
        for r, cells in enumerate(rows[:PREVIEW_ROWS]):
            out.append(f"row {r}: {_row_text(cells)}")
            out.append(f"   cells by column: {dict(enumerate(cells))}")
    return "\n".join(out)


def _cell(cells, idx):
    return cells[idx] if idx is not None and 0 <= idx < len(cells) else ""


def _table_facts(doc: Doc, state_dir: Path, deadline: float | None = None) -> dict | None:
    sheets = _sheet_rows(doc.data)
    content = [{"type": "text", "text": f"Spreadsheet: {doc.name}\n{_table_preview(sheets)}"},
               {"type": "text", "text": prompts.TASK["table"]}]
    m = call_json("table", prompts.SYSTEM, content, schemas.TABLE, state_dir=state_dir, model=MODEL_FOR["table"],
                  deadline=deadline)
    if not m:
        return None
    sheet_no = m["sheet"] if 1 <= m["sheet"] <= len(sheets) else 1
    rows = sheets[sheet_no - 1][m["header_row"] + 1:]
    col, fmt_ = m["columns"], m["date_format"]

    def day(cells, key):
        d = parse_date(_cell(cells, col.get(key)), fmt_) or parse_date(_cell(cells, col.get(key)))
        return d.isoformat() if d else None

    out: dict = {"table_kind": m["table_kind"], "mapping": m}
    if m["table_kind"] == "tracking":
        names = {v: k for k, v in m["event_names"].items() if v}
        out["tracking"] = [
            {"shipment": _cell(c, col["shipment"]), "event": names.get(_cell(c, col["event"]), "other"),
             "date": day(c, "event_date"), "station": _cell(c, col["station"]), "reason": _cell(c, col["reason"]),
             "quote": _row_text(c), "page": sheet_no, "quote_ok": True}
            for c in rows if _cell(c, col["shipment"])]
    elif m["table_kind"] == "payment_ledger":
        paid_words = {w.lower() for w in m["paid_status_words"]}
        out["ledger"] = [
            {"invoice_id": _cell(c, col["invoice_id"]), "invoice_date": day(c, "invoice_date"),
             "due_date": day(c, "due_date"), "amount": _cell(c, col["amount"]), "status": _cell(c, col["status"]),
             "paid": _cell(c, col["status"]).lower() in paid_words or bool(day(c, "paid_date")),
             "paid_date": day(c, "paid_date"), "quote": _row_text(c), "page": sheet_no, "quote_ok": True}
            for c in rows if _cell(c, col["invoice_id"])]
    return out


# ---- one document -----------------------------------------------------------------------------------------------------
def extract_doc(doc: Doc, state_dir: Path, deadline: float | None = None) -> dict:
    """-> {"kind": ..., "facts": {...}, "ok": bool}. No model call starts once the deadline is too close."""
    records = None
    if doc.kind_hint == "xlsx":  # records decide many keys, so a spreadsheet is mapped first, not classified
        records = _table_facts(doc, state_dir, deadline)
        if records is None:
            return {"kind": None, "facts": {}, "ok": False}
        if records.get("table_kind") in ("tracking", "payment_ledger"):
            _repair_quotes(records, doc)
            return {"kind": "table", "facts": records, "ok": True}
    kind = classify(doc, state_dir, deadline)
    if kind is None:
        return {"kind": None, "facts": {}, "ok": False}
    if kind == "email":
        f = _call("email", doc, state_dir, None, deadline)
    elif kind == "contract":
        parts = ("contract_terms", "contract_rates", "contract_tables")
        got = run_parallel([lambda t=t: _call(t, doc, state_dir, None, deadline) for t in parts], workers=3,
                           deadline=deadline or time.monotonic() + 600)
        f = None if any(g is None for g in got) else dict(zip(("terms", "rates", "tables"), got))
    elif kind == "table":
        f = records if records is not None else _table_facts(doc, state_dir, deadline)
    elif kind in ("invoice", "awb", "dgd"):
        f = _call(kind, doc, state_dir, None, deadline)
    else:
        f = {}
    if f is None:
        return {"kind": kind, "facts": {}, "ok": False}
    _repair_quotes(f, doc)
    return {"kind": kind, "facts": f, "ok": True}
