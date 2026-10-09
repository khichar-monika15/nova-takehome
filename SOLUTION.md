# My solution

## How to run it

Run `make setup`, then set `ANTHROPIC_API_KEY` in the shell. The grader commands work as the brief describes: `make grade`, `make sheet`, `make eval` and `make validate`. The program needs no packages beyond `harness/requirements.txt`. When `ANTHROPIC_API_KEY` is set, every model call goes to Claude: `claude-opus-5-5` for reading, and `claude-sonnet-5-5` for the document type and as a second try. When only `OPENAI_API_KEY` is set, the calls go to OpenAI instead. That path is for local development only, and `harness/requirements-dev.txt` installs the `openai` package for it. For the unit tests, run `.venv/bin/python -m pytest harness/tests -q`.

## What works

The practice card is 99.5 out of 100, and every hard gate is clear. Detection F1 is 1.00 with 22 hits, no false items and no misses. The program recovers $14,140.09 of $14,140.09 and disputes nothing by mistake. Adaptation is 11 of 11, learning is 3 of 3, and the clean controls are 16 of 16. The exam answer sheet matches an answer key that a separate agent built by hand from the exam mailbox, 9 of 9 rows. It includes the finding on the scanned invoice. All 8 worked examples match their expected reports. The own eval set has 19 cases on 16 new mailboxes, plus the 2 samples, and all 21 pass. Those mailboxes use a new customer, a new carrier, new code names, new lane wording and a new statement layout. There are 103 unit tests, and all pass.

## What doesn't

The local runs used `gpt-5.5`, because no Anthropic key was available. The Claude path sends the same prompts and schemas through the same code, but it has not run against the live API. A reviewer sent its requests through the installed SDK with a fake transport and checked their shape. A clean checkout with an invalid key fails each call cleanly and still prints a valid report. The schemas have no union types, because Claude allows at most 16 of them in one request. If the API refuses a schema, the call asks for plain JSON instead. The confidence weights are set by hand, and the practice set cannot test AUROC because every item there is right. The margin step-down credit is not built. Every rule follows GLOSSARY.md, and no rule uses a practice name, lane or file.

## The eval case that caught a bug

Eight cases on the new mailboxes found a real bug, for example `vb_overcharge_wrong_band.yaml`. The first eval run passed 12 of 21 cases. Each overcharge on the new statement layout was missing from the report, and the injection case found $9.60 of $24.84.

Two faults in the rules caused it. The rules looked for the practice contract's charge codes (`FRT`, `FUEL`, `SEC`, `LATE`). The new contract calls them `FSC`, `SCR` and other names. Also, the rules compared lanes as exact text, and the new contract writes `USTQM to INVKH` while its statements print the two stations apart. The extracted facts were right, so the fault was in stage 2.

The fix has two parts. The model now tags each Annex D and Annex E code with a charge kind from its meaning, such as freight, fuel or security. The rules use only those kinds. A lane becomes its two station codes, whatever the wording. After the fix, all 21 cases pass, and the practice card and the exam sheet did not change. The tests in `harness/tests/test_new_world.py` run the same arithmetic on a contract with renamed codes.
