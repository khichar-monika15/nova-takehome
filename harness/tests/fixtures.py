"""Small fact records in the shape facts.extract_doc stores them."""


def rec(ref, kind, facts, received="2032-01-03T10:00:00+00:00", sender=("Billing", "billing@carrier.example"),
        pages=("",)):
    return {"ref": ref, "email_ref": ref.split("#")[0], "name": ref.split("#")[-1], "kind": kind, "facts": facts,
            "ok": True, "received_at": received, "sender_name": sender[0], "sender_email": sender[1],
            "subject": "", "pages": list(pages), "is_scan": False}


def clause(q="clause text long enough", page=3):
    return {"quote": q, "page": page, "quote_ok": True}


def msa(cid="C-1", received="2031-11-25T09:00:00+00:00", **over):
    terms = {"doc_type": "msa", "contract_id": cid, "amendment_ref": None, "parent_contract_id": None,
             "signed_by_both": True, "dated": "2031-11-20", "effective_date": "2031-12-01", "end_date": "2032-11-30",
             "term": clause(), "auto_renews": False, "renewal_term_months": None, "non_renewal_notice_days": None,
             "renewal": None, "currency": "USD",
             "parties": {"shipper_name": "Shipper Inc.", "shipper_code": "SHP-US", "carrier_name": "Carrier Inc.",
                         "carrier_code": "CAR-US"},
             "payment_days": "45", "payment": clause(),
             "late_fee": {"rate_pct": "1.98", "grace_days": "0", "compounding": True, "clause": clause()},
             "rebate": {"applies": False, "tiers": [], "threshold_currency": "USD", "period": "quarter",
                        "credit_due_days": "45", "clause": None},
             "improvement_credit": {"applies": False, "pct": None, "due_days_after_anniversary": None, "clause": None},
             "margin_step_down": {"applies": False, "base_margin_pct": None, "stepped_margin_pct": None,
                                  "threshold": None, "threshold_basis": None, "clause": None},
             "qualifying_spend": {"includes": [], "excludes": [], "net_of_credit_notes": True,
                                  "inr_converted_at_invoice_month": True, "clause": None},
             "chargeable_weight_divisor": "6000", "chargeable_weight_round_to_kg": "0.5", "storage_free_days": "5",
             "rules": {k: clause() for k in ("pricing_date", "minimum_charge", "fuel", "dangerous_goods", "dry_ice",
                                             "storage", "delivery", "customs", "rate_notices", "precedence",
                                             "unranked_instruments", "quoted_text", "waivers",
                                             "extension_of_due_date")},
             "schedule1": [
                 {"person": "Rae Rates", "title": "Pricing Manager", "party": "CAR-US", "categories": ["rates"],
                  "email": "rae@carrier.example", **clause()},
                 {"person": "Kim Key", "title": "Key Account Manager", "party": "CAR-US",
                  "categories": ["notices", "billing_disputes"], "email": "kim@carrier.example", **clause()},
                 {"person": "Wes Waiver", "title": "Finance Lead", "party": "CAR-US",
                  "categories": ["waivers", "payment_terms"], "email": "wes@carrier.example", **clause()},
                 {"person": "Tia Treasury", "title": "Treasury", "party": "CAR-US", "categories": ["treasury"],
                  "email": "tia@carrier.example", **clause()},
                 {"person": "Ann Payables", "title": "AP Manager", "party": "SHP-US",
                  "categories": ["notices", "payment_terms", "billing_disputes"], "email": "ann@shipper.example",
                  **clause()}],
             "amendment_changes": []}
    terms.update(over)
    rates = {"currency": "USD",
             "periods": [{"label": "P1", "start": "2031-12-01", "end": "2032-05-31", **clause()},
                         {"label": "P2", "start": "2032-06-01", "end": "2032-11-30", **clause()}],
             "rows": [
                 {"lane": "AAA-BBB", "is_minimum": True, "min_kg": None, "max_kg": None,
                  "rates": [{"period_label": "P1", "rate": "80.00"}, {"period_label": "P2", "rate": "82.00"}],
                  "effective_from": None, "effective_to": None, **clause("AAA-BBB minimum charge 80.00 82.00", 8)},
                 {"lane": "AAA-BBB", "is_minimum": False, "min_kg": "0", "max_kg": "44.5",
                  "rates": [{"period_label": "P1", "rate": "7.73"}, {"period_label": "P2", "rate": "7.93"}],
                  "effective_from": None, "effective_to": None, **clause("AAA-BBB 0-44.5 kg 7.73 7.93", 8)},
                 {"lane": "AAA-BBB", "is_minimum": False, "min_kg": "45", "max_kg": "99.5",
                  "rates": [{"period_label": "P1", "rate": "6.81"}, {"period_label": "P2", "rate": "6.99"}],
                  "effective_from": None, "effective_to": None, **clause("AAA-BBB 45-99.5 kg 6.81 6.99", 8)},
                 {"lane": "AAA-BBB", "is_minimum": False, "min_kg": "100", "max_kg": "299.5",
                  "rates": [{"period_label": "P1", "rate": "6.01"}, {"period_label": "P2", "rate": "6.16"}],
                  "effective_from": None, "effective_to": None, **clause("AAA-BBB 100-299.5 kg 6.01 6.16", 8)},
                 {"lane": "AAA-BBB", "is_minimum": False, "min_kg": "300", "max_kg": None,
                  "rates": [{"period_label": "P1", "rate": "5.50"}, {"period_label": "P2", "rate": "5.60"}],
                  "effective_from": None, "effective_to": None, **clause("AAA-BBB 300+ kg 5.50 5.60", 8)}]}
    tables = {"fuel": [{"month": "2031-12", "pct": "20.16", **clause("2031-12 20.16%", 9)},
                       {"month": "2032-01", "pct": "19.00", **clause("2032-01 19.00%", 9)}],
              "accessorials": [
                  {"code": "SEC", "name": "Security surcharge", "fee": "0.12", "basis": "kg", "months": [], **clause()},
                  {"code": "DG", "name": "Dangerous goods fee", "fee": "124.02", "basis": "shipment", "months": [],
                   **clause()},
                  {"code": "DRYICE", "name": "Dry ice handling fee", "fee": "45.40", "basis": "shipment",
                   "months": [], **clause()},
                  {"code": "DLV", "name": "Delivery fee", "fee": "116.13", "basis": "shipment", "months": [],
                   **clause()},
                  {"code": "STOR", "name": "Storage", "fee": "28.88", "basis": "day", "months": [], **clause()},
                  {"code": "CUSTOMS", "name": "Customs hold fee", "fee": "227.14", "basis": "shipment",
                   "months": [], **clause()},
                  {"code": "PEAK", "name": "Peak season surcharge", "fee": "0.29", "basis": "kg",
                   "months": [9, 10, 11], **clause()}],
              "aliases": [
                  {"code": "FRT", "labels": ["Air freight", "Express freight"], **clause()},
                  {"code": "FUEL", "labels": ["Fuel surcharge", "FSC"], **clause()},
                  {"code": "SEC", "labels": ["Security surcharge", "Screening fee", "Screening fee (adj.)"],
                   **clause()},
                  {"code": "DG", "labels": ["Dangerous goods fee", "DG handling"], **clause()},
                  {"code": "DRYICE", "labels": ["Dry ice handling fee"], **clause()},
                  {"code": "DLV", "labels": ["Delivery fee", "Door delivery"], **clause()},
                  {"code": "STOR", "labels": ["Storage"], **clause()},
                  {"code": "CUSTOMS", "labels": ["Customs hold fee"], **clause()},
                  {"code": "PEAK", "labels": ["Peak season surcharge", "PSS"], **clause()},
                  {"code": "LATE", "labels": ["Late fee", "Late payment fee"], **clause()}],
              "fx": [], "fx_update_rule": None}
    return rec(f"batch_01/0001.eml#MSA-{cid}.pdf", "contract", {"terms": terms, "rates": rates, "tables": tables},
               received=received)


def line(shipment, pickup, label, lane, qty, unit, rate, amount, quote=None, page=1, refers=None):
    return {"shipment": shipment, "pickup_date": pickup, "label": label, "lane": lane, "qty": qty, "unit": unit,
            "rate": rate, "amount": amount, "refers_to_invoice": refers, "refers_to_period": None,
            "quote": quote or f"{shipment} {label} {amount}", "page": page, "quote_ok": True}


def invoice(inv_id, date, lines, ref=None, received=None, contract="C-1", due=None, doc_type="invoice",
            currency="USD", total=None, credit=None):
    ref = ref or f"batch_01/00{abs(hash(inv_id)) % 90 + 10}.eml#{inv_id}.pdf"
    facts = {"doc_type": doc_type, "invoice_id": inv_id, "invoice_id_quote": clause(f"INVOICE {inv_id}", 1),
             "invoice_date": date, "due_date": due, "contract_id": contract, "currency": currency,
             "total": total or str(sum(float(x["amount"]) for x in lines)), "total_quote": None,
             "marked_copy_or_reminder": False, "lines": lines,
             "credit": credit or {"credits_invoice": None, "period": None, "credit_type": None}}
    return rec(ref, "invoice", facts, received=received or f"{date}T12:00:00+00:00")


def email(ref, received, sender, **facts):
    base = {"intent": "other", "contract_id": None, "waivers": [], "quoted_waivers": [], "extensions": [],
            "rate_notices": [], "statuses": [], "customs_holds": [], "invoice_refs": [], "contract_changes": [],
            "instructions_to_automation": []}
    base.update(facts)
    return rec(ref, "email", base, received=received, sender=sender)


def tracking(rows, ref="batch_01/0005.eml#tracking.xlsx", received="2032-02-29T10:00:00+00:00"):
    out = [{"shipment": s, "event": e, "date": d, "station": st, "reason": "-",
            "quote": f"{s} | {e.upper()} | {d} | {st} | -", "page": 1, "quote_ok": True} for s, e, d, st in rows]
    return rec(ref, "table", {"table_kind": "tracking", "tracking": out}, received=received)


def ledger(rows, ref="batch_01/0041.eml#ap.xlsx", received="2032-08-30T10:00:00+00:00"):
    out = [{"invoice_id": i, "invoice_date": d, "due_date": due, "amount": a, "status": s, "paid": s == "paid",
            "paid_date": p, "quote": f"{i} | {d} | due {due} | USD {a} | {s} | {p or ''}".rstrip(" |"),
            "page": 1, "quote_ok": True} for i, d, due, a, s, p in rows]
    return rec(ref, "table", {"table_kind": "payment_ledger", "ledger": out}, received=received)
