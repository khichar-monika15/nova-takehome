"""Late fees: a fee billed that is not owed, and an unpaid invoice that will start costing a fee within 14 days."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .. import terms
from ..money import ceil_div, cents, parse_date
from ..world import Contract, Invoice, World, dec, ev, norm_id
from . import Candidate, dedupe, to_usd

RISK_DAYS = 14


def _due(w: World, key: str, c: Contract | None, printed: date | None) -> tuple[date | None, list[dict | None]]:
    """The due date (printed, else from the ledger), moved by an extension from the contract's payment_terms
    person, and its evidence."""
    due = printed
    led = w.ledger.get(key)
    if due is None and led:
        due = parse_date(led[1].get("due_date"))
    evidence: list[dict | None] = []
    for mail in w.emails:
        for x in mail.facts.get("extensions", []):
            if norm_id(x.get("invoice_id", "")) != key or c is None:
                continue
            if not terms.authorised(w, c, mail.sender_email, mail.sender_name, "payment_terms",
                                    mail.received_at.date()):
                continue
            new = parse_date(x.get("new_due_date"))
            if new:
                due = new
                evidence = [ev(mail, x), terms.rule_evidence(c, "extension_of_due_date")]
    return due, evidence


def _fees(principal: Decimal, months: int, rate: Decimal, compounding: bool) -> Decimal:
    total, base = Decimal(0), principal
    for _ in range(months):
        fee = cents(rate / 100 * base)
        total += fee
        if compounding:
            base += fee
    return total


def _late_terms(c: Contract | None):
    lf = (c.terms.get("late_fee") if c else None) or {}
    return dec(lf.get("rate_pct")), int(dec(lf.get("grace_days")) or 0), bool(lf.get("compounding")), lf


def _fee_lines(w: World):
    for copies in w.invoices.values():
        inv = copies[0]
        for ln in inv.lines:
            if ln.kind == "late_fee" and ln.refers_to_invoice:
                yield inv, ln


def _not_owed(w: World) -> list[Candidate]:
    by_target: dict[str, list] = {}
    for inv, ln in _fee_lines(w):
        by_target.setdefault(norm_id(ln.refers_to_invoice), []).append((inv, ln))
    out = {}
    for target_key, rows in by_target.items():
        target = w.latest_invoice(target_key)
        contract = target.contract if target and target.contract else rows[0][0].contract
        if contract is None:
            continue
        rate, grace, compounding, lf = _late_terms(contract)
        due, due_ev = _due(w, target_key, contract, target.due if target else None)
        led = w.ledger.get(target_key)
        if rate is None or due is None or led is None:
            continue
        paid = parse_date(led[1].get("paid_date"))
        rows.sort(key=lambda r: (r[0].date or date.min, r[0].doc.received_at))
        end = paid or rows[-1][0].date
        if end is None:
            continue
        days_late = (end - due).days
        principal = dec(led[1].get("amount")) or (target.total if target else None)
        owed = Decimal(0) if days_late <= grace or principal is None else \
            _fees(principal, ceil_div(days_late, 30), rate, compounding)
        billed_before = Decimal(0)
        for inv, ln in rows:
            remaining = max(owed - billed_before, Decimal(0))
            billed_before += ln.amount
            excess = ln.amount - remaining
            if excess <= 0:
                continue
            found = out.setdefault(inv.key, {"inv": inv, "native": Decimal(0), "evidence": [], "contract": contract,
                                             "refs": [inv.doc.ref, led[0].ref]})
            found["native"] += excess
            found["evidence"] += [ev(inv.doc, ln.item), *due_ev, ev(led[0], led[1]),
                                  ev(contract.msa, lf.get("clause")) if contract.msa else None]
    items = []
    for f in out.values():
        inv = f["inv"]
        usd, fx_ev, _ = to_usd(f["native"], inv)  # converted once per finding
        if usd is None:
            continue
        items.append(Candidate(cls="late_fee_not_owed", verdict="finding", invoice_id=inv.id,
                               contract_id=f["contract"].id, amount=usd, native=f["native"],
                               evidence=dedupe(f["evidence"] + fx_ev), deciding_refs=f["refs"],
                               features={"pickup_source": "invoice", "judgment": False,
                                         "inr": inv.currency != "USD"}))
    return items


def _unpaid(w: World, inv: Invoice) -> tuple[bool, list[dict | None]]:
    led = w.ledger.get(inv.key)
    if led:
        doc, row = led
        return (not row.get("paid") and "schedul" not in (row.get("status") or "").lower()), [ev(doc, row)]
    latest = max((d for d, _ in w.ledger.values()), key=lambda d: d.received_at, default=None)
    if latest is None or inv.doc.received_at > latest.received_at:
        return True, []
    return False, []


def _risk(w: World, disputed: dict[str, Decimal]) -> list[Candidate]:
    out = []
    for key, copies in w.invoices.items():
        inv = copies[0]
        if inv.contract is None:
            continue
        due, due_ev = _due(w, key, inv.contract, inv.due)
        if due is None or not (0 < (due - w.as_of).days <= RISK_DAYS):
            continue
        unpaid, led_ev = _unpaid(w, inv)
        rate, _, _, lf = _late_terms(inv.contract)
        if not unpaid or rate is None:
            continue
        led = w.ledger.get(key)
        open_amount = (dec(led[1].get("amount")) if led else None) or inv.total
        if open_amount is None:
            continue
        principal = open_amount - disputed.get(key, Decimal(0))
        usd, fx_ev, _ = to_usd(cents(rate / 100 * principal), inv)
        if usd is None:
            continue
        out.append(Candidate(cls="late_fee_risk", verdict="finding", invoice_id=inv.id,
                             contract_id=inv.contract.id, amount=usd, deadline=due,
                             evidence=dedupe([*led_ev, *inv.evidence(), *due_ev,
                                              ev(inv.contract.msa, lf.get("clause")) if inv.contract.msa else None,
                                              *fx_ev]),
                             deciding_refs=[inv.doc.ref],
                             features={"pickup_source": "invoice", "judgment": False, "inr": inv.currency != "USD"}))
    return out


def run(w: World, invoice_findings: list[Candidate]) -> list[Candidate]:
    disputed: dict[str, Decimal] = {}
    for c in invoice_findings:
        if c.verdict == "finding" and c.invoice_id and c.native is not None:
            k = norm_id(c.invoice_id)
            disputed[k] = disputed.get(k, Decimal(0)) + c.native
    return _not_owed(w) + _risk(w, disputed)
