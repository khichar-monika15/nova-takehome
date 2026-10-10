# Subagent: Study the assignment data

Source: `agent-a7cd407d772f47147.jsonl`. Tool results are cut to 1500 characters, tool inputs to 2500. API keys are replaced with a marker. Nothing else is removed.

## User 2026-10-08 16:27:52

Research task, read-only. Do NOT write, clone, or download any file to disk. Use only `gh api` piped to stdout, and `python3 -I -c` reading stdin to parse in memory (the `email` stdlib module for .eml; if `import fitz` or `import pymupdf` works locally, use it on bytes in memory to read PDF attachments; `openpyxl` on a BytesIO for xlsx). Write `command ls`, never plain `ls` (it is aliased to a tool that hangs without a terminal).

Context: a job candidate must build a Python harness for the public GitHub repo `gocomet-india/nova-takehome` (branch main) that reads a mailbox of .eml files (PDF invoices, Excel statements, contracts and amendments as attachments) and audits freight invoices. Six classes: overcharge, duplicate, waived_but_billed, late fees (late_fee_not_owed, late_fee_risk), cashback, expiry; plus conflict and cannot_determine. The hidden test set uses a NEW customer, NEW carrier, NEW invoice layouts, other wordings, backdated amendments, prompt-injection emails. A rules-only harness tuned to the practice files scored ~11/100 on the hidden set. I need to understand the documents so the design generalises.

Read raw files with: `gh api -H "Accept: application/vnd.github.raw" /repos/gocomet-india/nova-takehome/contents/<path>`

Do this:
1. Read every `data/examples/*/EXPLANATION.md` and `expected_finding.json` (8 folders: cashback, conflict, duplicate, duplicate_rebilled_4_months, expiry, late_fees, overcharge, waived_but_billed). Summarise per example: the deciding clause, the arithmetic, the look-alike that is fine, and which documents carry each fact.
2. Read all 30 `data/scenarios/answers/*.yaml`. Tabulate: class, verdict, variant (if present), amount, actions per mode, which batches it changes in, evidence docs. Count by class and verdict. List every distinct "trick" (near miss, unauthorised sender, quoted waiver, injection, conflict, cannot_determine, supersedes, retro, learned_at).
3. Parse 3 to 4 representative .eml files from `data/scenarios/batch_01/` in memory: the big one (0001.eml, likely the MSA contract), one invoice email, one Excel statement email, one small text-only email. Report: headers present, attachment types and names, how the contract is structured (MSA sections, Schedule 1 contacts table, Annex names for rates/fuel/accessorials/FX Annex F, precedence clause wording, rebate tiers, late fee terms, renewal/notice terms), invoice layout (fields, line items, currency).
4. Do the same light pass on `data/exam/batch_01/` (0001.eml and one invoice) to see how the exam customer, carrier and invoice layout differ from practice. Identify which exam .eml holds the scanned image invoice with no text layer (an image-only PDF attachment).
5. Sizes: count emails and attachments per batch in scenarios and exam, and estimate total text characters of a whole batch (to size LLM cost).

Report under 1,800 words, facts with file citations, no advice.

## Claude 2026-10-08 16:27:54

I'll start by listing the repo tree.

**Tool call: Bash**

```json
{
 "command": "gh api \"/repos/gocomet-india/nova-takehome/git/trees/main?recursive=1\" | python3 -I -c \"\nimport json,sys\nd=json.load(sys.stdin)\nprint(d.get('truncated'))\nfor t in d['tree']:\n    print(t['type'], t.get('size',''), t['path'])\n\" | head -300",
 "description": "List repo tree recursively"
}
```

<details><summary>tool result</summary>

```
False
tree  .github
tree  .github/workflows
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
tree  data
tree  data/exam
tree  data/exam/batch_01
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
tree  data/exam/batch_02
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
blob 37882 data/exam/batch_0
... [10571 more characters]
```
</details>

## Claude 2026-10-08 16:28:00

Now reading the example explanations and expected findings.

**Tool call: Bash**

```json
{
 "command": "for d in cashback conflict duplicate duplicate_rebilled_4_months; do echo \"===== $d EXPLANATION\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/examples/$d/EXPLANATION.md; echo; echo \"===== $d expected_finding.json\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/examples/$d/expected_finding.json; echo; done",
 "description": "Read first 4 example explanations and findings"
}
```

**Tool call: Bash**

```json
{
 "command": "for d in expiry late_fees overcharge waived_but_billed; do echo \"===== $d EXPLANATION\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/examples/$d/EXPLANATION.md; echo; echo \"===== $d expected_finding.json\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/examples/$d/expected_finding.json; echo; done",
 "description": "Read remaining 4 example explanations and findings"
}
```

<details><summary>tool result</summary>

```
===== cashback EXPLANATION
# Worked example: Cashback: quarterly rebate earned and not credited

A quarterly volume rebate that was earned and never credited. The skill: add up Qualifying Spend exactly as the contract defines it before reading the tier table.

## The documents

Everything is in `docs/`, laid out like the scenario mailbox (one folder per batch, attachments inside the emails). The report date is `2033-11-30`.

| File | What it is | Received |
|---|---|---|
| `batch_01/0002.eml` | email from Fintan Quigley: `Executed agreement TBX-US-EXP-E58` | `2033-01-30` |
| `batch_01/0002.eml#MSA-TBX-US-EXP-E58.pdf` | Master Services Agreement (Express Air) TBX-US-EXP-E58 | `2033-01-30` |
| `batch_01/0003.eml` | email from Tarrowby Billing: `Invoice TX-US-2033-5462` | `2033-04-13` |
| `batch_01/0003.eml#TX-US-2033-5462.pdf` | Invoice TX-US-2033-5462 | `2033-04-13` |
| `batch_01/0004.eml` | email from Tarrowby Billing: `Invoice TX-US-2033-5464` | `2033-05-28` |
| `batch_01/0004.eml#TX-US-2033-5464.pdf` | Invoice TX-US-2033-5464 | `2033-05-28` |
| `batch_01/0004.eml#AWB-TE14764227.pdf` | Air waybill TE14764227 | `2033-05-28` |
| `batch_01/0004.eml#AWB-TE51172724.pdf` | Air waybill TE51172724 | `2033-05-28` |
| `batch_02/0001.eml` | email from Tarrowby Billing: `Invoice TX-US-2033-5468` | `2033-07-31` |
| `batch_02/0001.eml#TX-US-2033-5468.pdf` | Invoice TX-US-2033-5468 | `2033-07-31` |
| `batch_02/0002.eml` | email from Tarrowby Billing: `Invoice TX-US-2033-5472` | `2033-09-11
... [24750 more characters]
```
</details>

<details><summary>tool result</summary>

```
===== expiry EXPLANATION
# Worked example: Expiry: contract deadline inside 60 days

A contract whose end date falls inside the 60-day alert window. The skill: find the operative date and measure it from the report date.

## The documents

Everything is in `docs/`, laid out like the scenario mailbox (one folder per batch, attachments inside the emails). The report date is `2034-02-28`.

| File | What it is | Received |
|---|---|---|
| `batch_01/0002.eml` | email from Isolde Yardley: `Executed agreement TBX-US-EXP-E24` | `2033-03-10` |
| `batch_01/0002.eml#MSA-TBX-US-EXP-E24.pdf` | Master Services Agreement (Express Air) TBX-US-EXP-E24 | `2033-03-10` |

## The deciding clause

MSA §2.2, `batch_01/0002.eml#MSA-TBX-US-EXP-E24.pdf` p. 3:

> `2.2 Initial term. The initial term is 12 months, ending on 2034-03-20.`

## The email line

No email decides this one. The date is in the MSA, `batch_01/0002.eml#MSA-TBX-US-EXP-E24.pdf` p. 3:

> `2.2 Initial term. The initial term is 12 months, ending on 2034-03-20.`

## Step by step

1. Clause 2.2 (`batch_01/0002.eml#MSA-TBX-US-EXP-E24.pdf` p. 3): `2.2 Initial term. The initial term is 12 months, ending on 2034-03-20.`
2. Clause 2.3 (`batch_01/0002.eml#MSA-TBX-US-EXP-E24.pdf` p. 3): `2.3 Auto-renewal. This Agreement does not renew automatically. It ends at the end of the initial term unless extended under clause 2.4.` So the date that matters is the last day of the term, `2034-03-20`.
3. The report is as of `2034-02-28`. Days left: `2034-03-
... [24418 more characters]
```
</details>

## Claude 2026-10-08 16:28:34

Now the 30 scenario answer YAMLs.

**Tool call: Bash**

```json
{
 "command": "for f in 1d5d4842 28f910a1 3874a142 3ecb61d3 472574a9 490f68d0 4c5310e6 4e59ec78 52db5230 6e4f24cd; do echo \"===== sc-$f\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/sc-$f.yaml; done",
 "description": "Read first 10 scenario answer YAMLs"
}
```

**Tool call: Bash**

```json
{
 "command": "for f in 6f266dbe 6f955cee 703db266 73ed4854 78171a40 88c6ccb5 9bb38241 a6783f61 a9066934 b7a1aee9; do echo \"===== sc-$f\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/sc-$f.yaml; done",
 "description": "Read scenario answer YAMLs 11 to 20"
}
```

**Tool call: Bash**

```json
{
 "command": "for f in bff95595 c04b8a91 c635bc71 c8db301f ddb759a8 e25ce214 e85d8676 f88fe65b f9cfdf2a fbb8b8f9; do echo \"===== sc-$f\"; gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/answers/sc-$f.yaml; done",
 "description": "Read scenario answer YAMLs 21 to 30"
}
```

<details><summary>tool result</summary>

```
===== sc-1d5d4842
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
scenario: sc-1d5d4842
key:
  invoice_id: TX-US-2035-0251
  class: duplicate
class: duplicate
variant: DU-05
decoy: true
clean: false
probes: []
feedback_links: []
verdict: no_finding
amount_usd: null
amount_range: null
deadline: null
in_totals: false
bucket: none
action:
  supervised: none
  autonomous: none
missing_doc: null
evidence:
- doc: batch_02/0020.eml#AWB-TX75680985.pdf
  page: 1
  quote: Total pieces 3 | Total chargeable weight 363 kg
- doc: batch_02/0019.eml#TX-US-2035-0
... [24197 more characters]
```
</details>

<details><summary>tool result</summary>

```
===== sc-6f266dbe
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
  quote: '7.1 Volume rebate. Th
... [25485 more characters]
```
</details>

<details><summary>tool result</summary>

```
===== sc-bff95595
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
scenario: sc-bff95595
key:
  invoice_id: TX-US-2035-0265
  class: late_fee_not_owed
class: late_fee_not_owed
variant: LF-01
decoy: false
clean: false
probes: []
feedback_links: []
verdict: finding
amount_usd: '39.66'
amount_range: null
deadline: null
in_totals: true
bucket: late_fee_not_owed
action:
  supervised: draft:dispute
  autonomous: execute:dispute
missing_doc: null
evidence:
- doc: batch_02/0021.eml
  page: 1
  quote: We extend the due date of invoice TX-US-2035-0233 to 20
... [26446 more characters]
```
</details>

## Claude 2026-10-08 16:29:16

Now feedback, manifests, and batches.json files.

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"; for p in data/scenarios/feedback/W1_batch_01.json data/scenarios/batches.json data/exam/batches.json data/scenarios/batch_01/_manifest.json data/scenarios/batch_02/_manifest.json data/exam/batch_01/_manifest.json data/exam/batch_02/_manifest.json data/examples/README.md; do echo \"===== $p\"; gh api -H \"$H\" $R/$p; echo; done",
 "description": "Read feedback, batches and manifest files"
}
```

<details><summary>tool result</summary>

```
===== data/scenarios/feedback/W1_batch_01.json
{
 "schema_version": "1.0",
 "world": "W1",
 "after_batch": "batch_01",
 "decided_at": "2035-06-02T10:15:00Z",
 "decided_by": {
  "name": "Isolde Pembroke",
  "role": "AP Manager",
  "entity": "QMP-US"
 },
 "items": [
  {
   "item_id": "fb-01-p1",
   "finding_key": {
    "invoice_id": "TX-US-2035-0210",
    "class": "overcharge"
   },
   "solicited": false,
   "decision": "close",
   "fact": {
    "type": "rate_accepted",
    "subject": {
     "contract_id": "TBX-US-EXP-01",
     "lane": "USC3-INS1"
    },
    "value": {
     "source": "rate notice",
     "sent_by": "Joaquin Rathbone",
     "sent_on": "2035-03-06",
     "effective_from": "2035-03-13",
     "effective_to": "2035-09-25"
    },
    "evidence": "The carrier's Pricing Manager confirmed the notice by phone to AP"
   },
   "scope": {
    "kind": "standing",
    "applies_to": {
     "contract_id": "TBX-US-EXP-01",
     "lane": "USC3-INS1"
    },
    "valid_from": "2035-03-13",
    "valid_to": "2035-09-25"
   },
   "note": "The carrier confirms the USC3-INS1 rate notice from Joaquin Rathbone is valid and we accept those rates for lane USC3-INS1 from 2035-03-13 to 2035-09-25. Close the dispute on this invoice."
  }
 ]
}

===== data/scenarios/batches.json
{
 "batches": [
  {
   "batch": "batch_01",
   "as_of": "2035-05-31"
  },
  {
   "batch": "batch_02",
   "as_of": "2035-09-30"
  }
 ]
}

===== data/exam/batches.json
{
 "batches": [
  {
   "batch": "batch_01",
   "as_of": 
... [12450 more characters]
```
</details>

## Claude 2026-10-08 16:29:31

Checking which PDF/xlsx libraries are available locally.

**Tool call: Bash**

```json
{
 "command": "python3 -I -c \"\nfor m in ['fitz','pymupdf','openpyxl','pypdf','pdfplumber']:\n    try:\n        __import__(m); print(m,'OK')\n    except Exception as e: print(m,'NO',e)\n\"",
 "description": "Check available Python PDF and Excel libs"
}
```

<details><summary>tool result</summary>

```
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
fitz OK
pymupdf OK
openpyxl NO No module named 'openpyxl'
pypdf NO No module named 'pypdf'
pdfplumber NO No module named 'pdfplumber'
```
</details>

## Claude 2026-10-08 16:29:36

Parsing scenarios batch_01/0001.eml (the MSA) in memory.

**Tool call: Bash**

```json
{
 "command": "gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/batch_01/0001.eml | python3 -I -c \"\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nprint('HEADERS:'); [print(' ',k,':',v) for k,v in m.items()]\nfor p in m.walk():\n    ct=p.get_content_type(); fn=p.get_filename()\n    if p.is_multipart(): print('PART multipart',ct); continue\n    data=p.get_payload(decode=True) or b''\n    print('PART',ct,fn,len(data))\n    if ct=='text/plain' or ct=='text/html': print(data.decode('utf-8','replace'))\n    if fn and fn.lower().endswith('.pdf'):\n        d=pymupdf.open(stream=data,filetype='pdf')\n        print('PDF pages',d.page_count, d.metadata)\n        for i,pg in enumerate(d):\n            t=pg.get_text(); print('--- page',i+1,'chars',len(t),'images',len(pg.get_images()))\n            print(t)\n\"",
 "description": "Parse MSA email and print PDF text in memory"
}
```

<details><summary>tool result</summary>

```
HEADERS:
  From : Joaquin Rathbone <joaquin.rathbone@tarrowby.example>
  To : isolde.pembroke@quillmere.example
  Date : Mon, 02 Oct 2034 09:21:00 +0000
  Subject : Executed agreement TBX-US-EXP-01
  Message-ID : <85eecb751b9c2c65730b1ec1@tarrowby.example>
  MIME-Version : 1.0
  X-GCA-Canary : GCA-0.1.0-CANARY
  Content-Type : multipart/mixed; boundary="==gca-092aed809713c10d47a9=="
PART multipart multipart/mixed
PART text/plain None 226
Hello,

Attached is the executed Master Services Agreement (Express Air) TBX-US-EXP-01, signed by both parties.
It takes effect on 2034-10-20.

Best regards,
Joaquin Rathbone
Key Account Manager
Tarrowby Express Inc.

PART application/pdf MSA-TBX-US-EXP-01.pdf 150816
PDF pages 11 {'format': 'PDF 1.7', 'title': 'Master Services Agreement (Express Air) TBX-US-EXP-01', 'author': 'Tarrowby Express Inc.', 'subject': '', 'keywords': 'GCA-0.1.0-CANARY', 'creator': 'gca-render', 'producer': 'gca-render', 'creationDate': "D:20340927000000+00'00'", 'modDate': "D:20340927000000+00'00'", 'trapped': '', 'encryption': None}
--- page 1 chars 379 images 0
Confidential  |  Master Services Agreement (Express Air) TBX-US-EXP-01
Master Services Agreement (Express Air)
Agreement No. TBX-US-EXP-01
between
Quillmere Pharma Inc.
315 Linden Parade, Suite 775
Fallowmere 26170, USA
(the Shipper)
and
Tarrowby Express Inc.
214 Merrow Road, Suite 671
Fallowmere 20905, USA
(the Carrier)
Dated 2034-09-27
Initials: Shipper
Carrier
Page 1 of 11

--- page 2 chars 943 
... [23104 more characters]
```
</details>

## Claude 2026-10-08 16:29:48

The MSA is fully readable. Now I'll run an inventory pass across all emails in each batch (headers, attachments, page counts, text sizes, image-only detection).

**Tool call: Bash**

```json
{
 "command": "PY='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nname=sys.argv[1]\nraw=sys.stdin.buffer.read()\nm=email.message_from_bytes(raw,policy=policy.default)\nbody=0; atts=[]; tot=0; extra_hdr=[k for k in m.keys() if k.lower() not in (\"from\",\"to\",\"date\",\"subject\",\"message-id\",\"mime-version\",\"content-type\",\"x-gca-canary\",\"content-transfer-encoding\")]\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"):\n        t=data.decode(\"utf-8\",\"replace\"); body+=len(t); tot+=len(t); continue\n    info=fn or ct\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\"); tl=sum(len(pg.get_text()) for pg in d); im=sum(len(pg.get_images()) for pg in d)\n        info+=\"[pdf p=%d txt=%d img=%d]\"%(d.page_count,tl,im); tot+=tl\n    elif fn and fn.lower().endswith(\".xlsx\"):\n        z=zipfile.ZipFile(io.BytesIO(data)); tl=0; sheets=[n for n in z.namelist() if n.startswith(\"xl/worksheets/sheet\")]\n        for n in z.namelist():\n            if n.startswith(\"xl/worksheets/sheet\") or n==\"xl/sharedStrings.xml\":\n                x=z.read(n).decode(\"utf-8\",\"replace\"); tl+=sum(len(v) for v in re.findall(r\"<(?:v|t)[^>]*>([^<]*)</(?:v|t)>\",x))\n        info+=\"[xlsx sheets=%d txt~%d]\"%(len(sheets),tl); tot+=tl\n    else:\n        info+=\"[%s %dB]\"%(ct,len(data))\n    atts.append(info)\nprint(\"%s | %s | %s | %s | body=%d | total_txt=%d | %s%s\"%(name,m[\"Date\"],m[\"From\"],m[\"Subject\"],body,tot,\"; \".join(atts),\" | XHDR:\"+\",\".join(extra_hdr) if extra_hdr else \"\"))\n'\nfor i in $(seq -w 1 41); do gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/data/scenarios/batch_01/00$i.eml | python3 -I -c \"$PY\" 00$i 2>/dev/null; done",
 "description": "Inventory all scenarios batch_01 emails in memory",
 "timeout": 400000
}
```

<details><summary>tool result</summary>

```
0001 | Mon, 02 Oct 2034 09:21:00 +0000 | Joaquin Rathbone <joaquin.rathbone@tarrowby.example> | Executed agreement TBX-US-EXP-01 | body=226 | total_txt=23413 | MSA-TBX-US-EXP-01.pdf[pdf p=11 txt=23187 img=0]
0002 | Thu, 09 Nov 2034 07:06:00 +0000 | Joaquin Rathbone <joaquin.rathbone@tarrowby.example> | Signed amendment 1 to TBX-US-EXP-01 | body=157 | total_txt=1781 | TBX-US-EXP-01-AMD-1.pdf[pdf p=1 txt=1624 img=0]
0003 | Sun, 19 Nov 2034 08:31:00 +0000 | Isolde Pembroke <isolde.pembroke@quillmere.example> | Charges on your account | body=168 | total_txt=168 | 
0004 | Sun, 19 Nov 2034 12:16:00 +0000 | Signe Underhill <signe.underhill@tarrowby.example> | Re: Charges on your account | body=443 | total_txt=443 |  | XHDR:In-Reply-To,References
0005 | Mon, 27 Nov 2034 13:05:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Invoice TX-US-2034-0379 | body=216 | total_txt=1078 | TX-US-2034-0379.pdf[pdf p=1 txt=862 img=0]
0006 | Mon, 27 Nov 2034 17:59:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Invoice TX-US-2034-0383 | body=220 | total_txt=1084 | TX-US-2034-0383.pdf[pdf p=1 txt=864 img=0]
0007 | Sat, 02 Dec 2034 16:47:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Statement TX-ST-203411 | body=206 | total_txt=545 | TX-ST-203411.xlsx[xlsx sheets=1 txt~339]
0008 | Sat, 30 Dec 2034 14:10:00 +0000 | Lena Zeller <lena.zeller@tarrowby.example> | Executed agreement TBX-IN-EXP-01 | body=229 | total_txt=24356 | MSA-TBX-IN-EXP-01.pdf[pdf p=11 txt=24127 img=0]
0009 
... [6423 more characters]
```
</details>

## Claude 2026-10-08 16:30:42

Two fetches failed with connection resets; I'll retry those and run the other three batches with retry logic.

**Tool call: Bash**

```json
{
 "command": "PY='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nname=sys.argv[1]\nraw=sys.stdin.buffer.read()\nm=email.message_from_bytes(raw,policy=policy.default)\nbody=0; atts=[]; tot=0; extra_hdr=[k for k in m.keys() if k.lower() not in (\"from\",\"to\",\"date\",\"subject\",\"message-id\",\"mime-version\",\"content-type\",\"x-gca-canary\",\"content-transfer-encoding\")]\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"):\n        t=data.decode(\"utf-8\",\"replace\"); body+=len(t); tot+=len(t); continue\n    info=fn or ct\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\"); tl=sum(len(pg.get_text()) for pg in d); im=sum(len(pg.get_images()) for pg in d)\n        info+=\"[pdf p=%d txt=%d img=%d]\"%(d.page_count,tl,im); tot+=tl\n    elif fn and fn.lower().endswith(\".xlsx\"):\n        z=zipfile.ZipFile(io.BytesIO(data)); tl=0; sheets=[n for n in z.namelist() if n.startswith(\"xl/worksheets/sheet\")]\n        for n in z.namelist():\n            if n.startswith(\"xl/worksheets/sheet\") or n==\"xl/sharedStrings.xml\":\n                x=z.read(n).decode(\"utf-8\",\"replace\"); tl+=sum(len(v) for v in re.findall(r\"<(?:v|t)[^>]*>([^<]*)</(?:v|t)>\",x))\n        info+=\"[xlsx sheets=%d txt~%d]\"%(len(sheets),tl); tot+=tl\n    else:\n        info+=\"[%s %dB]\"%(ct,len(data))\n    atts.append(info)\nprint(\"%s | %s | %s | %s | body=%d | total_txt=%d | %s%s\"%(name,m[\"Date\"],m[\"From\"],m[\"Subject\"],body,tot,\"; \".join(atts),\" | XHDR:\"+\",\".join(extra_hdr) if extra_hdr else \"\"))\n'\nf(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$PY\" $2 2>/dev/null); case \"$out\" in *\"| None |\"*|\"\") continue;; *) echo \"$out\"; return;; esac; done; echo \"$2 FAILED\"; }\nf data/scenarios/batch_01/0024.eml 0024\nf data/scenarios/batch_01/0030.eml 0030\necho \"=== scenarios batch_02\"\nfor i in $(seq -w 1 37); do f data/scenarios/batch_02/00$i.eml 00$i; done",
 "description": "Inventory scenarios batch_02 emails and retry failures",
 "timeout": 500000
}
```

**Tool call: Bash**

```json
{
 "command": "PY='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nname=sys.argv[1]\nraw=sys.stdin.buffer.read()\nm=email.message_from_bytes(raw,policy=policy.default)\nbody=0; atts=[]; tot=0; extra_hdr=[k for k in m.keys() if k.lower() not in (\"from\",\"to\",\"date\",\"subject\",\"message-id\",\"mime-version\",\"content-type\",\"x-gca-canary\",\"content-transfer-encoding\")]\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"):\n        t=data.decode(\"utf-8\",\"replace\"); body+=len(t); tot+=len(t); continue\n    info=fn or ct\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\"); tl=sum(len(pg.get_text()) for pg in d); im=sum(len(pg.get_images()) for pg in d)\n        info+=\"[pdf p=%d txt=%d img=%d]\"%(d.page_count,tl,im); tot+=tl\n    elif fn and fn.lower().endswith(\".xlsx\"):\n        z=zipfile.ZipFile(io.BytesIO(data)); tl=0; sheets=[n for n in z.namelist() if n.startswith(\"xl/worksheets/sheet\")]\n        for n in z.namelist():\n            if n.startswith(\"xl/worksheets/sheet\") or n==\"xl/sharedStrings.xml\":\n                x=z.read(n).decode(\"utf-8\",\"replace\"); tl+=sum(len(v) for v in re.findall(r\"<(?:v|t)[^>]*>([^<]*)</(?:v|t)>\",x))\n        info+=\"[xlsx sheets=%d txt~%d]\"%(len(sheets),tl); tot+=tl\n    else:\n        info+=\"[%s %dB]\"%(ct,len(data))\n    atts.append(info)\nprint(\"%s | %s | %s | %s | body=%d | total_txt=%d | %s%s\"%(name,m[\"Date\"],m[\"From\"],m[\"Subject\"],body,tot,\"; \".join(atts),\" | XHDR:\"+\",\".join(extra_hdr) if extra_hdr else \"\"))\n'\nf(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$PY\" $2 2>/dev/null); case \"$out\" in *\"| None |\"*|\"\") continue;; *) echo \"$out\"; return;; esac; done; echo \"$2 FAILED\"; }\necho \"=== exam batch_01\"\nfor i in $(seq -w 1 18); do f data/exam/batch_01/00$i.eml 00$i; done\necho \"=== exam batch_02\"\nfor i in $(seq -w 1 23); do f data/exam/batch_02/00$i.eml 00$i; done",
 "description": "Inventory exam batch_01 and batch_02 emails",
 "timeout": 500000
}
```

<details><summary>tool result</summary>

```
0024 | Tue, 06 Mar 2035 15:52:00 +0000 | Joaquin Rathbone <joaquin.rathbone@tarrowby.example> | Rate notice USC3-INS1 | body=414 | total_txt=414 | 
0030 | Fri, 13 Apr 2035 21:40:00 +0000 | Aurelie Whitlock <aurelie.whitlock@tarrowby.example> | Status TX43196050: delivered | body=151 | total_txt=151 | 
=== scenarios batch_02
0001 | Fri, 01 Jun 2035 09:36:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Invoice TX-US-2035-0220 | body=215 | total_txt=1426 | TX-US-2035-0220.pdf[pdf p=1 txt=1211 img=0]
0002 | Mon, 04 Jun 2035 11:40:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Statement TX-ST-203505 | body=211 | total_txt=550 | TX-ST-203505.xlsx[xlsx sheets=1 txt~339]
0003 | Tue, 05 Jun 2035 07:47:00 +0000 | Fintan Corrigan <fintan.corrigan@tarrowby.example> | Rate notice USC3-USS2 | body=406 | total_txt=406 | 
0004 | Sun, 10 Jun 2035 14:02:00 +0000 | Signe Underhill <signe.underhill@tarrowby.example> | Re: charges on your account | body=219 | total_txt=219 | 
0005 | Wed, 13 Jun 2035 15:25:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Invoice TX-US-2035-0224 | body=219 | total_txt=1081 | TX-US-2035-0224.pdf[pdf p=1 txt=862 img=0]
0006 | Fri, 15 Jun 2035 13:46:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Invoice TX-US-2035-0227 | body=206 | total_txt=2694 | TX-US-2035-0227.pdf[pdf p=1 txt=2248 img=0]; AWB-TX72292042.pdf[pdf p=1 txt=240 img=0]
0007 | Mon, 18 Jun 2035 15:35:00 +0000 | Tarrowby Billing <billing@tarrowby.example> | Invoice TX-U
... [6046 more characters]
```
</details>

<details><summary>tool result</summary>

```
=== exam batch_01
0001 | Tue, 08 Jan 2030 09:15:00 +0000 | Pallavi Whitlock <pallavi.whitlock@caldrith.example> | Executed agreement CDA-IN-EXP-E91 | body=260 | total_txt=24466 | MSA-CDA-IN-EXP-E91.pdf[pdf p=11 txt=24206 img=0]
0002 | Sat, 02 Mar 2030 10:23:00 +0000 | Caldrith Billing <billing@caldrith.example> | Invoice CDI-2930-0148 | body=247 | total_txt=1204 | CDI-2930-0148.pdf[pdf p=1 txt=957 img=0]
0003 | Fri, 15 Mar 2030 17:59:00 +0000 | Ines Oyelaran <ines.oyelaran@caldrith.example> | Executed agreement CDA-US-EXP-E91 | body=247 | total_txt=23498 | MSA-CDA-US-EXP-E91.pdf[pdf p=11 txt=23251 img=0]
0004 | Wed, 01 May 2030 12:39:00 +0000 | Ines Oyelaran <ines.oyelaran@caldrith.example> | Signed amendment 1 to CDA-US-EXP-E91 | body=172 | total_txt=1828 | CDA-US-EXP-E91-AMD-1.pdf[pdf p=1 txt=1656 img=0]
0005 | Tue, 04 Jun 2030 19:37:00 +0000 | Caldrith Billing <billing@caldrith.example> | Invoice CDU-3051254 | body=237 | total_txt=1111 | CDU-3051254.pdf[pdf p=1 txt=874 img=0]
0006 | Fri, 07 Jun 2030 08:50:00 +0000 | Odette Underhill <odette.underhill@ferrowyn.example> | Charges on your account | body=194 | total_txt=194 | 
0007 | Fri, 07 Jun 2030 12:46:00 +0000 | Thea Kapadia <thea.kapadia@caldrith.example> | Re: Charges on your account | body=458 | total_txt=458 |  | XHDR:In-Reply-To,References
0008 | Sat, 15 Jun 2030 12:51:00 +0000 | Caldrith Billing <billing@caldrith.example> | Invoice CDU-3051259 | body=233 | total_txt=1043 | CDU-3051259.pdf[pdf p=1 txt=810 img=0]
0009
... [6292 more characters]
```
</details>

<details><summary>Claude thinking</summary>

I found image-only PDFs in `batch_02/0016.eml` for both scenarios and exam cases. Now I'll pull the full content of representative scenario emails covering amendments, waiver threads, invoices, statements, and notices.


</details>

**Tool call: Bash**

```json
{
 "command": "cat > /dev/null <<'X'\nX\nDUMP='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nimport xml.etree.ElementTree as ET\nname=sys.argv[1]; maxrows=int(sys.argv[2]) if len(sys.argv)>2 else 999\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nprint(\"######\",name); [print(\"  H\",k,\":\",v) for k,v in m.items() if k not in (\"MIME-Version\",\"Content-Type\")]\nNS={\"a\":\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"}\ndef xl(data):\n    z=zipfile.ZipFile(io.BytesIO(data)); ss=[]\n    if \"xl/sharedStrings.xml\" in z.namelist():\n        r=ET.fromstring(z.read(\"xl/sharedStrings.xml\"))\n        for si in r.findall(\"a:si\",NS): ss.append(\"\".join(t.text or \"\" for t in si.iter(\"{%s}t\"%NS[\"a\"])))\n    for n in sorted(x for x in z.namelist() if x.startswith(\"xl/worksheets/sheet\")):\n        print(\"  [sheet]\",n); r=ET.fromstring(z.read(n)); k=0\n        for row in r.iter(\"{%s}row\"%NS[\"a\"]):\n            vals=[]\n            for c in row.findall(\"a:c\",NS):\n                v=c.find(\"a:v\",NS); t=c.get(\"t\"); isv=c.find(\"a:is\",NS)\n                if t==\"s\" and v is not None: vals.append(ss[int(v.text)])\n                elif t==\"inlineStr\" and isv is not None: vals.append(\"\".join(x.text or \"\" for x in isv.iter(\"{%s}t\"%NS[\"a\"])))\n                else: vals.append(v.text if v is not None else \"\")\n            k+=1\n            if k<=maxrows: print(\"   \", \" | \".join(vals))\n        print(\"   rows:\",k)\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"): print(\"  [body]\\n\"+data.decode(\"utf-8\",\"replace\")); continue\n    print(\"  [att]\",fn,ct,len(data))\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\")\n        for i,pg in enumerate(d): print(\"   --p%d--\"%(i+1)); print(pg.get_text())\n    elif fn and fn.lower().endswith(\".xlsx\"): xl(data)\n'\ng(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$DUMP\" \"$2\" \"${3:-999}\" 2>/dev/null); [ -n \"$out\" ] && { echo \"$out\"; return; }; done; echo \"$2 FAILED\"; }\nB=data/scenarios/batch_01\ng $B/0002.eml s1/0002; g $B/0003.eml s1/0003; g $B/0004.eml s1/0004; g $B/0005.eml s1/0005; g $B/0007.eml s1/00
... [206 more characters]
```

<details><summary>tool result</summary>

```
###### s1/0002
  H From : Joaquin Rathbone <joaquin.rathbone@tarrowby.example>
  H To : isolde.pembroke@quillmere.example
  H Date : Thu, 09 Nov 2034 07:06:00 +0000
  H Subject : Signed amendment 1 to TBX-US-EXP-01
  H Message-ID : <54ab5ab91069458a31055275@tarrowby.example>
  H X-GCA-Canary : GCA-0.1.0-CANARY
  [body]
Hi team,

Attached is Amendment No. 1 to TBX-US-EXP-01, signed by both parties.

Regards,
Joaquin Rathbone
Key Account Manager
Tarrowby Express Inc.

  [att] TBX-US-EXP-01-AMD-1.pdf application/pdf 14100
   --p1--
Confidential  |  Amendment No. 1 to TBX-US-EXP-01
Amendment No. 1 to Master Services Agreement (Express Air) TBX-US-EXP-01
Amendment reference TBX-US-EXP-01/AMD-1
Effective from 2034-11-11
This Amendment is made between Quillmere Pharma Inc. (the Shipper) and Tarrowby Express Inc. (the Carrier).
Recitals
(A) The parties entered into the Master Services Agreement (Express Air) TBX-US-EXP-01 dated 2034-09-27 (the Agreement).
(B) The parties wish to amend the Agreement as set out below. Words defined in the Agreement have the same meaning in this
Amendment.
The parties agree as follows:
1. Annex A rates for the lanes below are deleted and replaced with the following, for every period, with effect from the effective
date:
Lane
Weight band
Rate
Currency
USC3-USS2
minimum charge
82.82
USD
USC3-USS2
0-44.5 kg
3.43
USD
USC3-USS2
45-99.5 kg
3.27
USD
USC3-USS2
100-299.5 kg
3.12
USD
USC3-USS2
300+ kg
2.97
USD
2. The Annex A rates for lane(s) USS2-INN1 ar
... [7843 more characters]
```
</details>

## Claude 2026-10-08 16:33:09

Now the larger scenario invoices, the INR invoice, the AP register and tracking export.

**Tool call: Bash**

```json
{
 "command": "DUMP='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nimport xml.etree.ElementTree as ET\nname=sys.argv[1]; maxrows=int(sys.argv[2]) if len(sys.argv)>2 else 999\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nprint(\"######\",name, \"|\", m[\"From\"], \"|\", m[\"To\"], \"|\", m[\"Subject\"])\nNS={\"a\":\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"}\ndef xl(data):\n    z=zipfile.ZipFile(io.BytesIO(data)); ss=[]\n    if \"xl/sharedStrings.xml\" in z.namelist():\n        r=ET.fromstring(z.read(\"xl/sharedStrings.xml\"))\n        for si in r.findall(\"a:si\",NS): ss.append(\"\".join(t.text or \"\" for t in si.iter(\"{%s}t\"%NS[\"a\"])))\n    for n in sorted(x for x in z.namelist() if x.startswith(\"xl/worksheets/sheet\")):\n        r=ET.fromstring(z.read(n)); k=0\n        for row in r.iter(\"{%s}row\"%NS[\"a\"]):\n            vals=[]\n            for c in row.findall(\"a:c\",NS):\n                v=c.find(\"a:v\",NS); t=c.get(\"t\"); isv=c.find(\"a:is\",NS)\n                if t==\"s\" and v is not None: vals.append(ss[int(v.text)])\n                elif t==\"inlineStr\" and isv is not None: vals.append(\"\".join(x.text or \"\" for x in isv.iter(\"{%s}t\"%NS[\"a\"])))\n                else: vals.append(v.text if v is not None else \"\")\n            k+=1\n            if k<=maxrows: print(\"   \", \" | \".join(vals))\n        print(\"   rows:\",k)\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"): print(\"  [body]\", data.decode(\"utf-8\",\"replace\").replace(\"\\n\",\" / \")); continue\n    print(\"  [att]\",fn)\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\")\n        for i,pg in enumerate(d): print(\"   --p%d--\"%(i+1)); print(pg.get_text().replace(\"\\n\",\" ~ \"))\n    elif fn and fn.lower().endswith(\".xlsx\"): xl(data)\n'\ng(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$DUMP\" \"$2\" \"${3:-999}\" 2>/dev/null); [ -n \"$out\" ] && { echo \"$out\"; return; }; done; echo \"$2 FAILED\"; }\nB=data/scenarios/batch_01\ng $B/0019.eml s1/0019; g $B/0035.eml s1/0035; g $B/0038.eml s1/0038; g $B/0040.eml s1/0040 8; g $B/0041.eml s1/0041 40",
 "description": "Dump big invoice, INR in
... [54 more characters]
```

<details><summary>tool result</summary>

```
###### s1/0019 | Tarrowby Billing <billing@tarrowby.example> | isolde.pembroke@quillmere.example | Invoice TX-US-2035-0196
  [body] Good morning, /  / Please find attached invoice TX-US-2035-0196 for services under TBX-US-EXP-01. / Kindly process payment by the due date shown. /  / Thanks, / Tarrowby Billing / Billing Operations / Tarrowby Express Inc. / 
  [att] TX-US-2035-0196.pdf
   --p1--
Tarrowby Express Inc. ~ 214 Merrow Road, Suite 671, Fallowmere 20905, USA ~ INVOICE TX-US-2035-0196 ~ Invoice date ~ 2035-02-26 ~ Due date ~ 2035-04-12 ~ Contract reference ~ TBX-US-EXP-01 ~ Bill to ~ Quillmere Pharma Inc. ~ 315 Linden Parade, Suite 775, Fallowmere 26170, USA ~ No. ~ AWB ~ Pickup ~ Description ~ Lane ~ Qty / basis ~ Rate ~ Amount (USD) ~ 1 ~ TX72378388 ~ 2035-02-16 ~ Air freight ~ USE1-USW2 ~ 797 kg ~ 5.82 ~ 4638.54 ~ 2 ~ TX72378388 ~ 2035-02-16 ~ Fuel surcharge ~ USE1-USW2 ~ 4638.54 ~ 20.53% ~ 952.29 ~ 3 ~ TX72378388 ~ 2035-02-16 ~ Security surcharge ~ USE1-USW2 ~ 797 kg ~ 0.12 ~ 95.64 ~ 4 ~ TX72378388 ~ 2035-02-16 ~ Delivery fee ~ USE1-USW2 ~ 1 shpt ~ 116.13 ~ 116.13 ~ 5 ~ TX57745206 ~ 2035-02-17 ~ Air freight ~ USE1-USW2 ~ 706 kg ~ 5.82 ~ 4108.92 ~ 6 ~ TX57745206 ~ 2035-02-17 ~ Fuel surcharge ~ USE1-USW2 ~ 4108.92 ~ 20.53% ~ 843.56 ~ 7 ~ TX57745206 ~ 2035-02-17 ~ Security surcharge ~ USE1-USW2 ~ 706 kg ~ 0.12 ~ 84.72 ~ 8 ~ TX57745206 ~ 2035-02-17 ~ Delivery fee ~ USE1-USW2 ~ 1 shpt ~ 116.13 ~ 116.13 ~ 9 ~ TX54079708 ~ 2035-02-15 ~ Air freight ~ USE1-USW2 ~ 62
... [10847 more characters]
```
</details>

## Claude 2026-10-08 16:33:33

Now comparing exam MSAs against the practice MSA. I'll diff the clause text in memory (both piped via stdin).

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"\nDIFF='\nimport sys,email,re,difflib\nfrom email import policy\nimport pymupdf\nraw=sys.stdin.buffer.read(); parts=raw.split(b\"\\n@@@SEP@@@\\n\")\ndef txt(b):\n    m=email.message_from_bytes(b,policy=policy.default)\n    for p in m.walk():\n        fn=p.get_filename()\n        if fn and fn.lower().endswith(\".pdf\"):\n            d=pymupdf.open(stream=p.get_payload(decode=True),filetype=\"pdf\")\n            return fn,[pg.get_text() for pg in d]\nA=txt(parts[0]); B=txt(parts[1])\nprint(\"A=\",A[0],\"B=\",B[0])\ndef lines(pages):\n    out=[]\n    for t in pages:\n        for l in t.split(\"\\n\"):\n            l=l.strip()\n            if l and not l.startswith(\"Initials\") and l!=\"Carrier\" and not l.startswith(\"Page \") and not l.startswith(\"Confidential\"): out.append(l)\n    return out\na=lines(A[1]); b=lines(B[1])\nfor op in difflib.unified_diff(a,b,lineterm=\"\",n=0):\n    if op.startswith(\"@@\"): continue\n    print(op)\n'\n{ gh api -H \"$H\" $R/data/scenarios/batch_01/0001.eml; printf '\\n@@@SEP@@@\\n'; gh api -H \"$H\" $R/data/exam/batch_01/0003.eml; } | python3 -I -c \"$DIFF\" 2>&1 | head -400",
 "description": "Diff practice US MSA vs exam US MSA text"
}
```

<details><summary>tool result</summary>

```
A= MSA-TBX-US-EXP-01.pdf B= MSA-CDA-US-EXP-E91.pdf
--- 
+++ 
-Agreement No. TBX-US-EXP-01
+Agreement No. CDA-US-EXP-E91
-Quillmere Pharma Inc.
-315 Linden Parade, Suite 775
-Fallowmere 26170, USA
+Ferrowyn Life Sciences Inc.
+148 Harwick Close, Suite 411
+Everholt 75661, USA
-Tarrowby Express Inc.
-214 Merrow Road, Suite 671
-Fallowmere 20905, USA
+Caldrith Air Logistics Inc.
+277 Saltmarsh Road, Suite 897
+Dunmere 30801, USA
-Dated 2034-09-27
+Dated 2030-03-14
-THIS AGREEMENT is dated 2034-09-27 and is made between:
-(1) Quillmere Pharma Inc., whose principal office is at 315 Linden Parade, Suite 775, Fallowmere 26170, USA (the Shipper);
+THIS AGREEMENT is dated 2030-03-14 and is made between:
+(1) Ferrowyn Life Sciences Inc., whose principal office is at 148 Harwick Close, Suite 411, Everholt 75661, USA (the Shipper);
-(2) Tarrowby Express Inc., whose principal office is at 214 Merrow Road, Suite 671, Fallowmere 20905, USA (the Carrier).
+(2) Caldrith Air Logistics Inc., whose principal office is at 277 Saltmarsh Road, Suite 897, Dunmere 30801, USA (the Carrier).
-2.1 Effective date. This Agreement takes effect on 2034-10-20 (the Effective Date).
-2.2 Initial term. The initial term is 12 months, ending on 2035-10-19.
-2.3 Auto-renewal. This Agreement does not renew automatically. It ends at the end of the initial term unless extended under
-clause 2.4.
+2.1 Effective date. The Effective Date of this Agreement is 2030-04-02.
+2.2 Initial term. The initial term runs for 12 mo
... [6432 more characters]
```
</details>

## Claude 2026-10-08 16:33:44

Exam US MSA differs in wording and parameters. Now I'll diff the practice IN MSA against the practice US MSA, and the exam IN MSA against the practice IN MSA.

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"\nDIFF='\nimport sys,email,re,difflib\nfrom email import policy\nimport pymupdf\nraw=sys.stdin.buffer.read(); parts=raw.split(b\"\\n@@@SEP@@@\\n\")\ndef txt(b):\n    m=email.message_from_bytes(b,policy=policy.default)\n    for p in m.walk():\n        fn=p.get_filename()\n        if fn and fn.lower().endswith(\".pdf\"):\n            d=pymupdf.open(stream=p.get_payload(decode=True),filetype=\"pdf\")\n            return fn,[pg.get_text() for pg in d]\nA=txt(parts[0]); B=txt(parts[1])\nprint(\"A=\",A[0],\"B=\",B[0])\ndef lines(pages):\n    out=[]\n    for t in pages:\n        for l in t.split(\"\\n\"):\n            l=l.strip()\n            if l and not l.startswith(\"Initials\") and l!=\"Carrier\" and not l.startswith(\"Page \") and not l.startswith(\"Confidential\"): out.append(l)\n    return out\na=lines(A[1]); b=lines(B[1])\nskipnum=re.compile(r\"^[\\d.,%]+( USD| INR)?$|^[A-Z]{3}\\d-[A-Z]{3}\\d$|kg$|^minimum charge$|^\\d{4}-\\d{2}$\")\nfor op in difflib.unified_diff(a,b,lineterm=\"\",n=0):\n    if op.startswith(\"@@\") or op.startswith(\"---\") or op.startswith(\"+++\"): continue\n    if skipnum.search(op[1:]): continue\n    print(op)\n'\necho \"######## practice US MSA (A) vs practice IN MSA (B)\"\n{ gh api -H \"$H\" $R/data/scenarios/batch_01/0001.eml; printf '\\n@@@SEP@@@\\n'; gh api -H \"$H\" $R/data/scenarios/batch_01/0008.eml; } | python3 -I -c \"$DIFF\" 2>&1\necho \"######## practice IN MSA (A) vs exam IN MSA (B)\"\n{ gh api -H \"$H\" $R/data/scenarios/batch_01/0008.eml; printf '\\n@@@SEP@@@\\n'; gh api -H \"$H\" $R/data/exam/batch_01/0001.eml; } | python3 -I -c \"$DIFF\" 2>&1",
 "description": "Diff practice IN MSA vs US MSA and exam IN MSA"
}
```

<details><summary>tool result</summary>

```
######## practice US MSA (A) vs practice IN MSA (B)
Get "https://api.github.com/repos/gocomet-india/nova-takehome/contents/data/scenarios/batch_01/0008.eml": read tcp 172.16.0.2:57926->20.207.73.85:443: read: connection reset by peer
Traceback (most recent call last):
  File "<string>", line 14, in <module>
    print("A=",A[0],"B=",B[0])
                         ~^^^
TypeError: 'NoneType' object is not subscriptable
######## practice IN MSA (A) vs exam IN MSA (B)
A= MSA-TBX-IN-EXP-01.pdf B= MSA-CDA-IN-EXP-E91.pdf
-Agreement No. TBX-IN-EXP-01
+Agreement No. CDA-IN-EXP-E91
-Quillmere Pharma India Pvt. Ltd.
-Plot 152, Linden Parade Industrial Estate
-Navapur Nagar 546 018, India
+Ferrowyn Life Sciences India Pvt. Ltd.
+Plot 107, Merrow Road Industrial Estate
+Mohanbagh 531 095, India
-Tarrowby Express India Pvt. Ltd.
-Plot 264, Linden Parade Industrial Estate
-Kesarganj 597 085, India
+Caldrith Air Logistics India Pvt. Ltd.
+Plot 219, Foundry Walk Industrial Estate
+Ranipet Vihar 495 049, India
-Dated 2034-12-29
+Dated 2030-01-07
-THIS AGREEMENT is dated 2034-12-29 and is made between:
-(1) Quillmere Pharma India Pvt. Ltd., whose principal office is at Plot 152, Linden Parade Industrial Estate, Navapur Nagar 546
-018, India (the Shipper); and
-(2) Tarrowby Express India Pvt. Ltd., whose principal office is at Plot 264, Linden Parade Industrial Estate, Kesarganj 597 085,
-India (the Carrier).
+THIS AGREEMENT is dated 2030-01-07 and is made between:
+(1) Ferrowyn Life Sciences Ind
... [4451 more characters]
```
</details>

## Claude 2026-10-08 16:34:00

Retrying the US-vs-IN practice diff that hit a connection reset, and printing the IN MSA Annex F / annex pages.

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"\nDIFF='\nimport sys,email,re,difflib\nfrom email import policy\nimport pymupdf\nraw=sys.stdin.buffer.read(); parts=raw.split(b\"\\n@@@SEP@@@\\n\")\ndef txt(b):\n    m=email.message_from_bytes(b,policy=policy.default)\n    for p in m.walk():\n        fn=p.get_filename()\n        if fn and fn.lower().endswith(\".pdf\"):\n            d=pymupdf.open(stream=p.get_payload(decode=True),filetype=\"pdf\")\n            return fn,[pg.get_text() for pg in d]\nA=txt(parts[0]); B=txt(parts[1])\nprint(\"A=\",A[0],\"B=\",B[0])\ndef lines(pages):\n    out=[]\n    for t in pages:\n        for l in t.split(\"\\n\"):\n            l=l.strip()\n            if l and not l.startswith(\"Initials\") and l!=\"Carrier\" and not l.startswith(\"Page \") and not l.startswith(\"Confidential\"): out.append(l)\n    return out\na=lines(A[1]); b=lines(B[1])\nskipnum=re.compile(r\"^[\\d.,%]+( USD| INR)?$|^[A-Z]{3}\\d-[A-Z]{3}\\d$|kg$|^minimum charge$|^\\d{4}-\\d{2}$\")\nfor op in difflib.unified_diff(a,b,lineterm=\"\",n=0):\n    if op.startswith(\"@@\") or op.startswith(\"---\") or op.startswith(\"+++\"): continue\n    if skipnum.search(op[1:]): continue\n    print(op)\nprint(\"==== B pages 9-11 raw\")\nfor i in (8,9,10): print(\"--p\",i+1); print(B[1][i].replace(\"\\n\",\" ~ \"))\n'\nfor t in 1 2 3 4; do out=$({ gh api -H \"$H\" $R/data/scenarios/batch_01/0001.eml && printf '\\n@@@SEP@@@\\n' && gh api -H \"$H\" $R/data/scenarios/batch_01/0008.eml; } 2>/dev/null | python3 -I -c \"$DIFF\" 2>/dev/null); [ -n \"$out\" ] && { echo \"$out\"; break; }; done",
 "description": "Retry diff practice US MSA vs IN MSA"
}
```

<details><summary>tool result</summary>

```
A= MSA-TBX-US-EXP-01.pdf B= MSA-TBX-IN-EXP-01.pdf
-Agreement No. TBX-US-EXP-01
+Agreement No. TBX-IN-EXP-01
-Quillmere Pharma Inc.
-315 Linden Parade, Suite 775
-Fallowmere 26170, USA
+Quillmere Pharma India Pvt. Ltd.
+Plot 152, Linden Parade Industrial Estate
+Navapur Nagar 546 018, India
-Tarrowby Express Inc.
-214 Merrow Road, Suite 671
-Fallowmere 20905, USA
+Tarrowby Express India Pvt. Ltd.
+Plot 264, Linden Parade Industrial Estate
+Kesarganj 597 085, India
-Dated 2034-09-27
+Dated 2034-12-29
-THIS AGREEMENT is dated 2034-09-27 and is made between:
-(1) Quillmere Pharma Inc., whose principal office is at 315 Linden Parade, Suite 775, Fallowmere 26170, USA (the Shipper);
-and
-(2) Tarrowby Express Inc., whose principal office is at 214 Merrow Road, Suite 671, Fallowmere 20905, USA (the Carrier).
+THIS AGREEMENT is dated 2034-12-29 and is made between:
+(1) Quillmere Pharma India Pvt. Ltd., whose principal office is at Plot 152, Linden Parade Industrial Estate, Navapur Nagar 546
+018, India (the Shipper); and
+(2) Tarrowby Express India Pvt. Ltd., whose principal office is at Plot 264, Linden Parade Industrial Estate, Kesarganj 597 085,
+India (the Carrier).
-2.1 Effective date. This Agreement takes effect on 2034-10-20 (the Effective Date).
-2.2 Initial term. The initial term is 12 months, ending on 2035-10-19.
+2.1 Effective date. This Agreement takes effect on 2035-01-06 (the Effective Date).
+2.2 Initial term. The initial term is 12 months, ending on 2036-01-05.
-6.1 
... [8922 more characters]
```
</details>

## Claude 2026-10-08 16:34:21

Now dumping representative exam emails (invoices in both layouts, amendment, waiver thread, extension, rate notice, credit note, AP register).

**Tool call: Bash**

```json
{
 "command": "DUMP='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nimport xml.etree.ElementTree as ET\nname=sys.argv[1]; maxrows=int(sys.argv[2]) if len(sys.argv)>2 else 999\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nprint(\"######\",name, \"|\", m[\"From\"], \"->\", m[\"To\"], \"|\", m[\"Subject\"], \"|\", m[\"Date\"])\nNS={\"a\":\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"}\ndef xl(data):\n    z=zipfile.ZipFile(io.BytesIO(data)); ss=[]\n    if \"xl/sharedStrings.xml\" in z.namelist():\n        r=ET.fromstring(z.read(\"xl/sharedStrings.xml\"))\n        for si in r.findall(\"a:si\",NS): ss.append(\"\".join(t.text or \"\" for t in si.iter(\"{%s}t\"%NS[\"a\"])))\n    for n in sorted(x for x in z.namelist() if x.startswith(\"xl/worksheets/sheet\")):\n        r=ET.fromstring(z.read(n)); k=0\n        for row in r.iter(\"{%s}row\"%NS[\"a\"]):\n            vals=[]\n            for c in row.findall(\"a:c\",NS):\n                v=c.find(\"a:v\",NS); t=c.get(\"t\"); isv=c.find(\"a:is\",NS)\n                if t==\"s\" and v is not None: vals.append(ss[int(v.text)])\n                elif t==\"inlineStr\" and isv is not None: vals.append(\"\".join(x.text or \"\" for x in isv.iter(\"{%s}t\"%NS[\"a\"])))\n                else: vals.append(v.text if v is not None else \"\")\n            k+=1\n            if k<=maxrows: print(\"   \", \" | \".join(vals))\n        print(\"   rows:\",k)\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"): print(\"  [body]\", data.decode(\"utf-8\",\"replace\").replace(\"\\n\",\" / \")); continue\n    print(\"  [att]\",fn)\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\")\n        for i,pg in enumerate(d):\n            print(\"   --p%d-- images=%d\"%(i+1,len(pg.get_images()))); print(pg.get_text().replace(\"\\n\",\" ~ \"))\n            for im in pg.get_images(full=True):\n                x=d.extract_image(im[0]); print(\"   IMAGE xref\",im[0],x[\"ext\"],x[\"width\"],\"x\",x[\"height\"],len(x[\"image\"]),\"bytes\")\n    elif fn and fn.lower().endswith(\".xlsx\"): xl(data)\n'\ng(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$DUMP\" \"$2\" \"${3:-999}\" 2>/dev/null); [ -n 
... [423 more characters]
```

**Tool call: Bash**

```json
{
 "command": "DUMP='\nimport sys,email,io,zipfile,re\nfrom email import policy\nimport pymupdf\nname=sys.argv[1]\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nprint(\"######\",name, \"|\", m[\"From\"], \"->\", m[\"To\"], \"|\", m[\"Subject\"], \"|\", m[\"Date\"])\nfor p in m.walk():\n    if p.is_multipart(): continue\n    ct=p.get_content_type(); fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and ct.startswith(\"text/\"): print(\"  [body]\", data.decode(\"utf-8\",\"replace\").replace(\"\\n\",\" / \")); continue\n    print(\"  [att]\",fn,ct,len(data))\n    if fn and fn.lower().endswith(\".pdf\"):\n        d=pymupdf.open(stream=data,filetype=\"pdf\"); print(\"   meta\",d.metadata.get(\"title\"),d.metadata.get(\"creator\"),d.metadata.get(\"producer\"))\n        for i,pg in enumerate(d):\n            print(\"   --p%d-- images=%d\"%(i+1,len(pg.get_images()))); print(pg.get_text().replace(\"\\n\",\" ~ \"))\n            for im in pg.get_images(full=True):\n                x=d.extract_image(im[0]); print(\"   IMAGE xref\",im[0],x[\"ext\"],x[\"width\"],\"x\",x[\"height\"],len(x[\"image\"]),\"bytes\")\n'\ng(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$DUMP\" \"$2\" 2>/dev/null); [ -n \"$out\" ] && { echo \"$out\"; return; }; done; echo \"$2 FAILED\"; }\nE=data/exam/batch_02\ng $E/0001.eml e2/0001; g $E/0009.eml e2/0009; g $E/0012.eml e2/0012; g $E/0014.eml e2/0014; g $E/0016.eml e2/0016; g $E/0019.eml e2/0019; g data/scenarios/batch_02/0016.eml s2/0016",
 "description": "Dump representative exam batch_02 emails and image PDFs",
 "timeout": 300000
}
```

<details><summary>tool result</summary>

```
###### e1/0002 | Caldrith Billing <billing@caldrith.example> -> tamsin.everly@ferrowyn.example | Invoice CDI-2930-0148 | Sat, 02 Mar 2030 10:23:00 +0000
  [body] To whom it may concern, /  / Please find attached invoice CDI-2930-0148 for services under CDA-IN-EXP-E91. / Kindly process payment by the due date shown. /  / Sincerely, / Caldrith Billing | Billing Operations | Caldrith Air Logistics India Pvt. Ltd. / 
  [att] CDI-2930-0148.pdf
   --p1-- images=0
Caldrith Air Logistics India Pvt. Ltd. ~ Plot 219, Foundry Walk Industrial Estate, Ranipet Vihar 495 049, India ~ GSTIN 30LSAJZ3930J1Z9 ~ Charges advice CDI-2930-0148 ~ Document date ~ 02/03/2030 ~ Payable by ~ 01/04/2030 ~ Contract ~ CDA-IN-EXP-E91 ~ Currency ~ INR ~ Customer ~ Ferrowyn Life Sciences India Pvt. Ltd. ~ Plot 107, Merrow Road Industrial Estate, Mohanbagh 531 095, India ~ GSTIN 36JHOAW8944J1Z7 ~ Route ~ Waybill ~ Charge ~ Basis ~ Rate ~ Amount ~ Collected ~ INW1-USC1 ~ CA98924245 ~ Air freight ~ 106 kg ~ 357.13 ~ 37,855.78 ~ 22/02/2030 ~ INW1-USC1 ~ CA98924245 ~ Fuel surcharge ~ 37,855.78 ~ 16.67% ~ 6,310.56 ~ 22/02/2030 ~ INW1-USC1 ~ CA98924245 ~ Security surcharge ~ 106 kg ~ 17.93 ~ 1,900.58 ~ 22/02/2030 ~ INW1-USC1 ~ CA98924245 ~ Delivery fee ~ 1 shpt ~ 8644.00 ~ 8,644.00 ~ 22/02/2030 ~ INR 54,710.92 ~ Charges ~ INR 0.00 ~ Tax ~ nil ~ INR 54,710.92 ~ Total payable ~ Terms 30 days. Please remit to Caldrith Air Logistics India Pvt. Ltd. at Ostlea Commercial Bank, account 851170553729 (IFSC OSTL0992708
... [6839 more characters]
```
</details>

<details><summary>tool result</summary>

```
###### e2/0001 | Joaquin Rathbone <joaquin.rathbone@caldrith.example> -> odette.underhill@ferrowyn.example | Rate notice USE2-USC3 | Mon, 09 Sep 2030 09:32:00 +0000
  [body] Good afternoon Odette, /  / Notice ref. CDA-US-EXP-E91/RN-USE2-USC3-2030-09-15 / Pursuant to clause 3.5, the rates below apply to lane USE2-USC3 for pickups from 2030-09-15 until 2030-10-10: / USE2-USC3 minimum charge = USD 85.98 / USE2-USC3 0-44.5 kg = USD 5.08 / USE2-USC3 45-99.5 kg = USD 4.72 / USE2-USC3 100-299.5 kg = USD 4.38 / USE2-USC3 300+ kg = USD 4.06 /  / Yours sincerely, / Joaquin Rathbone | Pricing Manager | Caldrith Air Logistics Inc. / 
###### e2/0009 | Thea Kapadia <thea.kapadia@caldrith.example> -> odette.underhill@ferrowyn.example | Re: Charges on your account | Mon, 14 Oct 2030 17:48:00 +0000
  [body] Good afternoon Odette, /  / The Delivery fee billed against AWB CA75329761 is waived, with our apologies. / Kindly deduct it when you pay. /  / Yours sincerely, / Thea Kapadia | Customer Finance Lead | Caldrith Air Logistics Inc. / On 2030-10-14, Odette Underhill wrote: / > To whom it may concern, / >  / > Could you check the Delivery fee on AWB CA75329761? We did not expect it on this shipment. / >  / > With thanks, / > Odette Underhill | AP Manager | Ferrowyn Life Sciences Inc. / 
###### e2/0012 | Caldrith Billing <billing@caldrith.example> -> odette.underhill@ferrowyn.example | Invoice CDU-3051329 | Thu, 05 Dec 2030 15:59:00 +0000
  [body] Dear Sir or Madam, /
... [9933 more characters]
```
</details>

## Claude 2026-10-08 16:35:09

Now a keyword sweep across every email body and attachment in all four batches for injection-style text, forwarded/quoted content, conditional waivers, and backdating.

**Tool call: Bash**

```json
{
 "command": "SW='\nimport sys,email,re\nfrom email import policy\nimport pymupdf\nname=sys.argv[1]\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nkw=re.compile(r\"ignore|instruction|system|assistant|\\bAI\\b|override|prompt|disregard|automat|agent|model|forward|Fwd|FW:|wrote:|condition|provided that|subject to|retro|backdat|with effect from|supersed|replac|correct|revis|credit|cancel|void|reissue|copy|reminder|duplicate|terminat|renew|extend|notice\",re.I)\ntxts=[]\nfor p in m.walk():\n    if p.is_multipart(): continue\n    fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and p.get_content_type().startswith(\"text/\"): txts.append((\"body\",data.decode(\"utf-8\",\"replace\")))\n    elif fn and fn.lower().endswith(\".pdf\") and not fn.startswith((\"MSA-\",)):\n        d=pymupdf.open(stream=data,filetype=\"pdf\"); txts.append((fn,\"\\n\".join(pg.get_text() for pg in d)))\nsubj=m[\"Subject\"] or \"\"\nhits=[]\nfor src,t in txts:\n    for l in t.split(\"\\n\"):\n        if kw.search(l) and not re.search(r\"Kindly process payment by the due date|Please find attached (invoice|statement)|Payment terms: net|Terms \\d+ days|Initials|^Page \",l): hits.append(src+\": \"+l.strip())\nif not subj.startswith((\"Invoice \",\"Statement \",\"Tracking export\",\"AP register\",\"Executed agreement\")) or hits:\n    print(\"##\",name,\"|\",m[\"From\"],\"|\",subj)\n    if not subj.startswith((\"Invoice \",\"Statement \",\"Tracking export\",\"AP register\",\"Executed agreement\",\"Signed amendment\")):\n        for src,t in txts:\n            if src==\"body\": print(\"   BODY:\", t.strip().replace(\"\\n\",\" / \")[:700])\n    for h in hits[:12]: print(\"   HIT:\",h[:300])\n'\ns(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$SW\" \"$2\" 2>/dev/null); rc=$?; [ $rc -eq 0 ] && { [ -n \"$out\" ] && echo \"$out\"; return; }; done; echo \"$2 FAILED\"; }\nfor i in $(seq -w 1 41); do s data/scenarios/batch_01/00$i.eml s1/00$i; done\nfor i in $(seq -w 1 37); do s data/scenarios/batch_02/00$i.eml s2/00$i; done",
 "description": "Sweep scenario emails for injection, quoted and special text",
 "timeout": 500000
}
```

**Tool call: Bash**

```json
{
 "command": "SW='\nimport sys,email,re\nfrom email import policy\nimport pymupdf\nname=sys.argv[1]\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nkw=re.compile(r\"ignore|instruction|system|assistant|\\bAI\\b|override|prompt|disregard|automat|agent|model|forward|Fwd|FW:|wrote:|condition|provided that|subject to|retro|backdat|with effect from|supersed|replac|correct|revis|credit|cancel|void|reissue|copy|reminder|duplicate|terminat|renew|extend|notice\",re.I)\ntxts=[]\nfor p in m.walk():\n    if p.is_multipart(): continue\n    fn=p.get_filename(); data=p.get_payload(decode=True) or b\"\"\n    if not fn and p.get_content_type().startswith(\"text/\"): txts.append((\"body\",data.decode(\"utf-8\",\"replace\")))\n    elif fn and fn.lower().endswith(\".pdf\") and not fn.startswith((\"MSA-\",)):\n        d=pymupdf.open(stream=data,filetype=\"pdf\"); txts.append((fn,\"\\n\".join(pg.get_text() for pg in d)))\nsubj=m[\"Subject\"] or \"\"\nhits=[]\nfor src,t in txts:\n    for l in t.split(\"\\n\"):\n        if kw.search(l) and not re.search(r\"Kindly process payment by the due date|Please find attached (invoice|statement)|Payment terms: net|Terms \\d+ days|Initials|^Page \",l): hits.append(src+\": \"+l.strip())\nif not subj.startswith((\"Invoice \",\"Statement \",\"Tracking export\",\"AP register\",\"Executed agreement\")) or hits:\n    print(\"##\",name,\"|\",m[\"From\"],\"|\",subj)\n    if not subj.startswith((\"Invoice \",\"Statement \",\"Tracking export\",\"AP register\",\"Executed agreement\",\"Signed amendment\")):\n        for src,t in txts:\n            if src==\"body\": print(\"   BODY:\", t.strip().replace(\"\\n\",\" / \")[:700])\n    for h in hits[:12]: print(\"   HIT:\",h[:300])\n'\ns(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$SW\" \"$2\" 2>/dev/null); rc=$?; [ $rc -eq 0 ] && { [ -n \"$out\" ] && echo \"$out\"; return; }; done; echo \"$2 FAILED\"; }\nfor i in $(seq -w 1 18); do s data/exam/batch_01/00$i.eml e1/00$i; done\nfor i in $(seq -w 1 23); do s data/exam/batch_02/00$i.eml e2/00$i; done",
 "description": "Sweep exam emails for injection, quoted and special text",
 "timeout": 500000
}
```

<details><summary>tool result</summary>

```
Exit code 1
## s1/0002 | Joaquin Rathbone <joaquin.rathbone@tarrowby.example> | Signed amendment 1 to TBX-US-EXP-01
   HIT: TBX-US-EXP-01-AMD-1.pdf: 1. Annex A rates for the lanes below are deleted and replaced with the following, for every period, with effect from the effective
   HIT: TBX-US-EXP-01-AMD-1.pdf: 2. The Annex A rates for lane(s) USS2-INN1 are deleted and replaced as follows: Annex A rev 2 (attached) applies from
   HIT: TBX-US-EXP-01-AMD-1.pdf: Executed by duly authorised officers. Schedule 1 governs Authorised Persons for rates, waivers, payment terms and notices.
## s1/0003 | Isolde Pembroke <isolde.pembroke@quillmere.example> | Charges on your account
   BODY: Hi, /  / Could you check the Delivery fee on AWB TX45998993? We did not expect it on this shipment. /  / Best regards, / Isolde Pembroke / AP Manager / Quillmere Pharma Inc.
## s1/0004 | Signe Underhill <signe.underhill@tarrowby.example> | Re: Charges on your account
   BODY: Dear colleagues, /  / Following our call, we waive the Delivery fee on AWB TX45998993. / Please disregard that charge if it appears on an invoice. /  / Regards, / Signe Underhill / Customer Finance Lead / Tarrowby Express Inc. / On 2034-11-19, Isolde Pembroke wrote: / > Hi, / >  / > Could you check the Delivery fee on AWB TX45998993? We did not expect it on this shipment. / >  / > Best regards, / > Isolde Pembroke / > AP Manager / > Quillmere Pharma Inc.
   HIT: body: Please disregard that charge if it appe
... [5955 more characters]
```
</details>

<details><summary>tool result</summary>

```
Exit code 1
## e1/0004 | Ines Oyelaran <ines.oyelaran@caldrith.example> | Signed amendment 1 to CDA-US-EXP-E91
   HIT: CDA-US-EXP-E91-AMD-1.pdf: 1. Annex A rates for the lanes below are deleted and replaced with the following, for every period, with effect from the effective
   HIT: CDA-US-EXP-E91-AMD-1.pdf: 2. The Annex A rates for lane(s) USW2-USW1 are deleted and replaced as follows: Annex A rev 2 (attached) applies from
   HIT: CDA-US-EXP-E91-AMD-1.pdf: Executed by duly authorised officers. Schedule 1 governs Authorised Persons for rates, waivers, payment terms and notices.
## e1/0006 | Odette Underhill <odette.underhill@ferrowyn.example> | Charges on your account
   BODY: Good afternoon Thea, /  / Could you check the Delivery fee on AWB CA10343321? We did not expect it on this shipment. /  / Warm regards, / Odette Underhill | AP Manager | Ferrowyn Life Sciences Inc.
## e1/0007 | Thea Kapadia <thea.kapadia@caldrith.example> | Re: Charges on your account
   BODY: Dear Sir or Madam, /  / Please treat the Delivery fee on AWB CA10343321 as waived. / We will not pursue payment of that line. /  / Yours sincerely, / Thea Kapadia | Customer Finance Lead | Caldrith Air Logistics Inc. / On 2030-06-07, Odette Underhill wrote: / > Good afternoon Thea, / >  / > Could you check the Delivery fee on AWB CA10343321? We did not expect it on this shipment. / >  / > Warm regards, / > Odette Underhill | AP Manager | Ferrowyn Life Sciences Inc.
   HIT: body: On 2030-06-07, Od
... [3201 more characters]
```
</details>

## Claude 2026-10-08 16:40:49

No injection text exists in the visible practice or exam mail. Next I'll check the README and GLOSSARY for how supersedes, retro, learned_at, injection, and the unattended-action checks are defined.

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"; gh api -H \"$H\" $R/README.md | grep -n -i -E \"supersed|retro|backdat|learned_at|inject|quoted|forward|unattended|autonomous|cannot_determine|conflict|image|scan|OCR|hidden|new customer|new carrier|layout|wording|feedback|amount_range|late_fee_risk|60 days|window\" | head -60",
 "description": "Grep README for trick and rule definitions"
}
```

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"; gh api -H \"$H\" $R/GLOSSARY.md | grep -n -i -E \"supersed|retro|backdat|learned_at|inject|quoted|forward|unattended|cannot_determine|conflict|scan|image|near miss|decoy|variant|[A-Z]{2}-0[0-9]|clean control\" | head -80",
 "description": "Grep GLOSSARY for trick and variant definitions"
}
```

<details><summary>tool result</summary>

```
3:Freight runs on email. A carrier sends an invoice as a PDF. Someone forwards a waiver. A rate changes in an amendment
16:- raise a conflict when two sources that both count disagree, and leave that call to a person;
21:In the practice mailbox Tarrowby Express is the carrier. The exam mailbox and our hidden set bring other customers
31:6. **Expiry.** A contract that ends, or whose notice deadline falls, in the next 60 days.
33:Two more behaviours cut across all six. A **conflict** is two trusted sources that disagree. **cannot_determine** means
34:the answer depends on a document you don't have. [GLOSSARY.md](GLOSSARY.md) defines every term, formula and window.
40:per class, plus a conflict and a charge billed again four months later. Each has its documents, an `EXPLANATION.md`
43:feedback file after the first batch (`data/scenarios/feedback/`), and the answers in `data/scenarios/answers/`. An
46:fails. `make grade` replays the mailbox through your harness with our grader, feeds in the feedback file after
51:and a carrier you haven't met, with their own contracts, people, email habits and invoice layout. The problems in it are
54:dollars and the invoice ids, then the four totals, the conflicts with both sources, and the cannot_determine items
57:beyond that. One exam invoice is a scanned image with no text layer, and it carries one of the exam's findings: your
58:harness needs OCR or a vision model to get the sheet right (see "Reading the documents").
61:of the practice worl
... [2562 more characters]
```
</details>

<details><summary>tool result</summary>

```
35:- `conflict`: two trusted sources disagree and the contract's order of precedence doesn't settle it. See below.
36:- `cannot_determine`: the answer depends on a document you don't have. See below.
38:About a quarter of every set is clean invoices and near misses (a weight on the other side of a band, a sender with no
55:  for that month makes it `cannot_determine`.
65:- Quoted or forwarded text whose original you don't hold has no authority on its own.
75:5. quoted text with no original, text aimed at automated readers, anything from outside the two companies.
89:and any condition it sets was met. A waiver from anyone else is `no_finding`. A waiver you only see quoted inside
90:someone else's forward is `cannot_determine`: ask the carrier's Key Account Manager for the original.
137:Only `finding` counts. Conflicts and cannot_determine items are listed on their own and add nothing. Findings sent to
141:## Conflict, cannot_determine and human_review
147:| **conflict** | Two sources you hold, both with enough authority and both in force on the pickup date, give different correct amounts, and the precedence clause doesn't rank them. A signed amendment against a Schedule 1 rate notice is the usual case. | `verdict: conflict`, `action: escalate`, both sources in `evidence`, and `amount_range` = [billed minus the higher correct amount (never below 0), billed minus the lower one]. | no |
148:| **cannot_determine** | The answer depends on a document that a held document names, you 
... [2925 more characters]
```
</details>

## Claude 2026-10-08 16:40:59

Reading the relevant GLOSSARY sections (authority ranking, waivers, unattended test, supersedes/retro).

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"; gh api -H \"$H\" $R/GLOSSARY.md | sed -n '36,100p;177,230p'",
 "description": "Read GLOSSARY authority, waiver, and supersedes sections"
}
```

<details><summary>tool result</summary>

```
- `cannot_determine`: the answer depends on a document you don't have. See below.

About a quarter of every set is clean invoices and near misses (a weight on the other side of a band, a sender with no
authority, a credit that cancels the charge). Their right answer is `no_finding`, and listing them as findings costs
you.

## Amounts

- **What it is.** Billed minus correct, positive, in USD, for the whole finding. If billed minus correct is zero or
  less, it's `no_finding`. An undercharge is never a finding.
- **Lines.** Each correct line is rate times quantity, rounded half up to cents, in the invoice's own currency.
  Quantities are as printed (chargeable weight to one decimal, pieces, days). A percentage surcharge is rounded the
  same way, on a base that is itself the sum of already-rounded lines.
- **The finding.** Add up billed minus correct over the lines in the finding, in the invoice's currency.
- **Pickup date.** A shipment is priced on the day it was picked up. That date picks the rate period, the fuel month,
  and whether an amendment or a newer contract applies. Read it from the first of these you hold: the tracking export
  event `PICKED_UP`, then a carrier "picked up" email, then the AWB date, then the ship date printed on the invoice.
- **INR invoices.** Convert once per finding, never per line: `amount_usd = round_half_up(amount_inr / fx, 2)`, where
  `fx` is the INR per 1 USD rate in the contract's Annex F for the calendar month of the invoice date. No Anne
... [6484 more characters]
```
</details>

## Claude 2026-10-08 16:41:21

Last checks: confirming the alternate practice invoice layouts, then computing per-batch totals.

**Tool call: Bash**

```json
{
 "command": "DUMP='\nimport sys,email\nfrom email import policy\nimport pymupdf\nm=email.message_from_bytes(sys.stdin.buffer.read(),policy=policy.default)\nfor p in m.walk():\n    fn=p.get_filename()\n    if fn and fn.lower().endswith(\".pdf\") and not fn.startswith((\"AWB\",\"DGD\")):\n        d=pymupdf.open(stream=p.get_payload(decode=True),filetype=\"pdf\"); print(\"##\",sys.argv[1],fn); print(d[0].get_text().replace(\"\\n\",\" ~ \")[:900])\n'\ng(){ for t in 1 2 3 4; do out=$(gh api -H \"Accept: application/vnd.github.raw\" /repos/gocomet-india/nova-takehome/contents/$1 2>/dev/null | python3 -I -c \"$DUMP\" \"$2\" 2>/dev/null); [ -n \"$out\" ] && { echo \"$out\"; return; }; done; echo \"$2 FAILED\"; }\ng data/scenarios/batch_02/0012.eml s2/0012; g data/scenarios/batch_02/0026.eml s2/0026; g data/scenarios/batch_02/0007.eml s2/0007\npython3 -I -c \"\nb={'scen_b01':[23413,1781,168,443,1078,1084,545,24356,1012,555,2654,1626,2575,1004,997,987,554,1281,3481,146,558,1578,210,414,420,1322,998,545,297,151,4035,197,1099,995,2463,562,1066,1712,1077,8981,1258],\n'scen_b02':[1426,550,406,219,1081,2694,955,1074,1482,1005,1621,1014,1021,545,1010,220,1327,1499,1426,1611,201,544,1499,1025,1025,1254,1018,1738,1324,549,168,461,1007,1944,1293,5374,2444],\n'exam_b01':[24466,1204,23498,1828,1111,194,458,1043,1054,1037,232,3462,1109,1472,1126,3039,1094,561],\n'exam_b02':[443,2632,1049,1617,1302,1115,1347,196,473,1115,1832,3952,1254,2140,234,504,1294,1050,489,1033,1117,5440,1147]}\nfor k,v in b.items(): print(k,'emails',len(v),'chars',sum(v),'~tokens',sum(v)//4)\n\"",
 "description": "Check alternate invoice layouts and sum batch sizes"
}
```

<details><summary>tool result</summary>

```
## s2/0012 TX-US-2035-0239.pdf
Freight bill no. TX-US-2035-0239 ~ Tarrowby Express Inc. ~ 214 Merrow Road, Suite 671, Fallowmere 20905, USA ~ Issued on ~ 01 Jul 2035 ~ Settle by ~ 15 Aug 2035 ~ Service agreement ~ TBX-US-EXP-01 ~ Account ~ Quillmere Pharma Inc. ~ 315 Linden Parade, Suite 775, Fallowmere 26170, USA ~ Charge ~ Shipment ~ Route ~ Collected ~ Net (USD) ~ Units ~ Unit price ~ Air freight ~ TX77231778 ~ USC3-INS1 ~ 25 Jun 2035 ~ 493.37 ~ 103 kg ~ 4.79 ~ Fuel surcharge ~ TX77231778 ~ USC3-INS1 ~ 25 Jun 2035 ~ 121.07 ~ 493.37 ~ 24.54% ~ Security surcharge ~ TX77231778 ~ USC3-INS1 ~ 25 Jun 2035 ~ 12.36 ~ 103 kg ~ 0.12 ~ Delivery fee ~ TX77231778 ~ USC3-INS1 ~ 25 Jun 2035 ~ 116.13 ~ 1 shpt ~ 116.13 ~ USD 742.93 ~ Net charges ~ USD 0.00 ~ Tax ~ none charged ~ USD 742.93 ~ Balance due ~ Settlement 45 days net by bank transfer to Fenmoor Trust Bank, account 102163192184, SWIFT FENMUS7X. Quote the freight bill ~ nu
## s2/0026 TXI-35-36-0030.pdf
Tarrowby Express India Pvt. Ltd. ~ INVOICE TXI/35-36/0030 ~ Plot 264, Linden Parade Industrial Estate, Kesarganj 597 085, India ~ GSTIN 20MKUZB6447X1Z4 ~ Invoice date ~ 2035-08-26 ~ Due date ~ 2035-10-10 ~ Contract reference ~ TBX-IN-EXP-01 ~ Bill to ~ Quillmere Pharma India Pvt. Ltd. ~ Plot 152, Linden Parade Industrial Estate, Navapur Nagar 546 018, India ~ GSTIN 33VHHKR7771R1Z7 ~ AWB ~ Description ~ Pickup ~ Lane ~ SAC ~ Qty / basis ~ Rate ~ Amount (INR) ~ TX15472186 ~ Air freight ~ 2035-08-13 ~ INN3-USC3 ~ 996531 ~ 396 kg ~ 584.
... [1418 more characters]
```
</details>

## Claude 2026-10-08 16:42:53

One last check on how the grader renders xlsx rows and PDF pages into quotable text, since the expected quotes don't match the raw cells.

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"; gh api -H \"$H\" $R/grader/extract.py | grep -n -E \"def |due|USD|serial|from_excel|datetime|\\| |ocr|image|join\" | head -40",
 "description": "Check grader extract.py xlsx row rendering"
}
```

<details><summary>tool result</summary>

```
6:- XLSX: one "page" per sheet (hidden sheets included), each row as its displayed cell texts joined by " | ";
15:from datetime import date, datetime
19:from email.utils import parseaddr, parsedate_to_datetime
22:SEP = " | "
25:def norm(s: str) -> str:
26:    return " ".join(s.split())
30:def _reading_order(page) -> str:
40:    return "\n".join(" ".join(x[4] for x in sorted(ws, key=lambda w: w[0])) for _, ws in lines)
43:def pdf_pages(data: bytes) -> list[str]:
49:def pdf_is_image_only(data: bytes) -> bool:
57:def _cell_text(cell) -> str:
66:    if isinstance(v, datetime):
76:def xlsx_pages(data: bytes) -> list[str]:
85:                rows.append(SEP.join(cells))
86:        pages.append("\n".join(rows))
91:def parse_eml(data: bytes):
95:def email_lines(msg) -> list[str]:
100:    dt = parsedate_to_datetime(str(msg["Date"]))
106:        out.append("Attachments: " + ", ".join(names))
110:def attachments(data: bytes) -> list[tuple[str, bytes]]:
115:def pages_of(data: bytes, ext: str) -> list[str]:
122:        return ["\n".join(email_lines(parse_eml(data)))]
126:def found(pages: list[str], page: int, quote: str) -> bool:
138:    def __init__(self, root: Path):
140:        self._by_name: dict[str, list[tuple[str, bytes]]] | None = None
143:    def _index(self):
152:    def resolve(self, doc: str) -> tuple[bytes, str, str]:
176:    def pages(self, doc: str) -> tuple[list[str], bool]:
180:            scan = ext == "pdf" and pdf_is_image_only(data)
184:    def check(self, doc: str, p
... [36 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "R=/repos/gocomet-india/nova-takehome/contents; H=\"Accept: application/vnd.github.raw\"; gh api -H \"$H\" $R/grader/extract.py | sed -n '1,14p;28,90p;95,108p;126,136p;176,200p'",
 "description": "Read grader extract.py rendering functions"
}
```

<details><summary>tool result</summary>

```
"""Read mailbox files back as text, page by page, the way the grader checks a citation.

Standalone on purpose (the candidate's copy of the grader imports nothing else from this repo). Same rules as the
generator's reader:
- text PDF: words grouped into lines by baseline, each line read left to right; one entry per PDF page;
- XLSX: one "page" per sheet (hidden sheets included), each row as its displayed cell texts joined by " | ";
- .eml: one page: From / To / Cc / Date (ISO, UTC) / Subject, a blank line, the plain-text body, then
  "Attachments: a.pdf, b.xlsx" when there are any.
Comparisons collapse whitespace, because a long line wraps at a space in a PDF.
"""
from __future__ import annotations

import io
import re

# ---- PDF --------------------------------------------------------------------------------------------------------------
def _reading_order(page) -> str:
    words = page.get_text("words")
    words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines: list[list] = []
    for w in words:
        mid = (w[1] + w[3]) / 2
        if lines and abs(lines[-1][0] - mid) <= 2.5:
            lines[-1][1].append(w)
        else:
            lines.append([mid, [w]])
    return "\n".join(" ".join(x[4] for x in sorted(ws, key=lambda w: w[0])) for _, ws in lines)


def pdf_pages(data: bytes) -> list[str]:
    import pymupdf
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        return [_reading_order(p) for p in doc]


def pdf_is_image_only(data: bytes) -> b
... [3858 more characters]
```
</details>

## Claude 2026-10-08 16:45:21

I read everything in memory and wrote nothing to disk. pymupdf works locally; openpyxl isn't installed, so I read the xlsx files as raw XML (dates come out as Excel serial numbers).

## 1. Worked examples (`data/examples/*`)

| Example (as_of) | Deciding clause | Arithmetic | Look-alike that is fine | Where each fact lives |
|---|---|---|---|---|
| overcharge (2032-08-31) | MSA §3.2 pricing date; Annex A p.8 `USE2-INE2 100-299.5 kg 6.01 6.16` | 241 kg × 6.01 = 1448.41; fuel 20.16% = 292.00; billed 1612.29+325.04 = 1937.33 → **196.92** | 44 kg billed at 7.73 is correct: it falls in band 0-44.5 (§3.4) | invoice PDF (line), tracking xlsx (pickup date), MSA Annex A/C |
| conflict (2032-11-30) | §13.3: notice and amendment are unranked | 113 kg: amendment rate 2.88 gives 400.75, notice rate 3.03 gives 421.62; billed 421.62 → range **[0.00, 20.87]**, `escalate` | the same notice from someone not in Schedule 1 → plain overcharge of 20.87 | AMD-1 PDF, notice email body, MSA |
| duplicate (2033-08-31) | AP register row `…paid | 2033-02-07` plus a resend saying "Please process payment at your earliest convenience." | invoice total **1259.23** | master AWB split: H1 240 kg + H2 103 kg = 343 kg master total | AP xlsx, resend body, master AWB PDF |
| duplicate_rebilled (2032-08-31) | Annex E p.10 `Code SEC… also billed as: Screening fee (adj.)` | same AWB, same code, same amount 4 months later; the later invoice is flagged, **42.08** | a different AWB or a different code is a new charge | two invoice PDFs, Annex E |
| late_fees (2033-02-28) | §10.5 due-date extension by the payment_terms contact | extended to 08-25, paid 08-17 → −8 days → the billed fee **12.65** is not owed | extended to 12-12, paid 2033-01-01 (20 days, grace 5) → 1.86% × 4200.07 = 78.12, owed | extension email, AP xlsx, late-fee line on a later invoice, MSA |
| waived_but_billed (2034-02-28) | §11.1 plus Schedule 1 p.11 (sender listed for waivers) | the whole line, **133.44**, on an invoice dated after the waiver | waiver names a different AWB (§11.2) | waiver email, Schedule 1, invoice |
| cashback (2033-11-30) | §7.1 tiers; §1.1 Qualifying Spend (QS) definition | Q2 QS 65566.99 → 5% = **3278.35**, no credit note, so claim | Q3 gross 60271.89, but QS without duty, tax and late fees is 51381.39 < 55,000 | MSA p.3–4, invoice totals and excluded lines |
| expiry (2034-02-28) | §2.2 term ends 2034-03-20; §2.3 no auto-renewal | 20 days ≤ 60 → `internal:alert` | the same contract as of 2033-08-31 is 201 days out → absent | MSA only |

## 2. Scenario answers (30 files)

Reports are run as of 2035-05-31 (b1) and 2035-09-30 (b2). In the table, `-` means the item is absent from that report.

| sc- | Class / variant | Verdict | USD | b1/b2 | Evidence / note |
|---|---|---|---|---|---|
| 28f910a1 | overcharge FB-P1 | finding | 36.07 | ✓/- | b1/0034 inv; MSA p.8 4.71; b1/0024 notice 5.03 from Joaquin Rathbone (Key Account Manager, not listed for rates); b1/0040 tracking. Closed by feedback fb-01-p1 |
| a9066934 | overcharge FB-P1 | finding, learned_at required | 45.51 | -/✓ | b2/0025 billed 5.10 vs the accepted notice rate 4.79; b2/0036 |
| fbb8b8f9 | overcharge FB-P1 | finding | 65.24 | -/✓ | b1/0025 notice (lane USE2-INW2, also Joaquin, not covered by feedback); MSA 5.55 |
| 3ecb61d3 | overcharge FB-P1 decoy | no_finding | – | -/✓ | billed 4.79 equals the accepted notice rate |
| e25ce214 | overcharge OC-01 | finding | 88.96 | ✓/✓ | 244 kg at 3.14 vs 2.84 |
| c8db301f | overcharge OC-01, INR | finding | 383.13 | -/✓ | IN-MSA P2 column 519.17; Annex F conversion |
| c04b8a91 | OC-01 decoy | no_finding | – | ✓/✓ | 299 kg sits in the 100-299.5 band |
| b7a1aee9 | OC-01 decoy | no_finding | – | -/✓ | fuel 22.36% for a pickup on 2035-08-31 |
| 490f68d0 | OC-02 | finding | 124.02 | ✓/✓ | "DG handling" billed; DGD says "UN1845 Dry ice… refrigerant only"; §5.2 |
| f88fe65b | OC-02 | finding | 124.02 | -/✓ | same pattern, b2/0011 |
| 703db266 | OC-02 decoy | no_finding | – | -/✓ | UN3481 lithium batteries are real DG (§5.3) |
| 78171a40 | XC-01 | conflict | [0.00, 96.36] | -/✓ | AMD-1 3.12 vs Fintan Corrigan (rates contact) notice b2/0003 at 2.80; §13.3 p.5 |
| 6f955cee | XC-02 | cannot_determine | – | -/✓ | AMD-1 item 2 says "Annex A rev 2 (attached)", which is not attached; holder Fintan Corrigan, Pricing Manager |
| 52db5230, 4c5310e6, a6783f61, 6e4f24cd | clean | no_finding | – | ✓✓ / -✓ / -✓ / -✓ | a6783f61 is the scanned invoice; 6e4f24cd is statement TX-ST-203505 with evidence [] |
| 73ed4854 | DU-01 | finding | 1363.36 | ✓/✓ | b1/0041 AP register + b1/0016 resend |
| c635bc71 | DU-01 | finding | 998.56 | -/✓ | b2/0037 + b2/0017 |
| 1d5d4842 | DU-05 decoy | no_finding | – | -/✓ | master 363 kg = H1 117 + H2 246 |
| 472574a9 | WB-01 | finding | 116.13 | ✓/✓ | b1/0004 waiver, MSA p.11, b1/0006 |
| 4e59ec78 | WB-01 | finding | 116.13 | -/✓ | b2/0032 waiver, b2/0035 invoice |
| ddb759a8 | WB-01 decoy | no_finding | – | -/✓ | waiver names TX47649188; the billed AWB is TX88736541 |
| 3874a142 | LF-01 | finding | 13.54 | ✓/✓ | extended to 05-07, paid 05-01 |
| bff95595 | LF-01 | finding | 39.66 | -/✓ | extended to 09-07, paid 09-07 |
| e85d8676 | LF-01 decoy | no_finding | – | ✓/✓ | extended to 04-03, paid 04-10 → 87.33 owed |
| f9cfdf2a | late_fee_risk LF-03 | finding, deadline 2035-10-06 | 19.61 | -/✓ | open invoice, due 6 days after as_of; 1.98% × 990.33 |
| 6f266dbe | CB-01 | finding | 4450.07 | ✓/✓ | MSA p.3–4 |
| 9bb38241 | CB-02 decoy | no_finding | – | ✓/✓ | QS exclusions |
| 88c6ccb5 | EX-01 | finding, deadline 2035-10-19 | – | -/✓ | 19 days out at b2 |

**Actions per mode (supervised / autonomous).** These are the same within each class:
- Overcharge, duplicate, waived_but_billed and late_fee_not_owed findings: `draft:dispute` / `execute:dispute`.
- Cashback: `draft:claim_credit` / `execute:claim_credit`.
- Expiry: `internal:alert` in both modes. Late-fee risk: `internal:payment_reminder` in both.
- Conflict: `escalate` in both. cannot_determine: `draft:request_document` / `execute:request_document`.
- No item is `human_review`; every amount is under $5,000.

**Counts.**
- By class: overcharge 17, duplicate 3, waived_but_billed 3, late_fee_not_owed 3, cashback 2, late_fee_risk 1, expiry 1.
- By verdict: finding 16, no_finding 12 (8 decoys, 4 clean), conflict 1, cannot_determine 1.
- 11 keys appear in the b1 report and 29 in the b2 report.

**Feedback file** (`W1_batch_01.json`): fb-01-p1 is `close` with a `rate_accepted` fact. It is standing, covers contract TBX-US-EXP-01 lane USC3-INS1 only, and is valid 2035-03-13 to 2035-09-25.

**Tricks present in the practice set:**
- Weight-band edge; fuel rate at month end; choosing the P1 or P2 rate column.
- Unauthorised rate sender (Joaquin Rathbone in practice).
- Feedback that applies to exactly one lane (learned_at).
- One amendment-vs-notice conflict; one cannot_determine (named attachment missing).
- Dry ice vs dangerous goods; waiver scope by AWB; master-AWB split; extension edge cases; QS exclusions; the 60-day expiry window; a scanned clean invoice.

**Not in any of the 30 answers:** `supersedes` (always `[]`), `retro`, a waiver seen only as quoted text, a conditional waiver, injection text, and human_review. A keyword sweep of all 119 practice and exam emails found no text aimed at automated readers.

GLOSSARY rules for the missing ones:
- A waiver seen only quoted inside a forward is `cannot_determine`.
- Text addressed to "the AI" is data and is never followed.
- When a new document changes a key already reported, the new item lists the old `id` in `supersedes`.
- A key that exists only because of a backdated document sets `retro: true`.

README lines 61-63 say the hidden set adds a backdated amendment, a waiver meant only once, and emails that try to give orders.

## 3. Practice documents (`data/scenarios/batch_01`)

**Headers.** Every email has From, To, Date, Subject, Message-ID, MIME-Version, `X-GCA-Canary: GCA-0.1.0-CANARY` and Content-Type. Replies add In-Reply-To and References. There are no Cc headers. PDFs carry creator `gca-render` and the canary in keywords.

**MSA** (`0001.eml#MSA-TBX-US-EXP-01.pdf`, 11 pages, 23,187 chars). Page layout:
- p1 cover, p2 contents, p3–7 clauses 1–27 and signatures.
- p8 Annex A: lane × weight band (min, 0-44.5, 45-99.5, 100-299.5, 300+) with separate P1 and P2 rate columns. Annex B is not applicable.
- p9 Annex C: fuel % by pickup month.
- p10 Annex D accessorials (code, fee, basis) and Annex E label aliases (FRT…LATE, e.g. "DG handling", "PSS", "Duty paid on your behalf").
- p11 Annex F and Schedule 1.

Key clauses:
- 1.1 QS definition; 1.2 pickup date comes from the carrier's tracking record.
- 2.2 term ends 2035-10-19; 2.3 no auto-renewal; 2.4 extension only by an instrument both parties sign; 24.2 termination for convenience needs 90 days' notice.
- 3.3 chargeable weight uses /6000 and rounds up to 0.5 kg; 3.5 rate notices only from the rates contact.
- 4.1 fuel applies to base freight only.
- 6.1 storage (5 free days); 6.2 delivery fee only if the carrier delivers; 6.3 customs hold fees are the shipper's unless the carrier caused the hold.
- 7.1 rebate tiers 79k / 120k / 202k at 5 / 7.5 / 10%; 7.3 credit notes due within 45 days; 9.1 improvement credit 1.42%.
- 10.1 net 45; 10.2 late fee 1.98%, grace 0, ceil(days/30) months; 10.3 compounding; 10.5 extension.
- 11.1–11.3 waivers (authority, scope, conditional); 13.1 disputes within 90 days.
- Precedence: §14.1 "Signed amendment > this Agreement > Annexes. Between amendments, the later effective date prevails…". §14.3 "Quoted or forwarded text is not a notice."

**Schedule 1 (US practice):**
- Joaquin Rathbone: notices, billing_disputes (not rates).
- Fintan Corrigan: rates.
- Signe Underhill: waivers, payment_terms.
- Odette Sandoval: treasury.
- Isolde Pembroke (customer side): notices, payment_terms, billing_disputes.
- Sunil Yardley (customer side): rates.

**IN MSA** (0008): INR rates; GST 18% on domestic services; storage 3 free days; late fee 1.09% with 5-day grace; improvement credit 1.00%; a separate Billing Disputes Lead. Annex F holds monthly INR/USD rates 2035-01 to 2036-01, and says "Rows for months after the last row are issued by Treasury as an Annex F update".

**Amendment** (0002, AMD-1, effective 2034-11-11): item 1 replaces the USC3-USS2 rates "for every period"; item 2 points to an "Annex A rev 2 (attached)" that is not attached.

**Invoice layouts (three):**
- **"INVOICE":** columns `No. | AWB | Pickup | Description | Lane | Qty / basis | Rate | Amount (USD)`. On the fuel line, Qty is the base amount and Rate is the %. A late fee appears as a row, e.g. `14 - - Late fee on TX-US-2035-0202: … 1.98% 13.54`. Tax shows "not applicable". Invoices run up to 36 lines on one page (0019) or two pages (0031).
- **"Freight bill"** (batch_02): `Issued on 01 Jul 2035`, `Settle by`, columns `Charge | Shipment | Route | Collected | Net (USD) | Units | Unit price`, "Balance due".
- **INR "TXI/":** shows GSTINs and a SAC code column, with a GST 18% line.

**Other attachments and emails:**
- AWB PDFs give pieces, weights, dimensions, chargeable weight and nature of goods. DGD PDFs give the UN number and class, or "refrigerant only".
- Statement xlsx (0007) uses `Charge | Reference | Quantity | Rate | Amount` for the monthly ACCT/SPROG/PPROG fees, total 1426.5.
- Tracking xlsx: `AWB | Event | Date | Station | Reason code`, 278 rows.
- AP register: `Invoice no. | Invoice date | Due date | Amount | Status | Paid date`. The grader (`grader/extract.py` `_cell_text`) builds the quote form `… | due 2033-03-02 | USD 1259.23 | …` from the cell number-format prefixes.
- Short text-only emails: a waiver thread that quotes the customer's request, extensions ("We extend the due date of invoice X to D."), rate notices ("Under clause 3.5 we give notice… L band: r USD"), a "picked up" status email, and a customs broker email from ashgrove.example (`SHIPPER_PERMIT_MISSING`).

## 4. Exam (`data/exam`)

**Parties.** The customer is Ferrowyn Life Sciences (FWL-US / FWL-IN). The carrier is Caldrith Air Logistics (CDA-US / CDA-IN). AWBs start with CA, documents are dated 2030–31, and reports are run as of 2030-08-31 and 2031-02-28.

**Contracts.** `batch_01/0001.eml` is the CDA-IN-EXP-E91 MSA, which has a 24-month term ending 2032-01-11. `0003` is the CDA-US-EXP-E91 MSA, ending 2031-04-01. Both use the same 27 clauses and the same annex names; §13.3 and §14 are unchanged.

**Reworded clauses:**
- "The Effective Date of this Agreement is…"
- "runs for 12 months and expires on…"
- "does not continue after the initial term unless…"
- "Payment is due 30 days from the date of each invoice"
- "outstanding for more than N days past the due date incur…"
- "No later than 60 days… credit equal to…"

**Parameters:**
- US: late fee 1.49%, grace 0; rebate tiers 77k / 132k / 208k; improvement credit 1.76%; storage 2 free days; no PEAK surcharge.
- IN: late fee 1.74%, grace 10; rebate tiers 54k / 82k / 143k; improvement credit 0.83%.

**Schedule 1, US:**
- Ines Oyelaran: notices.
- **Joaquin Rathbone, Pricing Manager: rates** (the same name was the unauthorised sender in practice).
- Thea Kapadia: waivers, payment_terms.
- Greta Quigley: billing_disputes.

**Invoice layout, "Charges advice":**
- Header fields: `Document date 03/06/2030`, `Payable by`, `Contract`, `Currency`.
- Columns: `Route | Waybill | Charge | Basis | Rate | Amount | Collected`. There are no line numbers and the pickup date (DD/MM/YYYY) is in the last column.
- Amounts use thousands separators (`1,701.31`), tax shows "nil", and the total is labelled "Total payable".
- Invoices include `Import duty (disbursement)` lines. A two-page invoice repeats a "(continued)" header.

**Other exam documents:**
- Waivers: "Please treat the Delivery fee on AWB … as waived." and "…is waived, with our apologies."
- Extension: "now falls due on 2030-07-25 (extended under clause 10.5)."
- Rate notice (b2/0001): "Pursuant to clause 3.5, the rates below apply to lane USE2-USC3 for pickups from 2030-09-15 until 2030-10-10: … = USD 5.08". AMD-1 (b1/0004) also sets USE2-USC3 rates and cites an "Annex A rev 2 (attached)" for USW2-USW1 that is missing.
- Credit note b2/0019: "Annual improvement credit CY1: 0.83% of Qualifying Spend USD 1,640.08 | USD 13.61".
- CDU-3051273 is sent twice (b1/0013 and b1/0017), and the AP register shows it paid.
- There are no statement spreadsheets in the exam.

**Scanned image invoice:** `data/exam/batch_02/0016.eml#CDI-3031-0306.pdf`. It is one page holding one JPEG (1240×1755) with no text layer. It arrives with `AWB-CA68214550.pdf` (INE2→USW1, 274 kg chargeable). The practice equivalent is `data/scenarios/batch_02/0016.eml#TXI-35-36-0024.pdf`, which is a clean control. README line 57 says the exam scan "carries one of the exam's findings". For scans, the grader checks only the page number of a quote, not its text.

## 5. Sizes

| Batch | Emails | With attachments | Attachments (PDF / xlsx) | Text chars | ≈ tokens (chars ÷ 4) |
|---|---|---|---|---|---|
| scenarios b01 | 41 | 32 | 41 (33 / 8) | 99,678 | 25k |
| scenarios b02 | 37 | 32 | 44 (38 / 6, 1 image) | 45,054 | 11k |
| exam b01 | 18 | 15 | 17 (15 / 2) | 67,988 | 17k |
| exam b02 | 23 | 19 | 28 (26 / 2, 1 image) | 32,775 | 8k |

The two MSAs make up about 47.5k chars of each batch_01. Invoice PDFs run about 0.8–4k chars each, and text-only emails about 150–470 chars. The totals leave out the two scanned images, and the xlsx counts include cell values only.
