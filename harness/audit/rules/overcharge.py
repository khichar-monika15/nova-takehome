"""Overcharge: reprice every line of an invoice at the terms in force on its pickup date."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .. import terms
from ..money import cents
from ..world import Invoice, Line, Shipment, World, dec, ev
from . import Candidate, dedupe, to_usd

PER_SHIPMENT_CONDITIONS = {"DG": "dangerous_goods", "DRYICE": "dry_ice", "DLV": "delivery", "CUSTOMS": "customs"}
NOT_PRICED = {"LATE", "DUTY", "TAX", "COST", "MARGIN", "HDL"}


@dataclass
class Priced:
    diffs: list[tuple[Line, Decimal]] = field(default_factory=list)
    evidence: list[dict | None] = field(default_factory=list)
    conflicts: list[list[tuple[Decimal, list[dict]]]] = field(default_factory=list)
    missing: dict | None = None
    judgment: bool = False
    learned_at: dict | None = None


def _pickup(w: World, inv: Invoice, sid: str | None, lines: list[Line]):
    sh = w.shipments.get(sid) if sid else None
    if sh and sh.pickup:
        return sh.pickup.date, sh.pickup.source, sh.pickup.evidence
    printed = next((ln.pickup_printed for ln in lines if ln.pickup_printed), None)
    return (printed or inv.date), "invoice", None


def _freight_kg(lines: list[Line], sh: Shipment | None) -> Decimal | None:
    frt = next((ln for ln in lines if ln.code == "FRT" and ln.unit == "kg" and ln.qty), None)
    if frt:
        return frt.qty
    if sh and sh.awb:
        return dec(sh.awb[1].get("chargeable_kg"))
    return None


def _price_group(w: World, inv: Invoice, sid: str | None, lines: list[Line], pick: int | None) -> Priced:
    c = inv.contract
    out = Priced()
    pickup, _, pickup_ev = _pickup(w, inv, sid, lines)
    if pickup is None:
        return out
    sh = w.shipments.get(sid) if sid else None
    kg = _freight_kg(lines, sh)
    lane = next((ln.lane for ln in lines if ln.lane), None)
    correct_freight: Decimal | None = None

    def billed_wrong(ln: Line, correct: Decimal | None, *evidence):
        if correct is None:
            return
        if ln.amount - correct > 0:
            out.diffs.append((ln, ln.amount - correct))
            out.evidence.extend([ev(inv.doc, ln.item), *evidence])

    for ln in sorted(lines, key=lambda x: x.code != "FRT"):
        if ln.code == "FRT":
            if lane is None or kg is None:
                continue
            r = terms.rate(w, c, lane, kg, pickup)
            out.learned_at = out.learned_at or r.learned_at
            if r.missing_doc:
                out.missing = {**r.missing_doc, "evidence": r.evidence + [ev(inv.doc, ln.item)]}
                return out
            value = r.value
            if r.conflict:
                out.conflicts.append(r.conflict)
                out.evidence += [e for _, evs in r.conflict for e in evs]
                if pick is None:
                    continue
                value = r.conflict[pick][0]
            if value is None:
                continue
            correct = cents(value * kg)
            if r.minimum and correct < r.minimum:
                correct = r.minimum
            correct_freight = (correct_freight or Decimal(0)) + correct
            billed_wrong(ln, correct, *r.evidence)
        elif ln.code == "FUEL":
            pct, fuel_ev = terms.fuel_pct(c, pickup)
            if pct is None:
                continue
            base = correct_freight if correct_freight is not None else ln.qty
            if base is None:
                continue
            billed_wrong(ln, cents(pct / 100 * base), *fuel_ev, terms.rule_evidence(c, "fuel"))
        elif ln.code and ln.code not in NOT_PRICED:
            row, acc_ev = terms.accessorial(c, ln.code, pickup)
            if not row:
                continue
            correct = _accessorial(c, row, ln, kg, pickup, sh, out)
            rule = PER_SHIPMENT_CONDITIONS.get(ln.code) or ("storage" if row.get("basis") == "day" else None)
            billed_wrong(ln, correct, *acc_ev, terms.rule_evidence(c, rule) if rule else None, *_condition_ev(sh))
    if out.diffs:
        out.evidence.append(pickup_ev)
    return out


def _condition_ev(sh: Shipment | None) -> list[dict | None]:
    if not sh:
        return []
    found = [ev(sh.dgd[0], sh.dgd[1])] if sh.dgd else []
    found += [e["evidence"] for e in sh.events if e["event"] in ("collected_by_consignee", "arrived_facility",
                                                                  "delivered")]
    found += [ev(d, h) for d, h in sh.holds]
    return found


def _accessorial(c, row: dict, ln: Line, kg, pickup, sh: Shipment | None, out: Priced) -> Decimal | None:
    fee = dec(row.get("fee"))
    if fee is None:
        return None
    basis, code = row.get("basis"), ln.code
    if row.get("months") and pickup.month not in row["months"]:
        return Decimal("0.00")
    if basis == "kg":
        qty = ln.qty if ln.unit == "kg" and ln.qty else kg
        return cents(fee * qty) if qty is not None else None
    if basis == "month":
        return cents(fee * (ln.qty or 1))
    if basis == "day":
        days = _storage_days(c, sh)
        return cents(fee * days) if days is not None else cents(fee * (ln.qty or 1))
    if basis != "shipment":
        return None
    if code == "DG" and sh and sh.dgd:
        out.judgment = True
        f = sh.dgd[1]
        return Decimal("0.00") if f.get("dry_ice_refrigerant_only") and not f.get(
            "dangerous_goods_other_than_dry_ice") else fee
    if code == "DRYICE" and sh and sh.dgd:
        out.judgment = True
        return Decimal("0.00") if sh.dgd[1].get("dangerous_goods_other_than_dry_ice") else fee
    if code == "DLV" and sh and sh.events:
        out.judgment = True
        return Decimal("0.00") if sh.first_event("collected_by_consignee") else fee
    if code == "CUSTOMS" and sh and sh.holds:
        out.judgment = True
        return Decimal("0.00") if any(h.get("cause") == "carrier" for _, h in sh.holds) else fee
    return fee


def _storage_days(c, sh: Shipment | None) -> int | None:
    if not sh:
        return None
    arrived = sh.first_event("arrived_facility")
    released = sh.first_event("delivered", "collected_by_consignee")
    free = dec(c.terms.get("storage_free_days"))
    if not arrived or not released or free is None:
        return None
    return max(0, (released["date"] - arrived["date"]).days - int(free))


def _groups(inv: Invoice) -> dict[str | None, list[Line]]:
    groups: dict[str | None, list[Line]] = {}
    for ln in inv.lines:
        groups.setdefault(ln.shipment, []).append(ln)
    return groups


def _total(priced: list[Priced]) -> Decimal:
    return sum((d for p in priced for _, d in p.diffs), Decimal(0))


def audit_invoice(w: World, inv: Invoice) -> Candidate | None:
    groups = _groups(inv)
    priced = [_price_group(w, inv, sid, lines, None) for sid, lines in groups.items()]
    base = Candidate(cls="overcharge", verdict="finding", invoice_id=inv.id, contract_id=inv.contract.id)
    missing = next((p.missing for p in priced if p.missing), None)
    pickups = [w.shipments[s].pickup.source if s in w.shipments and w.shipments[s].pickup else "invoice"
               for s in groups if s]
    base.features = {"pickup_source": max(pickups, key=("tracking", "status_email", "awb", "invoice").index)
                     if pickups else "invoice",
                     "judgment": any(p.judgment for p in priced), "inr": inv.currency != "USD"}
    base.deciding_refs = [inv.doc.ref]
    if missing:
        base.verdict = "cannot_determine"
        base.missing_doc = {"name": missing["name"], "holder": missing["holder"]}
        base.evidence = dedupe(missing["evidence"] + inv.evidence())
        return base
    if any(p.conflicts for p in priced):
        totals = []
        for pick in (0, 1):
            alt = [_price_group(w, inv, sid, lines, pick) for sid, lines in groups.items()]
            usd, _, _ = to_usd(_total(alt), inv)
            totals.append(max(usd or Decimal(0), Decimal(0)))
        base.verdict = "conflict"
        base.amount_range = (cents(min(totals)), cents(max(totals)))
        base.evidence = dedupe([e for p in priced for e in p.evidence] + [ev(inv.doc, ln.item) for ln in inv.lines
                                                                          if ln.code == "FRT"])
        return base
    total = _total(priced)
    if total <= 0:
        return None
    usd, fx_ev, no_fx = to_usd(total, inv)
    if no_fx:
        base.verdict, base.missing_doc = "cannot_determine", no_fx
        base.evidence = dedupe([e for p in priced for e in p.evidence])
        return base
    base.amount, base.native = usd, total
    base.learned_at = next((p.learned_at for p in priced if p.learned_at), None)
    base.evidence = dedupe([e for p in priced for e in p.evidence] + fx_ev)
    return base


def run(w: World) -> list[Candidate]:
    out = []
    for copies in w.invoices.values():
        inv = copies[0]
        if inv.contract is None or inv.contract.msa is None:
            continue
        cand = audit_invoice(w, inv)
        if cand:
            out.append(cand)
    return out
