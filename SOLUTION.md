# My solution

## How to run it

Run `make setup`, then set `ANTHROPIC_API_KEY` in the shell. The grader commands work as the brief describes: `make grade`, `make sheet`, `make eval` and `make validate`. For the unit tests, run `.venv/bin/python -m pytest harness/tests -q`. The program needs no packages beyond `harness/requirements.txt`.

The provider follows the keys that are set. `ANTHROPIC_API_KEY` sends every call to Claude. Without it, `AWS_BEARER_TOKEN_BEDROCK` sends the same Claude requests through Amazon Bedrock, and `OPENAI_API_KEY` sends them to OpenAI. The two local paths are for development only. On Claude, `claude-opus-5-5` reads emails, contracts and invoices. `claude-sonnet-5-5` finds the document type and reads waybills, dangerous goods declarations and spreadsheet headers. Each model is the second try for the other.

Before you run it, know these facts:

- Ingest reads 12 documents at a time. The variable `NOVA_WORKERS` sets a lower number for a key with low rate limits.
- Ingest starts no document after 420 seconds, and every call ends before 540 seconds, retries included.
- `report` first reads any document that is still unread, for up to 420 seconds. Then it builds the report. A document that stays unread is left out, and the report is still valid JSON.
- No full batch was timed live on the Anthropic API. On Bedrock, an invoice took 80 to 106 seconds.
- The local results replay model replies from `.work/llm_cache`, which is not in the repository. In a clean checkout, every call goes to the API.
- The GitHub workflow runs only by hand, because the repository holds no API key.

## What works

The practice card is 99.5 out of 100, and every hard gate is clear. Detection F1 is 1.00 with 22 hits, no false items and no misses. The program recovers $14,140.09 of $14,140.09 and disputes nothing by mistake. Adaptation is 11 of 11, learning is 3 of 3, and the clean controls are 16 of 16.

The exam answer sheet matches 9 of 9 rows of an answer key that a separate agent built from the exam mailbox without the code. Every model reply behind the final exam run came from Claude Opus 5.5. On the same requests, Claude and `gpt-5.5` agreed on 26 of 27 invoices, 45 of 45 document types and 8 of 8 waybills. The one difference was the sign of a credit note total, and the answer sheet did not change. Claude also read the lane on the scanned invoice correctly, where `gpt-5.5` had misread it.

A probe sent the program's own invoice request through `anthropic.Anthropic`, the client the grader uses, with Bedrock as its endpoint. The reply parsed and matched the schema.

All 8 worked examples match their expected reports. The own eval set has 24 cases on 16 new mailboxes, plus the 2 samples, and all 26 pass. The new mailboxes use a new customer, a new carrier, new charge codes, new lane wording and a new statement layout. There are 149 unit tests, and all pass. No rule uses a practice name, lane or file.

## What doesn't

The practice card and the eval results mix two models, because no Anthropic API key was available. Claude Opus 5.5 through Bedrock read the emails and contracts. `gpt-5.5` read the invoices, waybills, declarations and spreadsheets. The OpenAI credit ran out, and Bedrock lost most calls above 2 at a time, so only the exam was read again on Claude. Bedrock offers only Opus, so Sonnet 5.5 never ran. Its tasks are small. If a Sonnet call fails, Opus takes over.

The confidence weights are set by hand, and no labelled set of mine has a wrong item, so AUROC is not measured. The margin step-down credit is not built. The code treats a signed amendment and an authorised rate notice as unranked, and it does not read the precedence clause. A cited annex that arrives later is found by its name in the file name or on its first page. A late FX annex is not handled yet.

## The eval case that caught a bug

The first eval run passed 12 of 21 cases: 9 of my 19 cases failed. One of them was `vb_overcharge_wrong_band.yaml`, with this line:

`FAIL  vb_overcharge_wrong_band.yaml: wrong weight band on a new statement layout, fuel follows the freight base`

The overcharges on the new statement layout were missing, and so was a compounded late fee. The injection case found $9.60 of $24.84.

Two faults in the rules caused it. The rules looked for the practice contract's charge codes (`FRT`, `FUEL`, `SEC`, `LATE`). The new contract uses other codes, such as `FSC` and `SCR`. The rules also compared lanes as exact text. The new contract writes `USTQM to INVKH`, and its statements print the two stations apart. The extracted facts were right, so the fault was in stage 2.

The fix has two parts. The model now tags each charge code with a charge kind from its meaning, such as freight or fuel. The rules use only those kinds. A lane becomes its two station codes, whatever the wording. After the fix, all cases passed, and the practice card and the exam sheet did not change. The tests in `harness/tests/test_new_world.py` run the same arithmetic on a contract with renamed codes.

In the final pass, a new eval case also proved a fix. If a one-off authority fact acts as standing, `vb_feedback_one_off_authority_not_wider.yaml` fails. With the fix, it passes.
