"""Rules turn the world view into candidate items, one per finding key."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ..money import cents
from ..terms import fx_rate
from ..world import Contract, Invoice

OUTBOUND = {"overcharge", "duplicate", "waived_but_billed", "late_fee_not_owed", "cashback"}


@dataclass
class Candidate:
    cls: str
    verdict: str
    invoice_id: str | None = None
    contract_id: str | None = None
    period: str | None = None
    credit_type: str | None = None
    amount: Decimal | None = None
    amount_range: tuple[Decimal, Decimal] | None = None
    deadline: date | None = None
    evidence: list[dict] = field(default_factory=list)
    missing_doc: dict | None = None
    learned_at: dict | None = None
    features: dict = field(default_factory=dict)
    deciding_refs: list[str] = field(default_factory=list)
    due: date | None = None

    @property
    def key(self) -> tuple:
        if self.cls == "cashback":
            return (self.cls, self.contract_id, self.period, self.credit_type)
        if self.cls == "expiry":
            return (self.cls, self.contract_id)
        return (self.cls, (self.invoice_id or "").upper())


def dedupe(evidence: list[dict | None]) -> list[dict]:
    out, seen = [], set()
    for e in evidence:
        if e and (e["doc"], e["page"], e["quote"]) not in seen:
            seen.add((e["doc"], e["page"], e["quote"]))
            out.append(e)
    return out


def to_usd(amount: Decimal, inv: Invoice) -> tuple[Decimal | None, list[dict], dict | None]:
    """-> (USD amount, FX evidence, missing Annex F row) for one finding, converting once."""
    if inv.currency == "USD":
        return cents(amount), [], None
    c: Contract | None = inv.contract
    month = inv.date.strftime("%Y-%m") if inv.date else None
    fx, evidence = fx_rate(c, month) if c and month else (None, [])
    if not fx:
        from ..terms import contact
        holder = (contact(c, "treasury") if c else None) or {"party": "carrier"}
        return None, [], {"name": "Annex F update", "holder": holder}
    return cents(amount / fx), evidence, None
