# Subagent: Study the grader internals

Source: `agent-a600e2aa95fff4063.jsonl`. Tool results are cut to 1500 characters, tool inputs to 2500. API keys are replaced with a marker. Nothing else is removed.

## User 2026-10-08 16:27:52

Research task, read-only. Do NOT write, clone, or download any file to disk. Use only `gh api` piped to stdout (and `python3 -I -c` reading stdin if you need to parse). Write `command ls`, never plain `ls` (it is aliased to a tool that hangs without a terminal).

Context: a job candidate must build a Python "harness" for the public GitHub repo `gocomet-india/nova-takehome` (branch main). The harness has three CLI commands the grader calls in fresh processes: `ingest <batch_dir> --state-dir <dir>`, `report --as-of YYYY-MM-DD --mode supervised|autonomous --state-dir <dir>` (prints report.json to stdout), `feedback <feedback.json> --state-dir <dir>`. It audits freight invoices (6 classes: overcharge, duplicate, waived_but_billed, late fees, cashback, expiry, plus conflict and cannot_determine verdicts). I already read README.md, GLOSSARY.md, SUBMISSION.md, the schema and the stub harness. I need the exact behaviour of the grading code so the plan targets what is actually scored.

Read file contents with: `gh api -H "Accept: application/vnd.github.raw" /repos/gocomet-india/nova-takehome/contents/<path>`

Read fully: grader/run_grader.py, grader/score.py (52 KB, read all of it), grader/grade_sheet.py, grader/make_sheet.py, grader/validate.py, grader/extract.py, tools/check_submission.py, tools/run_mailbox.py, evals/run_evals.py.

Report back, with file:line citations for each claim:
1. The exact sequence run_grader.py runs (ingest/report/feedback order, which as_of dates, both modes, fresh state dirs?), and any per-step timeout values or environment variables it sets.
2. For each of the 7 score components (finding 25, amounts 20, keeping up 15, learning 10, conflicts/missing 10, actions 10 + confidence 5, clean invoices 5): the exact formula, how items are matched to the key, what partial credit exists, and what the practice answer YAML fields feed each one.
3. The exact logic of each of the 5 score caps (instruction-following, one-off waiver treated as permanent, outbound in supervised, escalation over 60%, autonomous unattended failures). How does the grader detect "following an instruction written inside an email"? How is the 60% escalation rate computed (which actions count as escalated, what denominator)?
4. How quotes are verified (normalisation, which text layer, page numbering for xlsx and eml, what happens with a bare attachment name), and how `supersedes`, `retro`, `learned_at`, item `id` stability are checked in "keeping up" and "learning".
5. How confidence is scored (AUROC, Brier: over which items).
6. What grade_sheet.py/make_sheet.py put in answer_sheet.json and how it is compared to the key (tolerances, which fields).
7. What extract.py does: how it reads .eml bodies and PDF/XLSX attachments, page/sheet numbering, reading order. Is it importable as a library from the harness?
8. What check_submission.py checks, exactly.
9. Anything surprising: hidden rules not in the README/GLOSSARY, edge cases the scorer handles, the "variant" field, how `no_finding` items are treated, penalties for extra items.

Keep the report under 1,500 words. Facts with citations, no advice.

**Tool call: Bash**

```json
{
 "command": "gh api \"/repos/gocomet-india/nova-takehome/git/trees/main?recursive=1\" --jq '.tree[] | \"\\(.type) \\(.size // \"\") \\(.path)\"' | grep -v \"^tree\" | head -200",
 "description": "List repo files on main branch"
}
```

<details><summary>tool result</summary>

```
blob 1210 .github/workflows/grade.yml
blob 52 .gitignore
blob 472 AI_USE.md
blob 187992 BRIEF.pdf
blob 1057 DESIGN.md
blob 22889 GLOSSARY.md
blob 2172 Makefile
blob 13889 README.md
blob 686 SOLUTION.md
blob 3204 SUBMISSION.md
blob 217944 data/exam/batch_01/0001.eml
blob 19107 data/exam/batch_01/0002.eml
blob 201262 data/exam/batch_01/0003.eml
blob 19994 data/exam/batch_01/0004.eml
blob 19816 data/exam/batch_01/0005.eml
blob 548 data/exam/batch_01/0006.eml
blob 927 data/exam/batch_01/0007.eml
blob 18066 data/exam/batch_01/0008.eml
blob 18049 data/exam/batch_01/0009.eml
blob 18088 data/exam/batch_01/0010.eml
blob 589 data/exam/batch_01/0011.eml
blob 82892 data/exam/batch_01/0012.eml
blob 19814 data/exam/batch_01/0013.eml
blob 24004 data/exam/batch_01/0014.eml
blob 19783 data/exam/batch_01/0015.eml
blob 11445 data/exam/batch_01/0016.eml
blob 19799 data/exam/batch_01/0017.eml
blob 9017 data/exam/batch_01/0018.eml
blob 1753 data/exam/batch_01/_manifest.json
blob 799 data/exam/batch_02/0001.eml
blob 60260 data/exam/batch_02/0002.eml
blob 18084 data/exam/batch_02/0003.eml
blob 30486 data/exam/batch_02/0004.eml
blob 22917 data/exam/batch_02/0005.eml
blob 18170 data/exam/batch_02/0006.eml
blob 22299 data/exam/batch_02/0007.eml
blob 550 data/exam/batch_02/0008.eml
blob 942 data/exam/batch_02/0009.eml
blob 19826 data/exam/batch_02/0010.eml
blob 37882 data/exam/batch_02/0011.eml
blob 97770 data/exam/batch_02/0012.eml
blob 23331 data/exam/batch_02/0013.eml
blob 47977 data/exam/batch_02/00
... [7733 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api \"/repos/gocomet-india/nova-takehome/git/trees/main?recursive=1\" --jq '.tree[] | \"\\(.type) \\(.size // \"\") \\(.path)\"' | grep -v \"^tree\" | grep -v \"data/scenarios/batch_\\|data/exam/\\|data/examples/\" ",
 "description": "List non-data repo files"
}
```

<details><summary>tool result</summary>

```
blob 1210 .github/workflows/grade.yml
blob 52 .gitignore
blob 472 AI_USE.md
blob 187992 BRIEF.pdf
blob 1057 DESIGN.md
blob 22889 GLOSSARY.md
blob 2172 Makefile
blob 13889 README.md
blob 686 SOLUTION.md
blob 3204 SUBMISSION.md
blob 2025 data/scenarios/answers/sc-1d5d4842.yaml
blob 3144 data/scenarios/answers/sc-28f910a1.yaml
blob 3227 data/scenarios/answers/sc-3874a142.yaml
blob 2058 data/scenarios/answers/sc-3ecb61d3.yaml
blob 3121 data/scenarios/answers/sc-472574a9.yaml
blob 3198 data/scenarios/answers/sc-490f68d0.yaml
blob 1912 data/scenarios/answers/sc-4c5310e6.yaml
blob 3147 data/scenarios/answers/sc-4e59ec78.yaml
blob 1909 data/scenarios/answers/sc-52db5230.yaml
blob 1777 data/scenarios/answers/sc-6e4f24cd.yaml
blob 4010 data/scenarios/answers/sc-6f266dbe.yaml
blob 2740 data/scenarios/answers/sc-6f955cee.yaml
blob 2152 data/scenarios/answers/sc-703db266.yaml
blob 2479 data/scenarios/answers/sc-73ed4854.yaml
blob 3054 data/scenarios/answers/sc-78171a40.yaml
blob 2202 data/scenarios/answers/sc-88c6ccb5.yaml
blob 2967 data/scenarios/answers/sc-9bb38241.yaml
blob 1908 data/scenarios/answers/sc-a6783f61.yaml
blob 3115 data/scenarios/answers/sc-a9066934.yaml
blob 2179 data/scenarios/answers/sc-b7a1aee9.yaml
blob 3223 data/scenarios/answers/sc-bff95595.yaml
blob 2083 data/scenarios/answers/sc-c04b8a91.yaml
blob 2472 data/scenarios/answers/sc-c635bc71.yaml
blob 3056 data/scenarios/answers/sc-c8db301f.yaml
blob 2004 data/scenarios/answers/sc-ddb759a8.yaml
blob 3043 data/scenarios
... [807 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/run_grader.py | cat -n",
 "description": "Read run_grader.py with line numbers"
}
```

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/score.py | cat -n | sed -n '1,400p'",
 "description": "Read score.py lines 1-400"
}
```

<details><summary>tool result</summary>

```
     1	"""Replay the mailbox through a harness, batch by batch, and print the report card.
     2	
     3	    python grader/run_grader.py --harness "python harness/harness.py" --data data/scenarios \
     4	        --key data/scenarios/answers [--mode supervised|autonomous|both] [--out card.json]
     5	    reviewer: ... --key answer_key.json --exclude-key <practice answers>   (practice keys replayed, not scored)
     6	              --sandbox --submission <repo>   (every step in a container; reviewer tooling, not in the pack)
     7	
     8	For each mode and each world, in a fresh folder outside <data>, for each batch in order:
     9	    <harness> ingest <tmp>/mailbox/batch_k --state-dir <tmp>/state     (only the batches seen so far are copied)
    10	    <harness> report --as-of <batch cutoff> --mode <mode> --state-dir <dir>      (stdout = report.json)
    11	    <harness> feedback <tmp>/mailbox/feedback/<world>_batch_k.json --state-dir <dir>   (copied when due)
    12	Every step is a new process with a wall-clock timeout. The first world's batches live in <data>/batch_NN/; a second
    13	world (the reviewer's W2) in <data>/W2/batch_NN/ and gets its own fresh state dir. Every report is kept and scored by
    14	grader/score.py. The candidate and the reviewer run exactly this file; only --data and --key differ.
    15	
    16	Exit code 0 when no hard gate triggered and the last report of every world matches the key (the Level 2 page is
    17	green); 1 otherwise; 2 when th
... [14097 more characters]
```
</details>

<details><summary>tool result</summary>

```
     1	"""Score a replay: every report the harness printed, against a key. Deterministic; used by run_grader.py.
     2	
     3	The same code scores the candidate's practice run (key = data/scenarios/answers/) and the reviewer's run (key =
     4	the reviewer's answer_key.json, with its scenarios/ next to it). Points out of 100 (PLAN.md "Grading and weights"):
     5	
     6	    detection     25  F1 over finding keys, pooled over every report. A hit that cites none of the key's evidence
     7	                      documents with a quote (12+ non-space characters) that is really on the cited page counts half.
     8	                      A conflict or cannot_determine the key doesn't have is a false positive too.
     9	    amount        20  (recovered - 2 x wrongly disputed) / money at stake. Recovered: the key's amount when yours is
    10	                      within USD 0.01, else the smaller of the two. Wrongly disputed: every amount on a finding that
    11	                      should not be there, plus anything you claim above the right amount.
    12	    adaptation    15  Each time new documents change a key's answer (it appears, its verdict or amount moves, it
    13	                      needs `supersedes` or `retro`), the report of that batch must have the new answer. A key you
    14	                      reported that should now be gone must be gone (no stale answers).
    15	    learning      10  After feedback: keys whose answer changes because of it carry the
... [21299 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/score.py | cat -n | sed -n '400,750p'",
 "description": "Read score.py lines 400-750"
}
```

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/score.py | cat -n | sed -n '750,1200p'",
 "description": "Read score.py lines 750-end"
}
```

<details><summary>tool result</summary>

```
   400	def _feedback_items(fb: dict) -> list[dict]:
   401	    return [x for x in (fb or {}).get("items") or [] if isinstance(x, dict)]
   402	
   403	
   404	def score(key: dict, runs: dict, mailboxes: dict[str, Path] | None = None, feedback: dict | None = None,
   405	          exclude: dict | None = None) -> dict:
   406	    """runs: {mode: {world: [{"batch", "as_of", "report": dict|None, "error": str|None}, ...]}} in replay order.
   407	    feedback: {world: {batch: feedback.json dict}} (what was delivered after that batch).
   408	    mailboxes: {world: mailbox root} so quotes can be checked on their pages.
   409	    exclude: a key (load_key) whose items are not scored: the reviewer passes the practice key, so only items the
   410	    candidate has not seen count; report items on those keys are ignored too.
   411	    -> the report card (deterministic)."""
   412	    feedback = feedback or {}
   413	    ev = Evidence(mailboxes)
   414	    modes = [m for m in ("supervised", "autonomous") if m in runs]
   415	    main = "supervised" if "supervised" in runs else (modes[0] if modes else None)
   416	    # practice keys: not scored in the practice batches, nor later while their answer is the one the candidate saw
   417	    skip: set = set()
   418	    prac = {(s["world"], s["k"]): s for s in (exclude or {}).get("scenarios", [])}
   419	    scen = []
   420	    for s in key["scenarios"]:
   421	        ps = prac.get((s["world"], s["k"]))
   422	        if ps is not None:
 
... [19845 more characters]
```
</details>

<details><summary>tool result</summary>

```
   750	    auroc_part = clamp((au - 0.5) / 0.5) if au is not None else brier_part
   751	    act_part = sum(mode_scores.values()) / len(mode_scores) if mode_scores else 0.0
   752	    g = (GATING_ACTIONS * act_part + GATING_CONFIDENCE * (auroc_part + brier_part) / 2) / WEIGHTS["gating"]
   753	    comp["gating"] = {"applicable": bool(modes) and any(v["actions_expected"] for v in gate_detail.values()),
   754	                      "fraction": g,
   755	                      "detail": {"modes": gate_detail, "escalation_rate": round(esc_rate, 4),
   756	                                 "unsafe_autonomous_cases": len(unsafe_keys),
   757	                                 "auroc": None if au is None else round(au, 4),
   758	                                 "brier": None if br is None else round(br, 4), "items_scored": len(confs),
   759	                                 "actions_points": round(GATING_ACTIONS * act_part, 3),
   760	                                 "confidence_points": round(GATING_CONFIDENCE * (auroc_part + brier_part) / 2, 3)}}
   761	
   762	    # ---- clean controls (main mode) ----
   763	    cl_pass = cl_n = 0
   764	    cl_fail: list[str] = []
   765	    for w in sorted(by_world):
   766	        for i, st in enumerate(steps_of(main, w)):
   767	            idx = snaps.get((main, w, i), {})
   768	            for s in by_world[w]:
   769	                e = s["by_batch"].get(st["batch"])
   770	                if not s["control"] or e is None or e.get("verdict"
... [14136 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/extract.py | cat -n",
 "description": "Read extract.py with line numbers"
}
```

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/make_sheet.py | cat -n",
 "description": "Read make_sheet.py with line numbers"
}
```

<details><summary>tool result</summary>

```
     1	"""Read mailbox files back as text, page by page, the way the grader checks a citation.
     2	
     3	Standalone on purpose (the candidate's copy of the grader imports nothing else from this repo). Same rules as the
     4	generator's reader:
     5	- text PDF: words grouped into lines by baseline, each line read left to right; one entry per PDF page;
     6	- XLSX: one "page" per sheet (hidden sheets included), each row as its displayed cell texts joined by " | ";
     7	- .eml: one page: From / To / Cc / Date (ISO, UTC) / Subject, a blank line, the plain-text body, then
     8	  "Attachments: a.pdf, b.xlsx" when there are any.
     9	Comparisons collapse whitespace, because a long line wraps at a space in a PDF.
    10	"""
    11	from __future__ import annotations
    12	
    13	import io
    14	import re
    15	from datetime import date, datetime
    16	from decimal import Decimal
    17	from email import policy
    18	from email.parser import BytesParser
    19	from email.utils import parseaddr, parsedate_to_datetime
    20	from pathlib import Path
    21	
    22	SEP = " | "
    23	
    24	
    25	def norm(s: str) -> str:
    26	    return " ".join(s.split())
    27	
    28	
    29	# ---- PDF --------------------------------------------------------------------------------------------------------------
    30	def _reading_order(page) -> str:
    31	    words = page.get_text("words")
    32	    words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    33	    lines: li
... [8026 more characters]
```
</details>

<details><summary>tool result</summary>

```
     1	"""report.json -> answer_sheet.json (Part 1 of the submission).
     2	
     3	    python grader/make_sheet.py report.json [-o answer_sheet.json]
     4	
     5	The sheet holds, per class, the count, the USD amount and the ids of every `verdict: finding`; the four totals; every
     6	conflict with its two source documents; every cannot_determine with the missing document and who holds it.
     7	
     8	Totals (the brief's formulas):
     9	    total_overpayment = overcharge + duplicate + waived_but_billed + late_fee_not_owed
    10	    cashback_owed     = sum of cashback findings
    11	    late_fees_avoided = sum of late_fee_risk findings (one month's fee each)
    12	    total_savings     = total_overpayment + cashback_owed + late_fees_avoided
    13	conflict, cannot_determine and no_finding never count. Expiry findings are counted and listed; they carry no money.
    14	"""
    15	from __future__ import annotations
    16	
    17	import argparse
    18	import json
    19	import sys
    20	from decimal import Decimal, InvalidOperation
    21	from pathlib import Path
    22	
    23	CLASSES = ["overcharge", "duplicate", "waived_but_billed", "late_fee_not_owed", "cashback", "late_fee_risk", "expiry"]
    24	DATED = ("expiry", "late_fee_risk")          # the deadline is part of the answer: the notice date, the due date
    25	OVERPAYMENT = ["overcharge", "duplicate", "waived_but_billed", "late_fee_not_owed"]
    26	SHEET_VERSION = "1.0"
    27	
    28	
    29	def money
... [5338 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/grade_sheet.py | cat -n",
 "description": "Read grade_sheet.py with line numbers"
}
```

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/grader/validate.py | cat -n",
 "description": "Read validate.py with line numbers"
}
```

<details><summary>tool result</summary>

```
     1	"""Compare an answer_sheet.json with a key and print one page: totals on top, then one row per class.
     2	
     3	    python grader/grade_sheet.py answer_sheet.json --key data/scenarios/answers/ [--json result.json]
     4	
     5	The key can be:
     6	- a folder of answer files (data/scenarios/answers/*.yaml),
     7	- another answer_sheet.json (for example one made from a reference report),
     8	- the reviewer's answer_key.json.
     9	By default the key is read as it stands after the last batch; `--batch batch_01` grades an earlier point.
    10	
    11	A row is ✓ when the count, every id and every amount match (amounts within USD 0.01 per finding), and for expiry and
    12	late-fee risk every deadline. The row lists the ids that are missing (in the key, not on your sheet), extra (on your
    13	sheet, not in the key) and those with the wrong amount or date. A conflict must cite both documents that disagree
    14	(citing more, such as the contract clause, is fine). The page prints both report dates and warns when they differ.
    15	Exit code 0 when every row is ✓.
    16	
    17	On the exam mailbox this check is Part 1 of a submission, and it is a pass/fail gate (Ayush, 2026-09-28): PASS (every
    18	row ✓) means the reviewer goes on to run the code on the hidden set; NOT YET ends the review. It carries no weight in
    19	the final grade beyond that.
    20	"""
    21	from __future__ import annotations
    22	
    23	import argparse
    24	import json
   
... [15810 more characters]
```
</details>

<details><summary>tool result</summary>

```
     1	"""Check a report.json before grading: the schema, every citation, and the harness command line.
     2	
     3	    python grader/validate.py --report report.json --mailbox data/scenarios [--harness harness/harness.py]
     4	
     5	1. Schema: report.json matches grader/schema/report.schema.json.
     6	2. Citations: every evidence `doc` exists in the mailbox and its `quote` is on the cited `page`
     7	   (a scanned PDF has no text, so only its page number is checked).
     8	3. Command line (dry run, nothing is executed for real): `harness.py ingest|report|feedback --help` each exit 0 and
     9	   mention the arguments the grader passes (--state-dir everywhere, --as-of and --mode for report).
    10	Any of the three can run alone. Exit code 0 when nothing failed.
    11	"""
    12	from __future__ import annotations
    13	
    14	import argparse
    15	import json
    16	import subprocess
    17	import sys
    18	from pathlib import Path
    19	
    20	try:
    21	    from grader.extract import Mailbox
    22	    from grader.make_sheet import item_id, items
    23	except ImportError:                                   # run as a script: python grader/validate.py
    24	    from extract import Mailbox
    25	    from make_sheet import item_id, items
    26	
    27	HERE = Path(__file__).resolve().parent
    28	
    29	
    30	def schema_path() -> Path:
    31	    for p in (HERE / "schema" / "report.schema.json", HERE.parent / "contract" / "report.schema.json"):
    3
... [5029 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/tools/check_submission.py | cat -n",
 "description": "Read check_submission.py with line numbers"
}
```

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/tools/run_mailbox.py | cat -n; echo ======; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/evals/run_evals.py | cat -n",
 "description": "Read run_mailbox.py and run_evals.py"
}
```

<details><summary>tool result</summary>

```
     1	"""`make validate`: is this repo ready to send? One line per check (SUBMISSION.md lists them). Exit 0 when all pass.
     2	
     3	    python tools/check_submission.py [--harness harness/harness.py]
     4	"""
     5	from __future__ import annotations
     6	
     7	import argparse
     8	import json
     9	import re
    10	import sys
    11	from pathlib import Path
    12	
    13	ROOT = Path(__file__).resolve().parent.parent
    14	sys.path.insert(0, str(ROOT / "grader"))
    15	
    16	SOLUTION_SECTIONS = ["How to run it", "What works", "What doesn't", "The eval case that caught a bug"]
    17	DESIGN_SECTIONS = ["Fact model", "Conflicts", "Confidence", "People in the loop", "Feedback", "New documents", "Cost",
    18	                   "What I'd do next"]
    19	DESIGN_MAX_WORDS = 1000
    20	MIN_SECTION_WORDS = 15
    21	MIN_OWN_CASES = 10
    22	KEY_RE = re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")
    23	SKIP = {".git", ".venv", "venv", "__pycache__", "data", ".state", "node_modules", ".pytest_cache"}
    24	
    25	
    26	def sections(md: str) -> dict[str, str]:
    27	    out, cur = {}, None
    28	    for line in md.splitlines():
    29	        m = re.match(r"^##\s+(.+?)\s*$", line)
    30	        if m:
    31	            cur = m.group(1)
    32	            out[cur] = ""
    33	        elif cur is not None:
    34	            out[cur] += line + "\n"
    35	    return out
    36	
    37	
    38	def own_words(body: str) -> int:
    39	    """Words in a section, le
... [8009 more characters]
```
</details>

<details><summary>tool result</summary>

```
Exit code 1
     1	"""Run your harness over one mailbox and keep the report. Behind `make sheet` and `make run`.
     2	
     3	    python tools/run_mailbox.py --data data/exam --out out/exam_report.json --sheet answer_sheet.json
     4	    python tools/run_mailbox.py --data data/scenarios --out out/practice_report.json
     5	
     6	It starts from an empty state folder, runs `ingest` on every batch_* folder in order, then one `report` on the last
     7	batch's date from <data>/batches.json (or --as-of). With --sheet it turns that report into answer_sheet.json with
     8	grader/make_sheet.py. Each step is a fresh process, as in the grader.
     9	"""
    10	from __future__ import annotations
    11	
    12	import argparse
    13	import json
    14	import shlex
    15	import shutil
    16	import subprocess
    17	import sys
    18	from pathlib import Path
    19	
    20	ROOT = Path(__file__).resolve().parent.parent
    21	sys.path.insert(0, str(ROOT / "grader"))
    22	
    23	
    24	def harness_cmd(harness: str) -> list[str]:
    25	    cmd = shlex.split(harness)
    26	    if cmd and cmd[0].endswith(".py"):
    27	        cmd = [sys.executable] + cmd
    28	    elif cmd and cmd[0] in ("python", "python3"):
    29	        cmd[0] = sys.executable
    30	    return cmd
    31	
    32	
    33	def step(cmd: list[str], args: list[str], timeout: float) -> tuple[int, str, str]:
    34	    try:
    35	        r = subprocess.run(cmd + args, capture_output=True, text=True, timeout=
... [4885 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/evals/run_evals.py | cat -n",
 "description": "Read run_evals.py with line numbers"
}
```

**Tool call: Bash**

```json
{
 "command": "for p in data/scenarios/batches.json data/scenarios/feedback/W1_batch_01.json data/exam/batches.json Makefile .github/workflows/grade.yml; do echo \"---- $p\"; gh api -H \"Accept: application/vnd.github.raw\" \"/repos/gocomet-india/nova-takehome/contents/$p\" | cat -n; done",
 "description": "Read batches, feedback, Makefile, workflow"
}
```

<details><summary>tool result</summary>

```
     1	"""Run your eval cases (evals/cases/*.yaml) through your harness and score them. Behind `make eval`.
     2	
     3	    python evals/run_evals.py [--harness harness/harness.py] [--cases evals/cases] [--out evals/results.json] [-k name]
     4	
     5	Each case gets a fresh state folder: every batch_* of its mailbox is ingested in order (with a feedback file after
     6	the batch it names, if the case has one), then one report on the case's date and mode. The item with the case's key
     7	is compared with `expect`, using the grader's own matching (grader/score.py): verdict, amount within USD 0.01, the
     8	range for a conflict, the action, and the missing document's name for cannot_determine. `verdict: no_finding` passes
     9	when the key is missing or listed as no_finding. Exit code 0 when every case passes.
    10	"""
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import json
    15	import sys
    16	import tempfile
    17	from pathlib import Path
    18	
    19	import yaml
    20	
    21	ROOT = Path(__file__).resolve().parent.parent
    22	sys.path.insert(0, str(ROOT / "grader"))
    23	sys.path.insert(0, str(ROOT / "tools"))
    24	import score as S  # noqa: E402
    25	from run_mailbox import run  # noqa: E402
    26	
    27	
    28	def find_item(report: dict, key: dict) -> dict | None:
    29	    want = S.key_tuple(key)
    30	    for it in S.report_items(report):
    31	        if S.key_tuple(it) == want:
    32	           
... [4452 more characters]
```
</details>

<details><summary>tool result</summary>

```
---- data/scenarios/batches.json
     1	{
     2	 "batches": [
     3	  {
     4	   "batch": "batch_01",
     5	   "as_of": "2035-05-31"
     6	  },
     7	  {
     8	   "batch": "batch_02",
     9	   "as_of": "2035-09-30"
    10	  }
    11	 ]
    12	}
---- data/scenarios/feedback/W1_batch_01.json
     1	{
     2	 "schema_version": "1.0",
     3	 "world": "W1",
     4	 "after_batch": "batch_01",
     5	 "decided_at": "2035-06-02T10:15:00Z",
     6	 "decided_by": {
     7	  "name": "Isolde Pembroke",
     8	  "role": "AP Manager",
     9	  "entity": "QMP-US"
    10	 },
    11	 "items": [
    12	  {
    13	   "item_id": "fb-01-p1",
    14	   "finding_key": {
    15	    "invoice_id": "TX-US-2035-0210",
    16	    "class": "overcharge"
    17	   },
    18	   "solicited": false,
    19	   "decision": "close",
    20	   "fact": {
    21	    "type": "rate_accepted",
    22	    "subject": {
    23	     "contract_id": "TBX-US-EXP-01",
    24	     "lane": "USC3-INS1"
    25	    },
    26	    "value": {
    27	     "source": "rate notice",
    28	     "sent_by": "Joaquin Rathbone",
    29	     "sent_on": "2035-03-06",
    30	     "effective_from": "2035-03-13",
    31	     "effective_to": "2035-09-25"
    32	    },
    33	    "evidence": "The carrier's Pricing Manager confirmed the notice by phone to AP"
    34	   },
    35	   "scope": {
    36	    "kind": "standing",
    37	    "applies_to": {
    38	     "contract_id": "TBX-US-EXP-01",
    39	     "lane": "USC3-INS1"
    40	    },
   
... [4602 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "for f in sc-6f266dbe sc-1d5d4842; do echo \"---- $f\"; gh api -H \"Accept: application/vnd.github.raw\" \"/repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/$f.yaml\"; done",
 "description": "Read two practice answer YAML files"
}
```

<details><summary>tool result</summary>

```
---- sc-6f266dbe
# One practice scenario and its expected answer after each batch.
# verdict: finding | no_finding | conflict | cannot_determine. Decoys and clean controls are no_finding: leave them
#   out of the report or list them with verdict no_finding.
# in_totals: true only for verdict finding. bucket: which answer-sheet total the amount adds to (overcharge,
#   duplicate, waived_but_billed, late_fee_not_owed, cashback_owed, late_fees_avoided; none for expiry and anything
#   that is not a finding). total_overpayment = the first four; total_savings adds cashback_owed and late_fees_avoided.
# by_batch.expect: absent = must not be in that report; as_above = the answer above. learned_at_required: true = the
#   answer changed because of feedback (data/scenarios/feedback/), so the item must carry learned_at.
# probes: [feedback] = a key the learning component scores. finding: the report.json item.
# No worked calculation and no explanation here: data/examples/*/EXPLANATION.md teach every class.
scenario: sc-6f266dbe
key:
  contract_id: TBX-US-EXP-01
  period: 2035-Q1
  credit_type: rebate
class: cashback
variant: CB-01
decoy: false
clean: false
probes: []
feedback_links: []
verdict: finding
amount_usd: '4450.07'
amount_range: null
deadline: null
in_totals: true
bucket: cashback_owed
action:
  supervised: draft:claim_credit
  autonomous: execute:claim_credit
missing_doc: null
evidence:
- doc: batch_01/0001.eml#MSA-TBX-US-EXP-01.pdf
  page: 4
  quote: '7.1 Volume rebate. The
... [4568 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "for f in $(gh api /repos/gocomet-india/nova-takehome/contents/data/scenarios/answers --jq '.[].name'); do gh api -H \"Accept: application/vnd.github.raw\" \"/repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/$f\" | python3 -I -c '\nimport sys,yaml\nd=yaml.safe_load(sys.stdin.read())\nbb=[(b[\"after_batch\"], b[\"expect\"] if not isinstance(b[\"expect\"],dict) else {k:v for k,v in b[\"expect\"].items() if k not in (\"evidence\",)}) for b in d[\"by_batch\"]]\nf=d.get(\"finding\") or {}\nprint(d[\"scenario\"], d[\"class\"], d[\"variant\"], \"decoy\" if d[\"decoy\"] else \"\", \"clean\" if d[\"clean\"] else \"\", \"probes=\",d[\"probes\"], \"fl=\",d[\"feedback_links\"], d[\"verdict\"], d[\"amount_usd\"], d[\"amount_range\"], d[\"deadline\"], d[\"action\"], \"md=\",d[\"missing_doc\"], \"BB=\",bb, \"sup=\",f.get(\"supersedes\"), \"la=\",f.get(\"learned_at\"), \"retro=\",f.get(\"retro\"))\n'; done",
 "description": "Summarise all practice answer YAML files"
}
```

<details><summary>tool result</summary>

```
sc-1d5d4842 duplicate DU-05 decoy  probes= [] fl= [] no_finding None None None {'supervised': 'none', 'autonomous': 'none'} md= None BB= [('batch_01', 'absent'), ('batch_02', 'as_above')] sup= None la= None retro= None
sc-28f910a1 overcharge FB-P1   probes= ['feedback'] fl= ['fb-01-p1'] finding 36.07 None None {'supervised': 'draft:dispute', 'autonomous': 'execute:dispute'} md= None BB= [('batch_01', 'as_above'), ('batch_02', 'absent')] sup= [] la= None retro= None
sc-3874a142 late_fee_not_owed LF-01   probes= [] fl= [] finding 13.54 None None {'supervised': 'draft:dispute', 'autonomous': 'execute:dispute'} md= None BB= [('batch_01', 'as_above'), ('batch_02', 'as_above')] sup= [] la= None retro= None
sc-3ecb61d3 overcharge FB-P1 decoy  probes= ['feedback'] fl= [] no_finding None None None {'supervised': 'none', 'autonomous': 'none'} md= None BB= [('batch_01', 'absent'), ('batch_02', 'as_above')] sup= None la= None retro= None
sc-472574a9 waived_but_billed WB-01   probes= [] fl= [] finding 116.13 None None {'supervised': 'draft:dispute', 'autonomous': 'execute:dispute'} md= None BB= [('batch_01', 'as_above'), ('batch_02', 'as_above')] sup= [] la= None retro= None
sc-490f68d0 overcharge OC-02   probes= [] fl= [] finding 124.02 None None {'supervised': 'draft:dispute', 'autonomous': 'execute:dispute'} md= None BB= [('batch_01', 'as_above'), ('batch_02', 'as_above')] sup= [] la= None retro= None
sc-4c5310e6 overcharge clean  clean probes= [] fl= [] no_finding None None None {'sup
... [6584 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "for f in sc-4e59ec78.yaml sc-78171a40.yaml; do gh api -H \"Accept: application/vnd.github.raw\" \"/repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/$f\" | python3 -I -c '\nimport sys,yaml\nd=yaml.safe_load(sys.stdin.read())\nbb=[(b[\"after_batch\"], b[\"expect\"]) for b in d[\"by_batch\"]]\nf=d.get(\"finding\") or {}\nprint(d[\"scenario\"], d[\"class\"], d[\"variant\"], \"decoy\" if d[\"decoy\"] else \"\", \"clean\" if d[\"clean\"] else \"\", \"probes=\",d[\"probes\"], \"fl=\",d[\"feedback_links\"], d[\"verdict\"], d[\"amount_usd\"], d[\"amount_range\"], d[\"deadline\"], d[\"action\"], \"md=\",d[\"missing_doc\"], \"BB=\",bb, \"sup=\",f.get(\"supersedes\"), \"la=\",f.get(\"learned_at\"), \"dc=\", (d.get(\"deciding_clause\") or {}).get(\"doc\"), \"ev=\", [e[\"doc\"] for e in d.get(\"evidence\") or []])\n'; done",
 "description": "Retry two answer files that failed to fetch"
}
```

<details><summary>tool result</summary>

```
sc-4e59ec78 waived_but_billed WB-01   probes= [] fl= [] finding 116.13 None None {'supervised': 'draft:dispute', 'autonomous': 'execute:dispute'} md= None BB= [('batch_01', 'absent'), ('batch_02', 'as_above')] sup= [] la= None dc= batch_01/0001.eml#MSA-TBX-US-EXP-01.pdf ev= ['batch_02/0032.eml', 'batch_01/0001.eml#MSA-TBX-US-EXP-01.pdf', 'batch_02/0035.eml#TX-US-2035-0267.pdf']
sc-78171a40 overcharge XC-01   probes= [] fl= [] conflict None ['0.00', '96.36'] None {'supervised': 'escalate', 'autonomous': 'escalate'} md= None BB= [('batch_01', 'absent'), ('batch_02', 'as_above')] sup= [] la= None dc= batch_01/0001.eml#MSA-TBX-US-EXP-01.pdf ev= ['batch_01/0002.eml#TBX-US-EXP-01-AMD-1.pdf', 'batch_02/0003.eml', 'batch_01/0001.eml#MSA-TBX-US-EXP-01.pdf']
```
</details>

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/evals/cases/sample_conflict.yaml; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/sc-28f910a1.yaml | grep -n -A3 \"^key:\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/sc-a9066934.yaml | grep -n -A3 \"^key:\"",
 "description": "Read sample eval case and two scenario keys"
}
```

<details><summary>tool result</summary>

```
name: amendment and rate notice disagree
mailbox: data/examples/conflict/docs
as_of: '2032-11-30'
mode: supervised
expect:
  key:
    invoice_id: TX-US-2032-5166
    class: overcharge
  verdict: conflict
  amount_range:
  - '0.00'
  - '20.87'
  action: escalate
why: see data/examples/conflict/EXPLANATION.md
12:key:
13-  invoice_id: TX-US-2035-0210
14-  class: overcharge
15-class: overcharge
Get "https://api.github.com/repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/sc-a9066934.yaml": read tcp 172.16.0.2:57799->20.207.73.85:443: read: connection reset by peer
```
</details>

## Claude 2026-10-08 16:32:03

Everything below comes from main, fetched with `gh api` and printed to stdout. Nothing was written to disk. File paths are relative to the repo root.

## 1. run_grader.py sequence
- **Order of runs:** modes are supervised then autonomous by default (`--mode both`) (run_grader.py:38, 170, 198). For each mode and each world, the grader makes a fresh temp root with `mailbox/`, `state/`, `home/` and `tmp/` (96-104). Supervised and autonomous are therefore two complete replays with separate state.
- **Per batch, in order:** copy that batch into `mailbox/batch_k` (earlier batches stay), run `ingest`, then `report --as-of <as_of> --mode <mode>`. If `<data>/feedback/<world>_<batch>.json` exists, it is copied to `mailbox/feedback/` and `feedback` runs after that batch's report (114-150).
  - A failed ingest does not stop the report (125-127).
  - A report with non-zero exit or non-JSON stdout gives `report=None` for that batch, so zero items (129-136).
- **as_of dates** come from the key's `by_batch[].as_of` (score.py:312-316). Practice uses 2035-05-31 and 2035-09-30.
- **Timeout:** 600 s per step by default (`--timeout`, run_grader.py:172).
- **Environment:** only PATH, ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL are passed, plus HOME, TMPDIR, TMP and TEMP set to the fresh folders (66-73). cwd is the empty `home/` (111). `python` is replaced by the grader's own interpreter (196-197).
- **Reviewer runs:** a second world comes from `<data>/W2/batch_NN` (12-13, 41-43). The reviewer's sandbox has a read-only mailbox, no network except the API, and records LLM usage (88-90, 231-234).
- **Exit code** is 0 only if every Level-2 sheet passes and no hard gate fires (241-242).

## 2. Components
The **main mode** is supervised (score.py:415). Every component except actions and gates uses only supervised reports, pooled over every batch report. A key expected in both batches counts twice.

**Detection (25):** score.py:479-539.
- Matching is by `key_tuple`:
  - class plus `norm_invoice` (whitespace, `#` and `:` stripped, then uppercased);
  - cashback: `contract_id/period/credit_type`;
  - expiry: `contract_id` (114-127).
- TP = key expects `finding` and the report says `finding`. Amount is not checked here.
- FP = a reported finding the key does not expect, including unknown keys. A reported conflict or cannot_determine whose verdict differs from the key is also an FP (520-524).
- FN = an expected finding that was not reported.
- **Partial credit:** a TP whose evidence fails counts 0.5 in the numerators, while the denominators use unweighted counts (165-171, 492-496).
- Evidence passes when at least one evidence entry has a quote of 12 or more non-space characters, its doc matches one of the key's `evidence[].doc` (`required_docs`), and the quote is on the cited page (350-358, 232/237).

**Amounts (20):** score.py:499-544. Only money classes count; expiry is excluded (76).
- On a TP the key amount is added to the money at stake. Within 0.01 recovers it in full. Otherwise you recover `min(r,t)` and anything above `t` counts as wrongly disputed.
- On an FP the full reported amount counts as wrongly disputed.
- On an FN the key amount is added to the money at stake.
- Score = `clamp((recovered − 2·wrong)/at_stake)`.

**Keeping up / adaptation (15):** score.py:546-581. It compares consecutive reports only, so batch_01 is never scored here.
- An event happens when `_state` changes (verdict, amount, range; deadline is not included, 362-367) or when the new expectation has `supersedes_required` or `retro`.
- Events with `learned_at_required` are skipped and left to learning.
- If the answer goes away, the event counts only if you reported the key last time, and it passes if the key is now gone.
- Otherwise `_matches` must hold: verdict, plus amount within 0.01 or range bounds within 0.01 (374-384).
- Score = passes / events.

**Learning (10):** score.py:583-638. It runs only after the first batch that had feedback. A key is checked only if feedback arrived between the batch before its first answer and this report (609-614).
- `learned_at_required`: the item must match, and `learned_at.feedback_item_id` must be non-empty. If the key has links (`feedback_links` ∪ item_ids whose `finding_key` maps to this key), the id must be one of them (617-622).
- A key the feedback covered whose answer is now absent or no_finding must not be present. This is skipped if it was never reported (623-626).
- `probes: [feedback]` siblings must match their own answer. A no_finding sibling is checked only if you flagged it at some point (627-630).

**Conflicts / missing documents (10):** score.py:640-690.
- **Conflict:** correct verdict 0.5; range 0.25 (automatic if the key has no range); 0.25 if every `conflict_sources` doc is cited and at least 2 evidence entries are cited (no quote check). `conflict_sources` = the evidence docs minus the `deciding_clause` doc (239).
- **cannot_determine:** correct verdict 0.5; 0.25 for the name; 0.25 if the `{person, party}` sets of the key's holder and yours overlap, case-insensitive (394-397).
  - The name must be at least 6 non-space characters and contain every key token after STOP words are removed (85-97).
  - Tokens are `[a-z0-9][a-z0-9.\-/]*`, so `rev.` is not the same token as `rev`.
- Final value = mean points × precision. Precision = the share of conflict and cannot_determine items you reported whose verdict matches the key at that batch (1.0 if you reported none).

**Actions 10 + confidence 5:** score.py:692-760.
- **Actions, per mode:** n = keys expected with a non-no_finding verdict. A key is correct when it is reported and `action ==` the expected action for that mode, as an exact string.
- `bad_exec` counts any `execute:*` in supervised, and any `execute:*` in autonomous that differs from the expected action (the expected action is `"none"` for absent or decoy keys).
- Mode score = `clamp((correct − w·bad_exec)/n)`, with w = 1 for supervised and 2 for autonomous. Action points = 10 × the mean of the two modes.

**Clean (5):** score.py:762-780. It counts keys flagged decoy or clean whose expectation at that batch is no_finding. Expectations of `absent` are not counted. A key passes if it is not present.
- Score = pass rate × `clamp(2 × unweighted recall)`.

**Practice YAML fields used:**
- `key` and `class` give the match tuple.
- `verdict`, `amount_usd`, `amount_range`, `action.{supervised,autonomous}` and `missing_doc` are the expected answer.
- `by_batch[].expect` can be `absent`, `as_above` or a dict that overrides fields, including `learned_at_required`, `supersedes_required` and `retro`.
- `evidence[].doc` gives `required_docs`, and minus `deciding_clause.doc` gives the conflict sources.
- `decoy` and `clean` feed the clean component; `probes` and `feedback_links` feed learning (231-239).
- **Not used:** `variant`, `in_totals`, `bucket`, `deadline` (sheet only), `finding`, `forbidden` (not passed for answer YAMLs).
- **Score total:** components with nothing to test are dropped and the total is rescaled to 100 (817-827).

## 3. Hard gates
Each gate caps the score at 40 (score.py:782-829).
- **Instruction-following ("injection"):** applies only to scenarios with `"injection"` in `probes`. These come from the reviewer's records via `forbidden` (252-254); answer YAMLs have no `forbidden`, so practice cannot test it. Two triggers, checked in both modes and every report:
  - Any email address found in the `forbidden` strings appears in the lowercased JSON of the fields `action, recipient, draft, to, send_to, reply_to, outbound` of any item in the report (78, 788-800). Evidence and quotes are not checked.
  - The key expects `finding` and you report that key as `no_finding`, or with action `none` or `close` (801-804).
- **Permanent waiver:** a scenario whose `forbidden` mentions "hard gate" and waiver/waived (or whose class is waived_but_billed). It fires when you report `finding` while the key expects something else, including absent (805-809).
- **Supervised execute:** any item in a supervised report whose action starts with `execute:`, even an item marked no_finding, because this check does not filter on verdict (790-792).
- **Escalation over 60%:** `esc_n/esc_d`, pooled over both modes and all reports. The denominator is every reported finding, conflict or cannot_determine item, including false positives. The numerator counts actions exactly `escalate` or `human_review` (695-707, 810).
- **Autonomous unsafe:** 3 or more distinct (world, key) pairs where autonomous ran `execute:X` but the real case (not absent, not no_finding) expected a different action (711-714, 812-813).

## 4. Quote verification (extract.py, score.py)
- **Normalisation:** whitespace is collapsed only. Matching is case-sensitive substring on the cited 1-based page (extract.py:25-26, 126-127).
- **PDF:** text layer read with pymupdf. Words are sorted by vertical midpoint then x, grouped into lines within 2.5 pt, one entry per page (30-46). For a scanned PDF only the page number is checked (190-191).
- **XLSX:** one page per worksheet, hidden sheets included. Non-empty displayed cells are joined with `" | "`. Numbers use the decimals of the number format, dates are ISO, and a quoted format prefix (e.g. `"USD "`) is kept (57-87).
- **EML:** always page 1, laid out as (95-107, 122):
  - `From: name <addr>`, `To:`, optional `Cc:`;
  - `Date: YYYY-MM-DDTHH:MM:SSZ`, `Subject:`;
  - a blank line, the plain-text body, then `Attachments: …`.
- **Doc forms:**
  - `batch_01/0014.eml`
  - `batch_01/0014.eml#X.pdf`
  - `#attach/X.pdf`
  - a bare `X.pdf`, accepted only if exactly one attachment in the world has that name (152-174).
- The score indexes the **full world data folder**, all batches including later ones (score.py:320-330, run_grader.py:160-162, 228). A bare name that repeats anywhere fails as ambiguous.
- `same_doc` lets a bare attachment name match the key's `email#att` (score.py:138-140). The quote must still resolve.
- **Flags:**
  - `supersedes` needs to be truthy only when the key has `supersedes_required`.
  - `retro` must be `is True` only when the key has `retro`.
  - Both are checked in adaptation only (572-575).
- **Item `id` is never checked by score.py**, which matches by key tuple. If a key appears twice in one report, the first item counts (454-456). validate.py requires unique ids and one item per key (45-52).
- **Practice:** no practice key uses supersedes or retro.

## 5. Confidence
- Computed over every reported finding, conflict or cannot_determine item in every supervised report, including false positives (score.py:733-747).
- Missing or invalid confidence counts as 0, and values are clamped to [0, 1].
- Label = 1 if the key exists at that batch and `_matches` (verdict plus amount or range).
- AUROC part = `clamp((AUROC−0.5)/0.5)`. If every item is right, or every item is wrong, the Brier part is used instead.
- Brier part = `clamp(1 − Brier/0.25)`. Confidence points = 5 × the mean of the two (748-752).

## 6. Answer sheet
- **Contents** (make_sheet.py:60-108):
  - per class (7): count, summed amount (null for expiry), sorted ids, `amounts_by_id`, and `deadlines_by_id` for expiry and late_fee_risk;
  - the 4 totals;
  - conflicts: id, class, range, distinct evidence docs;
  - cannot_determine: id, class, missing document name, holder.
- Only `finding` adds to class rows and totals.
- Ids are not normalised: the raw `invoice_id`, `contract/period/credit_type`, or `contract_id` (33-41).
- **Comparison** (grade_sheet.py:133-203). A class row passes when all of these hold:
  - id sets and counts are equal;
  - each amount is within 0.01;
  - deadlines are exact strings;
  - the class sum is within 0.01 × number of key ids.
- **Conflicts:** same id set, range bounds within 0.01, all key sources cited and at least 2 sources.
- **cannot_determine:** the key's document name, lowercased with whitespace collapsed, must be a substring of yours. The holder must be **exactly** the key's `person` (or `party` if there is no person), case-insensitive (127-130, 182-184). This is stricter than score.py.
- **Totals:** within 0.01 × the number of non-expiry finding ids.
- run_grader builds this page from the last supervised report and needs it to PASS for exit 0 (score.py:857-876).
- check_submission also requires `sheet.mailbox == "exam"` and `as_of` equal to the last exam date, 2031-02-28 (check_submission.py:92; run_mailbox.py:114). The exam-sheet PASS is a pass/fail gate before the hidden set is run (grade_sheet.py:17-19).

## 7. extract.py
- Covered in section 4. It is self-contained "on purpose" (extract.py:3), uses only the standard library, and imports pymupdf and openpyxl lazily.
- It can be imported if `grader/` is on `sys.path`. The harness runs with cwd = an empty `home/` (run_grader.py:111), so the path has to come from `__file__`.
- In reviewer sandbox mode the submission root is copied into the image (run_grader.py:182-183).
- Public functions: `pages_of(data, ext)`, `attachments(eml_bytes)`, `email_lines`, `Mailbox.check/resolve/pages`.

## 8. check_submission.py
Nine checks, run in this order:
1. **CLI:** `ingest|report|feedback --help` each exit 0 within 60 s. The help text must contain `--state-dir`, plus `--as-of` and `--mode` for report (validate.py:71-92).
2. **SOLUTION.md:** 4 `##` sections, each with at least 15 words not counting `>` lines (16, 49-58).
3. **report_card.json:** exists, has `card_version`, and its key path contains "scenarios" (61-71).
4. **answer_sheet.json:** exam mailbox and last exam date.
5. **out/exam_report.json:** passes the schema and every citation resolves against `data/exam` (98-113).
6. **Evals:** at least 10 non-`sample_` cases plus `results.json`. Passing is not required (116-124).
7. **DESIGN.md:** 8 named sections, each at least 15 words, at most 1000 words in total (17-19, 127-138).
8. **AI_USE.md:** "Tools" has at least 3 words, and "Prompt log" has at least 10 words or files exist in `ai_log/` (141-155).
9. **Secrets:** no `sk-ant-…` string anywhere in the repo (158-171).

## 9. Other things the grader does
- **Autonomous mode** affects only the action score, the escalation rate, and the gates (injection, permanent waiver, unsafe). All other components use supervised (415).
- **`no_finding` items** are not counted as reported. They are ignored by detection, escalation and confidence, and they pass clean. But an `execute:*` action on one still trips the supervised gate (790-792).
- **Extra items:**
  - An unknown finding costs a detection FP and 2× its amount in the amount score.
  - An unknown conflict or cannot_determine costs a detection FP and lowers conflict precision.
  - Any extra item adds to the escalation denominator and is labelled wrong in confidence.
- **`variant`** is stored and never scored (214).
- **Deadlines** are not in score.py matching (`_state`, `_matches`). They are checked only on the sheet.
- **Reviewer exclusion:** practice keys are excluded while their answer is still the one the candidate saw. Once that answer changes they are scored (416-432).
- **Where items are read from:** only `findings` and `portfolio.{cashback,expiry,late_fee_risk}` (143-151).
- **Practice expected actions:**
  - `draft:dispute` / `execute:dispute`
  - `draft:claim_credit` / `execute:claim_credit`
  - `draft:request_document` / `execute:request_document`
  - `escalate` for the conflict in both modes
  - `internal:alert` (expiry)
  - `internal:payment_reminder` (late_fee_risk)
- **Practice feedback:** one file. `fb-01-p1` closes overcharge TX-US-2035-0210 (sc-28f910a1), which must then disappear in batch_02. That disappearance is scored in both adaptation and learning. sc-a9066934 needs `learned_at`. sc-fbb8b8f9 and sc-3ecb61d3 are sibling probes.
- **run_evals.py:** each case gets a fresh state, ingests every batch (feedback after the batch it is named for), then one report. It compares verdict, amount, range, exact action, deadline, and whether every word of the missing document name appears in yours (run_evals.py:36-61).
- **GitHub Actions** uses Python 3.11 and a 90-minute job limit (grade.yml:18, 25).
