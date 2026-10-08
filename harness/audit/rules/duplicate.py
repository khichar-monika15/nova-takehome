"""Duplicate: the same shipment charge on two invoice numbers, or a paid invoice sent again for payment."""
from __future__ import annotations

from decimal import Decimal

from ..world import Invoice, World, ev, norm_id
from . import Candidate, dedupe, to_usd

SKIP_GROUPS = {"LATE", "TAX", "DUTY"}


def _line_key(ln) -> tuple | None:
    if ln.group in SKIP_GROUPS:
        return None
    if ln.shipment:
        return ("shipment", ln.shipment, ln.group, ln.amount)
    if ln.refers_to_period:
        return ("period", ln.refers_to_period, ln.group, ln.amount)
    return None


def _credited(w: World, inv: Invoice) -> Decimal:
    return sum((abs(cn.total or Decimal(0)) for cn in w.credit_notes
                if norm_id(cn.facts.get("credit", {}).get("credits_invoice") or "") == inv.key), Decimal(0))


def _order(inv: Invoice):
    return (inv.date or inv.doc.received_at.date(), inv.doc.received_at)


def _cross_invoice(w: World) -> dict[str, Candidate]:
    first_seen: dict[tuple, tuple[Invoice, object]] = {}
    hits: dict[str, list] = {}
    for inv in sorted((c[0] for c in w.invoices.values()), key=_order):
        for ln in inv.lines:
            k = _line_key(ln)
            if k is None:
                continue
            if k in first_seen and first_seen[k][0].key != inv.key:
                hits.setdefault(inv.key, []).append((inv, ln, first_seen[k]))
            else:
                first_seen.setdefault(k, (inv, ln))
    out = {}
    for key, rows in hits.items():
        inv = rows[0][0]
        amount = sum((ln.amount for _, ln, _ in rows), Decimal(0)) - _credited(w, inv)
        if amount <= 0:
            continue
        usd, fx_ev, _ = to_usd(amount, inv)
        if usd is None:
            continue
        evidence = [ev(inv.doc, ln.item) for _, ln, _ in rows] + [ev(i0.doc, l0.item) for _, _, (i0, l0) in rows]
        out[key] = Candidate(cls="duplicate", verdict="finding", invoice_id=inv.id,
                             contract_id=inv.contract.id if inv.contract else None, amount=usd, native=amount,
                             evidence=dedupe(evidence + fx_ev), deciding_refs=[inv.doc.ref],
                             features={"pickup_source": "invoice", "judgment": False, "inr": inv.currency != "USD"})
    return out


def _resend_request(w: World, inv: Invoice):
    cover = next((e for e in w.emails if e.ref == inv.doc.email_ref), None)
    if not cover:
        return None
    for r in cover.facts.get("invoice_refs", []):
        if norm_id(r.get("invoice_id", "")) == inv.key and r.get("asks_payment") and not r.get(
                "marked_copy_or_reminder"):
            return cover, r
    return None


def _resent_after_payment(w: World) -> dict[str, Candidate]:
    out = {}
    for key, copies in w.invoices.items():
        if len(copies) < 2 or key not in w.ledger:
            continue
        led_doc, row = w.ledger[key]
        status = (row.get("status") or "").lower()
        if not (row.get("paid") or "schedul" in status):
            continue
        for again in copies[1:]:
            if again.facts.get("marked_copy_or_reminder"):
                continue
            ask = _resend_request(w, again)
            if not ask or again.total is None:
                continue
            usd, fx_ev, _ = to_usd(again.total, again)
            if usd is None:
                continue
            cover, ref = ask
            out[key] = Candidate(cls="duplicate", verdict="finding", invoice_id=again.id,
                                 contract_id=again.contract.id if again.contract else None, amount=usd,
                                 native=again.total,
                                 evidence=dedupe([ev(cover, ref), ev(led_doc, row), *again.evidence(),
                                                  *copies[0].evidence(), *fx_ev]),
                                 deciding_refs=[cover.ref, led_doc.ref],
                                 features={"pickup_source": "invoice", "judgment": True,
                                           "inr": again.currency != "USD"})
            break
    return out


def run(w: World) -> list[Candidate]:
    found = _cross_invoice(w)
    found.update(_resent_after_payment(w))
    return list(found.values())
