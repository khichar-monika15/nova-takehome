"""Cashback: quarterly volume rebates and annual promised credits earned and not yet credited."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from ..money import cents, parse_date
from ..terms import fx_rate
from ..world import Contract, Invoice, World, dec, ev, norm_label
from . import Candidate, dedupe

FREIGHT_CODES = {"FRT", "FUEL", "SEC"}


def _quarter(d: date) -> tuple[int, int]:
    return d.year, (d.month - 1) // 3 + 1


def _quarter_end(y: int, q: int) -> date:
    return (date(y + (q == 4), 1 if q == 4 else 3 * q + 1, 1)) - timedelta(days=1)


def _qualifying(c: Contract, inv: Invoice) -> Decimal:
    allowed = FREIGHT_CODES | {a["code"] for a in c.tables.get("accessorials", [])}
    return sum((ln.amount for ln in inv.lines if ln.code in allowed), Decimal(0))


def _usd(c: Contract, inv: Invoice, amount: Decimal) -> Decimal | None:
    if inv.currency == "USD":
        return amount
    fx, _ = fx_rate(c, inv.date.strftime("%Y-%m"))
    return cents(amount / fx) if fx else None


def _spend(w: World, c: Contract, start: date, end: date) -> Decimal | None:
    total = Decimal(0)
    for copies in w.invoices.values():
        inv = copies[0]
        if inv.contract is not c or inv.date is None or not (start <= inv.date <= end):
            continue
        usd = _usd(c, inv, _qualifying(c, inv))
        if usd is None:
            return None
        total += usd
    for cn in w.credit_notes:
        ctype = cn.facts.get("credit", {}).get("credit_type")
        if cn.contract is not c or cn.date is None or not (start <= cn.date <= end) or ctype in (
                "rebate", "promised_credit", "margin_step_down"):
            continue
        usd = _usd(c, cn, abs(cn.total or Decimal(0)))
        total -= usd or Decimal(0)
    return total


def _credited(w: World, c: Contract, period: str, credit_type: str) -> Decimal:
    total = Decimal(0)
    for cn in w.credit_notes:
        cr = cn.facts.get("credit", {})
        if cn.contract is not c or cr.get("credit_type") != credit_type:
            continue
        if norm_label(period) not in norm_label(cr.get("period") or "") + " " + norm_label(
                " ".join(ln.label for ln in cn.lines)):
            continue
        total += abs(cn.total or Decimal(0)) if cn.currency == "USD" else (_usd(c, cn, abs(cn.total or 0)) or 0)
    return total


def _tier(tiers: list[dict], qs: Decimal) -> Decimal | None:
    pct = None
    for t in sorted(tiers, key=lambda t: dec(t["threshold"]) or 0):
        if qs >= (dec(t["threshold"]) or 0):
            pct = dec(t["pct"])
    return pct


def _item(c: Contract, period: str, credit_type: str, amount: Decimal, due: date, clause_ev) -> Candidate:
    return Candidate(cls="cashback", verdict="finding", contract_id=c.id, period=period, credit_type=credit_type,
                     amount=cents(amount), due=due,
                     evidence=dedupe([clause_ev, ev(c.msa, c.terms.get("qualifying_spend", {}).get("clause"))]),
                     deciding_refs=[c.msa.ref],
                     features={"pickup_source": "invoice", "judgment": False, "inr": False})


def _rebates(w: World, c: Contract) -> list[Candidate]:
    rb = c.terms.get("rebate") or {}
    if not rb.get("applies") or not rb.get("tiers"):
        return []
    start = parse_date(c.terms.get("effective_date")) or parse_date(c.terms.get("dated"))
    if start is None:
        return []
    out, (y, q) = [], _quarter(start)
    while _quarter_end(y, q) < w.as_of:
        q_start = date(y, 3 * q - 2, 1)
        qs = _spend(w, c, max(q_start, start), _quarter_end(y, q))
        pct = _tier(rb["tiers"], qs) if qs is not None else None
        if pct:
            period = f"{y}-Q{q}"
            owed = cents(qs * pct / 100) - _credited(w, c, period, "rebate")
            if owed > 0:
                due = _quarter_end(y, q) + timedelta(days=int(dec(rb.get("credit_due_days")) or 0))
                out.append(_item(c, period, "rebate", owed, due, ev(c.msa, rb.get("clause"))))
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def _promised(w: World, c: Contract) -> list[Candidate]:
    ic = c.terms.get("improvement_credit") or {}
    pct = dec(ic.get("pct"))
    start = parse_date(c.terms.get("effective_date"))
    if not ic.get("applies") or pct is None or start is None:
        return []
    out, n = [], 1
    while True:
        cy_start = start.replace(year=start.year + n - 1)
        cy_end = start.replace(year=start.year + n) - timedelta(days=1)
        if cy_end >= w.as_of:
            break
        qs = _spend(w, c, cy_start, cy_end)
        if qs is not None:
            period = f"CY{n}"
            owed = cents(qs * pct / 100) - _credited(w, c, period, "promised_credit")
            if owed > 0:
                due = cy_end + timedelta(days=1 + int(dec(ic.get("due_days_after_anniversary")) or 0))
                out.append(_item(c, period, "promised_credit", owed, due, ev(c.msa, ic.get("clause"))))
        n += 1
    return out


def run(w: World) -> list[Candidate]:
    out = []
    for c in w.contracts.values():
        if c.msa is not None:
            out += _rebates(w, c) + _promised(w, c)
    return out
