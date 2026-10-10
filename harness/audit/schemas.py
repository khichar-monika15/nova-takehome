"""JSON schemas for each extraction call. Every object is closed, every field is required and has one type, because
Claude's structured output allows few optional or union-type fields per request. A value the document does not state
comes back as an empty string, -1 for a column index, "none" for a choice, or an empty quote with page 0."""
from __future__ import annotations


def obj(**props) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def arr(item: dict) -> dict:
    return {"type": "array", "items": item}


def enum(*values: str, nullable: bool = False) -> dict:
    return {"type": "string", "enum": [*values, "none"] if nullable else list(values)}


STR = {"type": "string"}
NSTR = STR
BOOL = {"type": "boolean"}
INT = {"type": "integer"}
NINT = INT


def cited(**props) -> dict:
    """An object that carries a verbatim quote and its page."""
    return obj(**props, quote=STR, page=INT)


CLAUSE = cited()

DOC_KINDS = ("contract", "invoice", "awb", "dgd", "table", "other")

CLASSIFY = obj(
    kind=enum(*DOC_KINDS),
    reason=STR,
)

CATEGORIES = ("rates", "waivers", "payment_terms", "notices", "billing_disputes", "treasury", "other")

EMAIL = obj(
    intent=enum("waiver", "due_date_extension", "rate_notice", "shipment_status", "customs_hold", "invoice_cover",
                "payment_request", "credit_note_cover", "contract_cover", "contract_change", "document_request",
                "dispute", "other"),
    contract_id=NSTR,
    waivers=arr(cited(shipments=arr(STR), months=arr(STR), invoice_id=NSTR, charge=STR, one_off=BOOL,
                      conditional=BOOL, condition=NSTR, condition_met=enum("yes", "no", "unknown", "not_applicable"))),
    quoted_waivers=arr(cited(shipments=arr(STR), months=arr(STR), invoice_id=NSTR, charge=STR,
                             quoted_author_name=NSTR, quoted_author_email=NSTR)),
    extensions=arr(cited(invoice_id=STR, new_due_date=STR)),
    rate_notices=arr(cited(contract_id=NSTR, reference=NSTR, lane=STR, effective_from=NSTR, effective_to=NSTR,
                           rows=arr(cited(is_minimum=BOOL, min_kg=NSTR, max_kg=NSTR, rate=STR, currency=NSTR)))),
    statuses=arr(cited(shipment=STR, event=enum("picked_up", "departed", "arrived_facility", "out_for_delivery",
                                               "delivered", "collected_by_consignee", "customs_hold",
                                               "customs_released", "other"),
                       date=NSTR, station=NSTR)),
    customs_holds=arr(cited(shipment=STR, date=NSTR, released=NSTR, reason_code=NSTR,
                            cause=enum("carrier", "shipper", "unknown"))),
    invoice_refs=arr(cited(invoice_id=STR, asks_payment=BOOL, marked_copy_or_reminder=BOOL)),
    contract_changes=arr(cited(contract_id=NSTR, change=enum("extension", "termination_notice",
                                                             "non_renewal_notice", "renewal", "other"),
                               new_end_date=NSTR, signed_by_both=BOOL)),
    instructions_to_automation=arr(obj(text=STR, page=INT)),
)

CONTRACT_TERMS = obj(
    doc_type=enum("msa", "amendment", "extension", "other_agreement"),
    contract_id=STR,
    amendment_ref=NSTR,
    parent_contract_id=NSTR,
    signed_by_both=BOOL,
    dated=NSTR,
    effective_date=NSTR,
    end_date=NSTR,
    term=CLAUSE,
    auto_renews=BOOL,
    renewal_term_months=NSTR,
    non_renewal_notice_days=NSTR,
    renewal=CLAUSE,
    currency=STR,
    parties=obj(shipper_name=NSTR, shipper_code=NSTR, carrier_name=NSTR, carrier_code=NSTR),
    payment_days=NSTR,
    payment=CLAUSE,
    late_fee=obj(rate_pct=NSTR, grace_days=NSTR, compounding=BOOL, clause=CLAUSE),
    rebate=obj(applies=BOOL, tiers=arr(obj(threshold=STR, pct=STR)), threshold_currency=NSTR,
               period=enum("quarter", "contract_year", "month", "other", nullable=True), credit_due_days=NSTR,
               clause=CLAUSE),
    improvement_credit=obj(applies=BOOL, pct=NSTR, due_days_after_anniversary=NSTR, clause=CLAUSE),
    margin_step_down=obj(applies=BOOL, base_margin_pct=NSTR, stepped_margin_pct=NSTR, threshold=NSTR,
                         threshold_basis=NSTR, clause=CLAUSE),
    qualifying_spend=obj(includes=arr(STR), excludes=arr(STR), net_of_credit_notes=BOOL,
                         inr_converted_at_invoice_month=BOOL, clause=CLAUSE),
    chargeable_weight_divisor=NSTR,
    chargeable_weight_round_to_kg=NSTR,
    storage_free_days=NSTR,
    rules=obj(pricing_date=CLAUSE, minimum_charge=CLAUSE, fuel=CLAUSE, dangerous_goods=CLAUSE, dry_ice=CLAUSE,
              storage=CLAUSE, delivery=CLAUSE, customs=CLAUSE, rate_notices=CLAUSE, precedence=CLAUSE,
              unranked_instruments=CLAUSE, quoted_text=CLAUSE, waivers=CLAUSE, extension_of_due_date=CLAUSE),
    schedule1=arr(cited(person=STR, title=NSTR, party=STR, categories=arr(enum(*CATEGORIES)), email=NSTR)),
    amendment_changes=arr(cited(kind=enum("rates", "fuel", "accessorials", "term", "other"), lanes=arr(STR),
                                effective_from=NSTR, effective_to=NSTR, all_periods=BOOL,
                                cites_document=NSTR, cited_document_attached=BOOL)),
)

CONTRACT_RATES = obj(
    currency=NSTR,
    periods=arr(cited(label=STR, start=NSTR, end=NSTR)),
    rows=arr(cited(lane=STR, is_minimum=BOOL, min_kg=NSTR, max_kg=NSTR,
                   rates=arr(obj(period_label=STR, rate=STR)), effective_from=NSTR, effective_to=NSTR)),
)

CHARGE_KINDS = ("freight", "fuel", "security", "dangerous_goods", "dry_ice", "delivery", "storage", "customs",
                "peak", "monthly_fee", "late_fee", "duty", "tax", "margin", "cost", "handling", "other")

CONTRACT_TABLES = obj(
    fuel=arr(cited(month=STR, pct=STR)),
    accessorials=arr(cited(code=STR, name=STR, kind=enum(*CHARGE_KINDS), fee=STR,
                           basis=enum("shipment", "kg", "day", "month", "percent", "other"), months=arr(INT))),
    aliases=arr(cited(code=STR, kind=enum(*CHARGE_KINDS), labels=arr(STR))),
    fx=arr(cited(month=STR, inr_per_usd=STR)),
    fx_update_rule=CLAUSE,
)

INVOICE = obj(
    doc_type=enum("invoice", "statement", "credit_note", "other"),
    invoice_id=STR,
    invoice_id_quote=cited(),
    invoice_date=NSTR,
    due_date=NSTR,
    contract_id=NSTR,
    currency=STR,
    total=NSTR,
    total_quote=CLAUSE,
    marked_copy_or_reminder=BOOL,
    lines=arr(cited(shipment=NSTR, pickup_date=NSTR, label=STR, kind=enum(*CHARGE_KINDS), lane=NSTR, qty=NSTR,
                    unit=enum("kg", "shipment", "day", "month", "percent_of_base", "other"), rate=NSTR, amount=STR,
                    refers_to_invoice=NSTR, refers_to_period=NSTR)),
    credit=obj(credits_invoice=NSTR, period=NSTR,
               credit_type=enum("rebate", "margin_step_down", "promised_credit", "billing_correction", "other",
                                nullable=True)),
)

AWB = obj(
    shipment=STR,
    executed_date=NSTR,
    origin=NSTR,
    destination=NSTR,
    pieces=NSTR,
    actual_kg=NSTR,
    chargeable_kg=NSTR,
    master_shipment=NSTR,
    house_shipments=arr(STR),
    nature=NSTR,
    handling=NSTR,
    quote=STR,
    page=INT,
)

DGD = obj(
    shipment=STR,
    un_numbers=arr(STR),
    dangerous_goods_other_than_dry_ice=BOOL,
    dry_ice_refrigerant_only=BOOL,
    quote=STR,
    page=INT,
)

TABLE = obj(
    table_kind=enum("tracking", "payment_ledger", "other"),
    sheet=INT,
    header_row=INT,
    columns=obj(shipment=NINT, event=NINT, event_date=NINT, station=NINT, reason=NINT, invoice_id=NINT,
                invoice_date=NINT, due_date=NINT, amount=NINT, status=NINT, paid_date=NINT),
    date_format=NSTR,
    paid_status_words=arr(STR),
    event_names=obj(picked_up=NSTR, arrived_facility=NSTR, delivered=NSTR, collected_by_consignee=NSTR),
)

def part(schema: dict, *keys: str) -> dict:
    """A smaller schema with some fields of a larger one: Claude refuses a grammar that compiles too large."""
    return obj(**{k: schema["properties"][k] for k in keys})


EMAIL_PARTS = {
    "email_main": part(EMAIL, "intent", "contract_id", "waivers", "quoted_waivers", "extensions", "invoice_refs"),
    "email_records": part(EMAIL, "rate_notices", "statuses", "customs_holds", "contract_changes",
                          "instructions_to_automation"),
}
TERMS_PARTS = {
    "contract_dates": part(CONTRACT_TERMS, "doc_type", "contract_id", "amendment_ref", "parent_contract_id",
                           "signed_by_both", "dated", "effective_date", "end_date", "term", "auto_renews",
                           "renewal_term_months", "non_renewal_notice_days", "renewal", "currency", "parties",
                           "payment_days", "payment", "late_fee"),
    "contract_credits": part(CONTRACT_TERMS, "rebate", "improvement_credit", "margin_step_down", "qualifying_spend",
                             "chargeable_weight_divisor", "chargeable_weight_round_to_kg", "storage_free_days"),
    "contract_rules": part(CONTRACT_TERMS, "rules"),
    "contract_people": part(CONTRACT_TERMS, "schedule1", "amendment_changes"),
}

ALL = {
    "classify": CLASSIFY,
    **EMAIL_PARTS,
    **TERMS_PARTS,
    "contract_rates": CONTRACT_RATES,
    "contract_tables": CONTRACT_TABLES,
    "invoice": INVOICE,
    "awb": AWB,
    "dgd": DGD,
    "table": TABLE,
}
