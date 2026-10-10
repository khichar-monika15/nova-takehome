# Design

The program has two stages. At ingest, a model reads each document once and returns typed facts with quotes. At report time, plain Python joins the facts and applies GLOSSARY.md. The model never computes money, dates, precedence or actions.

## Fact model

Each document gets one JSON file in the state folder. The file holds the document reference (`batch_01/0014.eml#INV-1.pdf`), the Date header of its email, the sender, the page text and the facts. Each document type has its own schema: contract terms, rate table, annex tables, invoice lines, email intents, waybill and dangerous goods declaration. For a spreadsheet, the model maps the columns from the first rows, and code reads every row. Every fact carries a quote and a page. Code finds each quote in the grader's text layer (`grader/extract.py`) and replaces it with the exact page text. A report reads only the documents received by its date.

## Conflicts

`terms.rate()` finds the rate for a lane, weight and pickup date. It reads four sources: the MSA period column, signed amendments, rate notices and feedback. Between amendments, the later effective date wins. Schedule 1 of the contract must list the sender of a rate notice for rates. Otherwise the notice does not count. A signed amendment and an authorised notice can be in force together with different rates. Then the precedence clause does not rank them, so the item is a conflict. It cites both sources, and its range is the overcharge under each rate. A source without authority never makes a conflict, and the stronger source decides. Examples are an unlisted sender, quoted text and an unsigned draft.

## Confidence

Confidence starts from the verdict: 0.92 for a finding, 0.80 for a conflict, 0.75 for cannot_determine. It goes down for each weakness. Two weaknesses are a pickup date from the invoice instead of a carrier record, and a model judgment on a condition. An INR conversion and evidence that code cannot cite also lower it. The weights are set by hand. On the practice mailbox, every reported item is right and the Brier score is 0.0226. The 21 eval cases also end with no wrong item, so no set of mine measures AUROC yet.

## People in the loop

A conflict goes to a person as `escalate`. An outbound remedy of $5,000.00 or more on one invoice or credit key is `human_review` in both modes. The sum covers every finding on that invoice. In supervised mode, every other outbound action is a draft. When the unattended test passes in autonomous mode, the program executes a dispute, a credit claim or a document request. Otherwise the item goes to `human_review`. The test needs cited evidence, a recipient that Schedule 1 names, and no open conflict on the same contract and lane. For an overcharge, it also needs a pickup date from tracking or a carrier email. A final guard turns any `execute:` in supervised mode into a draft. Items carry no addresses, so text in an email cannot redirect a dispute.

## Feedback

`feedback` stores each decision with its batch and date. `close` and `reject` remove only their key. `override_amount` sets the amount of its key. A standing fact applies only where every filter in `applies_to` matches, inside its dates. The standing facts are `sender_authority`, `rate_accepted` and `precedence`. A `one_off_approval` waives only the named months on the named invoice. Every item that changes because of feedback carries `learned_at`. A later signed amendment beats a feedback fact, because the rate order reads amendments first.

## New documents

Each report recomputes every key from all documents received by its date. A history file keeps the last id and state of each key. When the verdict or amount changes, the item gets a new id and `supersedes` the old one. A key that exists only because of a backdated amendment gets `retro: true`. When the condition of a key ends, the key is not reported. Examples are a paid due date and a passed expiry. A new invoice layout needs no code change, because the model reads lines by meaning and code checks the quotes.

## Cost

The practice and exam mailboxes hold 249 documents and took 391 model calls. Per 1,000 documents, that is about 1.83 million input tokens and 0.64 million output tokens. At Claude Opus 5.5 prices ($4 and $20 per million) plus 30% more tokens for its tokenizer, the cost is about $26 per 1,000 documents. Classification on Claude Sonnet 5.5 reads only the first 2,500 characters of each document and adds about $1.70. These numbers come from the usage log that `llm.py` writes for every call. On Claude Opus 5.5 through Bedrock, an invoice took 80 to 106 seconds and a contract about 2.5 minutes. With 12 documents at a time, a batch of 80 documents needs about 6 minutes of model time, and 1,000 documents need about 70 minutes.

## What I'd do next

In the local results, Claude Opus 5.5 read the emails and contracts, and `gpt-5.5` read the invoices and records. The first next step is a full run on the Anthropic API with all the Claude models it uses. After that, the confidence weights need a logistic fit on more labelled cases. The margin step-down credit is not built, because no practice or exam contract uses it. The least certain rules are house waybills rated at their own weight band, and the holder named for a forwarded waiver.
