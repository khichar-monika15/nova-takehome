"""Stage 2a: link the stored facts of every document received by as_of into one view."""
from __future__ import annotations

import json
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .money import D, parse_date

PICKUP_RANK = ("tracking", "status_email", "awb", "invoice")


def norm_id(s: str) -> str:
    return re.sub(r"[\s#:]", "", s or "").upper()


def norm_label(s: str) -> str:
    return " ".join((s or "").lower().split())


_STATION = re.compile(r"[A-Z][A-Z0-9]{2,}")


def norm_lane(s: str | None) -> str | None:
    """'USTQM to INVKH', 'USTQM-INVKH' and 'USTQM INVKH' are one lane: ORIGIN-DESTINATION."""
    if not s:
        return None
    codes = _STATION.findall(s.upper().replace(" TO ", " "))
    return "-".join(codes[:2]) if len(codes) >= 2 else s.strip().upper()


def _norm_lanes(kind: str, facts: dict) -> None:
    """Rewrite every lane in a document's facts to ORIGIN-DESTINATION, so documents compare by station codes."""
    if kind == "contract":
        for row in facts.get("rates", {}).get("rows", []):
            row["lane"] = norm_lane(row.get("lane"))
        for ch in facts.get("terms", {}).get("amendment_changes", []):
            ch["lanes"] = [norm_lane(x) for x in ch.get("lanes", [])]
    elif kind == "email":
        for n in facts.get("rate_notices", []):
            n["lane"] = norm_lane(n.get("lane"))
    elif kind == "invoice":
        for ln in facts.get("lines", []):
            ln["lane"] = norm_lane(ln.get("lane"))


def dec(x) -> Decimal | None:
    if x in (None, ""):
        return None
    try:
        return D(x)
    except (ValueError, InvalidOperation):
        return None


@dataclass
class Doc:
    ref: str
    kind: str
    facts: dict
    received_at: datetime
    sender_name: str
    sender_email: str
    pages: list[str]
    is_scan: bool
    email_ref: str

    @classmethod
    def of(cls, r: dict) -> Doc:
        facts = json.loads(json.dumps(r.get("facts") or {}))
        _norm_lanes(r.get("kind") or "other", facts)
        return cls(ref=r["ref"], kind=r.get("kind") or "other", facts=facts,
                   received_at=datetime.fromisoformat(r["received_at"]), sender_name=r.get("sender_name", ""),
                   sender_email=(r.get("sender_email") or "").lower(), pages=r.get("pages", []),
                   is_scan=r.get("is_scan", False), email_ref=r.get("email_ref", r["ref"].split("#")[0]))


def ev(doc: Doc, item: dict | None) -> dict | None:
    """Evidence entry for a fact that carries a quote, or None when the quote was not found on its page."""
    if not item or not item.get("quote_ok") or not isinstance(item.get("page"), int):
        return None
    return {"doc": doc.ref, "page": item["page"], "quote": item["quote"]}


@dataclass
class Pickup:
    date: date
    source: str
    evidence: dict | None


@dataclass
class Shipment:
    id: str
    pickup: Pickup | None = None
    events: list[dict] = field(default_factory=list)
    awb: tuple[Doc, dict] | None = None
    dgd: tuple[Doc, dict] | None = None
    holds: list[tuple[Doc, dict]] = field(default_factory=list)

    def offer_pickup(self, d: date | None, source: str, evidence: dict | None) -> None:
        if d is None:
            return
        if self.pickup is None or PICKUP_RANK.index(source) < PICKUP_RANK.index(self.pickup.source):
            self.pickup = Pickup(d, source, evidence)

    def first_event(self, *names: str) -> dict | None:
        hits = [e for e in self.events if e["event"] in names and e["date"]]
        return min(hits, key=lambda e: e["date"]) if hits else None


@dataclass
class Contract:
    id: str
    msa: Doc | None = None
    amendments: list[Doc] = field(default_factory=list)
    notices: list[tuple[Doc, dict]] = field(default_factory=list)

    @property
    def terms(self) -> dict:
        return self.msa.facts.get("terms", {}) if self.msa else {}

    @property
    def rates(self) -> dict:
        return self.msa.facts.get("rates", {}) if self.msa else {}

    @property
    def tables(self) -> dict:
        return self.msa.facts.get("tables", {}) if self.msa else {}

    @property
    def schedule1(self) -> list[dict]:
        rows = list(self.terms.get("schedule1") or [])
        for a in self.amendments:
            rows += a.facts.get("terms", {}).get("schedule1") or []
        return rows

    def schedule1_doc(self) -> Doc | None:
        return self.msa

    def lanes(self) -> set[str]:
        """Every lane that some rate source of this contract prices."""
        found = {r["lane"] for r in self.rates.get("rows", [])}
        for a in self.amendments:
            found |= {r["lane"] for r in a.facts.get("rates", {}).get("rows", [])}
            for ch in a.facts.get("terms", {}).get("amendment_changes", []):
                found |= set(ch.get("lanes", []))
        return found | {n.get("lane") for _, n in self.notices}

    def aliases(self) -> dict[str, str]:
        out = {}
        for a in self.tables.get("aliases", []):
            for label in a.get("labels", []):
                out[norm_label(label)] = a["code"]
        for a in self.tables.get("accessorials", []):
            out.setdefault(norm_label(a["name"]), a["code"])
        return out

    def kinds(self) -> dict[str, str]:
        out = {}
        for row in self.tables.get("aliases", []) + self.tables.get("accessorials", []):
            if row.get("kind"):
                out.setdefault(row["code"], row["kind"])
        return out

    def accessorial(self, code: str) -> dict | None:
        return next((a for a in self.tables.get("accessorials", []) if a["code"] == code), None)


def charge_code(contract: Contract | None, label: str) -> str | None:
    if contract is None:
        return None
    table = contract.aliases()
    n = norm_label(label)
    if n in table:
        return table[n]
    starts = [k for k in table if n.startswith((k + " ", k + ":"))]
    return table[max(starts, key=len)] if starts else None


@dataclass
class Line:
    idx: int
    shipment: str | None
    pickup_printed: date | None
    label: str
    code: str | None
    lane: str | None
    qty: Decimal | None
    unit: str
    rate: Decimal | None
    amount: Decimal
    refers_to_invoice: str | None
    refers_to_period: str | None
    item: dict
    kind: str | None = None

    @property
    def group(self) -> str:
        return self.code or norm_label(self.label)


@dataclass
class Invoice:
    id: str
    key: str
    doc: Doc
    facts: dict
    contract: Contract | None
    date: date | None
    due: date | None
    currency: str
    total: Decimal | None
    doc_type: str
    lines: list[Line]

    def evidence(self) -> list[dict]:
        e = ev(self.doc, self.facts.get("invoice_id_quote"))
        return [e] if e else []


@dataclass
class World:
    as_of: date
    docs: list[Doc]
    contracts: dict[str, Contract]
    invoices: dict[str, list[Invoice]]
    credit_notes: list[Invoice]
    shipments: dict[str, Shipment]
    ledger: dict[str, tuple[Doc, dict]]
    emails: list[Doc]
    feedback: list[dict] = field(default_factory=list)

    def shipment(self, sid: str) -> Shipment:
        return self.shipments.setdefault(sid, Shipment(sid))

    def latest_invoice(self, key: str) -> Invoice | None:
        copies = self.invoices.get(key)
        return copies[-1] if copies else None


def _contract_for(w: World, cid: str | None, create: bool = False) -> Contract | None:
    if not cid:
        return None
    key = cid.strip().upper()
    if key not in w.contracts and create:
        w.contracts[key] = Contract(key)
    return w.contracts.get(key)


def _add_contract(w: World, d: Doc) -> None:
    t = d.facts.get("terms", {})
    if t.get("doc_type") == "msa" or (t and t.get("doc_type") not in ("amendment", "extension")):
        c = _contract_for(w, t.get("contract_id"), create=True)
        unsigned_held = c and c.msa and not c.msa.facts.get("terms", {}).get("signed_by_both", True)
        if c and (c.msa is None or (unsigned_held and t.get("signed_by_both", True))):
            c.msa = d
        return
    for cid in (t.get("parent_contract_id"), t.get("contract_id")):
        c = _contract_for(w, cid)
        if c:
            c.amendments.append(d)
            return
    c = _contract_for(w, t.get("parent_contract_id") or t.get("contract_id"), create=True)
    if c:
        c.amendments.append(d)


def _invoice_contract(w: World, d: Doc, f: dict) -> Contract | None:
    c = _contract_for(w, f.get("contract_id"))
    if c:
        return c
    cover = next((e for e in w.emails if e.ref == d.email_ref), None)
    if cover:
        c = _contract_for(w, cover.facts.get("contract_id"))
        if c:
            return c
    same_cur = [c for c in w.contracts.values() if c.terms.get("currency") == f.get("currency")]
    if len(same_cur) == 1:
        return same_cur[0]
    return next(iter(w.contracts.values())) if len(w.contracts) == 1 else None


def _lines(contract: Contract | None, f: dict) -> list[Line]:
    out = []
    for i, x in enumerate(f.get("lines", [])):
        amount = dec(x.get("amount"))
        if amount is None:
            continue
        code = charge_code(contract, x.get("label", ""))
        kinds = contract.kinds() if contract else {}
        kind = kinds.get(code) if code else None
        if kind is None and x.get("kind") not in (None, "", "other", "none"):
            kind = x["kind"]
            code = code or next((k for k, v in kinds.items() if v == kind), None)
        out.append(Line(idx=i, shipment=(x.get("shipment") or None), pickup_printed=parse_date(x.get("pickup_date")),
                        label=x.get("label", ""), code=code, kind=kind,
                        lane=x.get("lane") or None, qty=dec(x.get("qty")), unit=x.get("unit", "other"),
                        rate=dec(x.get("rate")), amount=amount, refers_to_invoice=x.get("refers_to_invoice"),
                        refers_to_period=x.get("refers_to_period"), item=x))
    return out


def _add_invoice(w: World, d: Doc) -> None:
    f = d.facts
    if not f.get("invoice_id"):
        return
    contract = _invoice_contract(w, d, f)
    inv = Invoice(id=f["invoice_id"], key=norm_id(f["invoice_id"]), doc=d, facts=f, contract=contract,
                  date=parse_date(f.get("invoice_date")), due=parse_date(f.get("due_date")),
                  currency=(f.get("currency") or "USD").upper(), total=dec(f.get("total")),
                  doc_type=f.get("doc_type", "invoice"), lines=_lines(contract, f))
    if inv.doc_type == "credit_note":
        w.credit_notes.append(inv)
        return
    w.invoices.setdefault(inv.key, []).append(inv)
    for ln in inv.lines:
        if ln.shipment:
            w.shipment(ln.shipment).offer_pickup(ln.pickup_printed, "invoice", ev(d, ln.item))


def _add_email(w: World, d: Doc) -> None:
    w.emails.append(d)
    f = d.facts
    for s in f.get("statuses", []):
        sh = w.shipment(s["shipment"])
        day = parse_date(s.get("date"))
        sh.events.append({"event": s["event"], "date": day, "station": s.get("station"), "evidence": ev(d, s),
                          "source": "status_email"})
        if s["event"] == "picked_up":
            sh.offer_pickup(day, "status_email", ev(d, s))
    for h in f.get("customs_holds", []):
        w.shipment(h["shipment"]).holds.append((d, h))
    for n in f.get("rate_notices", []):
        c = _contract_for(w, n.get("contract_id")) or next(
            (c for c in w.contracts.values() if n.get("lane") in c.lanes()), None)
        if c is None and len(w.contracts) == 1:
            c = next(iter(w.contracts.values()))
        if c:
            c.notices.append((d, n))


def _add_table(w: World, d: Doc) -> None:
    f = d.facts
    for r in f.get("tracking", []):
        sh = w.shipment(r["shipment"])
        day = parse_date(r.get("date"))
        sh.events.append({"event": r["event"], "date": day, "station": r.get("station"), "reason": r.get("reason"),
                          "evidence": ev(d, r), "source": "tracking"})
        if r["event"] == "picked_up":
            sh.offer_pickup(day, "tracking", ev(d, r))
    if f.get("ledger") is not None:
        for r in f["ledger"]:
            w.ledger[norm_id(r["invoice_id"])] = (d, r)


def _add_awb(w: World, d: Doc) -> None:
    f = d.facts
    if not f.get("shipment"):
        return
    sh = w.shipment(f["shipment"])
    sh.awb = (d, f)
    sh.offer_pickup(parse_date(f.get("executed_date")), "awb", ev(d, f))


def _add_dgd(w: World, d: Doc) -> None:
    f = d.facts
    if f.get("shipment"):
        w.shipment(f["shipment"]).dgd = (d, f)


ORDER = ("contract", "email", "table", "awb", "dgd", "invoice")


def _docs(records: list[dict]) -> list[Doc]:
    out = []
    for r in records:
        if not r.get("ok"):
            continue
        try:
            out.append(Doc.of(r))
        except Exception:  # noqa: BLE001  one document with odd facts must not empty the report
            print(f"world: skipped {r.get('ref')}:\n{traceback.format_exc()}", file=sys.stderr)
    return out


def build(records: list[dict], as_of: date, feedback: list[dict] | None = None) -> World:
    docs = sorted(_docs(records), key=lambda d: (d.received_at, d.ref))
    w = World(as_of=as_of, docs=docs, contracts={}, invoices={}, credit_notes=[], shipments={}, ledger={},
              emails=[], feedback=feedback or [])
    add = {"contract": _add_contract, "email": _add_email, "table": _add_table, "awb": _add_awb, "dgd": _add_dgd,
           "invoice": _add_invoice}
    for kind in ORDER:
        for d in docs:
            if d.kind == kind:
                try:
                    add[kind](w, d)
                except Exception:  # noqa: BLE001  one document with odd facts must not empty the report
                    print(f"world: skipped {d.ref}:\n{traceback.format_exc()}", file=sys.stderr)
    return w
