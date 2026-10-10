# Design

The program has two stages. At ingest, a model reads each document once and returns typed facts with quotes. At report time, plain Python joins the facts and applies GLOSSARY.md. The model never computes money, dates, precedence or actions.

## Fact model

Each document gets one JSON file in the state folder. Each document type has its own schema: contract terms, rates, annex tables, invoice lines, email intents, waybill and dangerous goods declaration. For a spreadsheet, the model maps the columns, and code reads every row. Every fact carries a quote and a page. Code finds each quote in the grader's text layer (`grader/extract.py`) and replaces it with the exact page text.

## Conflicts

`terms.rate()` finds the rate for a lane, weight and pickup date in four sources: the MSA period column, signed amendments, rate notices and feedback. The later amendment wins. If Schedule 1 does not list the sender of a rate notice for rates, the notice does not count. A signed amendment and an authorised notice can be in force together with different rates. The code does not read the precedence clause, so it treats them as unranked, and the item is a conflict. It cites both sources, and its range is the overcharge under each rate. A source without authority, such as quoted text or an unsigned draft, never makes a conflict.

## Confidence

Confidence starts from the verdict: 0.92 for a finding, 0.80 for a conflict, 0.75 for cannot_determine. Authority and the clause in force are gates: a source that fails either never makes an item. Extraction, agreement and completeness lower the score: a quote that code cannot find, a pickup date from the invoice, an INR conversion, or a model judgment on a condition. The weights are set by hand. On the practice mailbox, every reported item is right and the Brier score is 0.0226. The 21 eval cases also end with no wrong item, so no set of mine measures AUROC yet.

## People in the loop

A conflict goes to a person as `escalate`. An outbound remedy of $5,000.00 or more on one invoice or credit key is `human_review` in both modes. In supervised mode, every other outbound action is a draft. If the unattended test passes in autonomous mode, the program executes a dispute, a credit claim or a document request. The test needs cited evidence, a recipient that Schedule 1 names, and no open conflict on the same contract and lane. An overcharge also needs a pickup date from tracking or a carrier email. Otherwise the item goes to `human_review`. A final guard turns any `execute:` in supervised mode into a draft. Text in a document is data: extraction returns typed fields, no rule reads an instruction to automated readers, and items carry no addresses.

## Feedback

`feedback` stores each decision with its batch and date. `close` and `reject` remove only their key, and `override_amount` sets the amount of its key. A standing fact (`sender_authority`, `rate_accepted`, `precedence`) applies only where every filter in `applies_to` matches, inside its dates. A `one_off_approval` waives only the named months on the named invoice. Every item that feedback changes carries `learned_at`. A later signed amendment beats a feedback fact.

## New documents

Each report recomputes every key from all documents received by its date. A history file keeps the last id and state of each key. When the verdict or amount changes, the item gets a new id and `supersedes` the old one. A key that exists only because of a backdated amendment gets `retro: true`. A key whose condition ends, such as a paid due date, is not reported. A new invoice layout needs no code change, because the model reads lines by meaning.

## Cost

On the exam mailbox, every call ran on Claude Opus 5.5: 176 calls for 86 documents. Per 1,000 documents, that is about 6.6 million input tokens and 1.1 million output tokens. At $4 and $20 per million tokens, that is about $48. The grader's setup sends classification and the small records to Sonnet 5.5, so its cost is a little lower. Time is the tighter limit. Ingest and report stop starting work early enough to end inside 600 seconds.

## What I'd do next

Claude Opus 5.5 read the whole exam mailbox, and the emails and contracts elsewhere. `gpt-5.5` read the other practice and eval documents. The first next step is a full run on the Anthropic API, Sonnet 5.5 included. Then the confidence weights need a logistic fit on labelled cases with wrong items. Other gaps are the precedence clause, a late FX annex and the margin step-down credit.
