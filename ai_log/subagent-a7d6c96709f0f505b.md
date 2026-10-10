# Subagent: Research current practice for design

Source: `agent-a7d6c96709f0f505b.jsonl`. Tool results are cut to 1500 characters, tool inputs to 2500. API keys are replaced with a marker. Nothing else is removed.

## User 2026-10-08 16:27:52

Research task, read-only, web only. Do not write any files.

Context: a job candidate (Full Stack AI intern, GoComet Nova team) must build in about 16 hours a Python CLI "harness" of LLM agents that reads a mailbox of emails with PDF/Excel attachments (freight invoices, carrier contracts and amendments, waiver emails), stores facts on disk between batches, and reports findings (overcharges, duplicates, waived-but-billed charges, late fees, rebates owed, contract expiry) with exact USD amounts, verbatim evidence quotes with page numbers, a calibrated confidence in [0,1] scored by AUROC and Brier, conflict detection between sources by authority, missing-document requests, learning from human feedback scoped to exact keys, and prompt-injection resistance (emails that try to give the agents orders). It is graded on a hidden set with new companies and new invoice layouts, so it must read by meaning, not by regex. Only api.anthropic.com is reachable at grading time (Claude models via the `anthropic` Python SDK 1.8.0). OCR option: rapidocr-onnxruntime, or Claude vision.

Find what the field currently does (2025-2026) for each point, with sources (URLs) and one or two lines each. Name what is standard practice versus experimental:
1. LLM structured extraction from invoices and contracts with grounded, verbatim citations: Anthropic's Citations API on documents, structured outputs / tool-use JSON schema with Claude, quote-then-verify patterns. Does the Anthropic Citations feature work with PDF documents and return page numbers? Is it compatible with structured outputs?
2. Architecture pattern "LLM extracts typed facts, deterministic code computes money and rules" versus "LLM reasons end to end", for financial audit or invoice reconciliation. Any published accounts-payable / 3-way-match agent designs.
3. Prompt-injection defense for agents reading untrusted documents: spotlighting / datamarking (Microsoft), dual-LLM pattern (Simon Willison), CaMeL (Google DeepMind 2025), "extraction-only, no tools" designs.
4. Confidence calibration for LLM pipelines when the target metric is AUROC and Brier: verbalized confidence vs feature-based logistic scoring vs self-consistency; known results.
5. Cost: current Claude model ids and per-million-token prices (Haiku, Sonnet, Opus latest), prompt caching discounts, Batch API, to estimate cost per 1,000 documents. Check docs.anthropic.com / platform.claude.com pricing pages.
6. Bitemporal fact stores / event sourcing for "as-of" queries (valid time vs transaction time) in small Python tools: is a JSON or SQLite fact store with received_at and effective dates the standard approach?

Report under 1,200 words with URLs.

**Tool call: ToolSearch**

```json
{
 "query": "select:WebSearch,WebFetch",
 "max_results": 2
}
```

<details><summary>tool result</summary>

```

```
</details>

**Tool call: Skill**

```json
{
 "skill": "claude-api",
 "args": "Research only: current Claude model ids and per-million-token pricing (Haiku, Sonnet, Opus latest), prompt caching discounts, Batch API discount; Citations API with PDF documents (page numbers) and compatibility with structured outputs. No code writing."
}
```

<details><summary>tool result</summary>

```
Launching skill: claude-api
```
</details>

**Tool call: Bash**

```json
{
 "command": "grep -n -i -E \"pricing|citation|batch|caching|structured\" /private/tmp/claude-501/bundled-skills/2.1.293/cb2cadf239e7edf3a9cd298272ba8cb5/claude-api/shared/live-sources.md | head -40; grep -n -i -E \"1\\.25|0\\.1x|10%|2x|multiplier|write|read.*price|\\\\\\$\" /private/tmp/claude-501/bundled-skills/2.1.293/cb2cadf239e7edf3a9cd298272ba8cb5/claude-api/shared/prompt-caching.md | head -30",
 "description": "Find docs URLs and caching price multipliers in skill reference files"
}
```

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/about-claude/pricing",
 "prompt": "List current model IDs with base input, output, 5-minute cache write, 1-hour cache write, cache hit/read prices per million tokens for latest Opus, Sonnet, and Haiku models. Also Batch API discount, and any long-context pricing notes. Quote exact numbers."
}
```

<details><summary>tool result</summary>

```
14:### Models & Pricing
18:| Models Overview | `https://platform.claude.com/docs/en/about-claude/models/overview.md`        | "Extract current model IDs, context windows, and pricing for all Claude models" |
21:| Pricing         | `https://platform.claude.com/docs/en/about-claude/pricing.md`                | "Extract current pricing per million tokens for input and output"               |
22:| Cost Optimization | `https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence.md` | "Extract measured cost levers, cache and batch savings, effort and model cost-per-task comparisons, budget controls, and multi-model guidance" |
33:| Prompt Caching    | `https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md`    | "Extract cache_control usage, pricing benefits, and implementation examples"           |
46:| Batch Processing | `https://platform.claude.com/docs/en/build-with-claude/batch-processing.md` | "Extract batch API endpoints, request format, and polling for results"                                  |
72:| Computer Use   | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool.md`   | "Extract the computer_toolset_20260801 setup (configs, member tools, batch actions, toolset_name on results), the Compatibility matrix, and the migration steps from computer_20251124"             |
85:| Structured Outputs | `https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md` | "Extract output_config
... [9143 more characters]
```
</details>

<details><summary>tool result</summary>

```
---
title: Pricing
url: https://platform.claude.com/docs/en/about-claude/pricing
description: Learn about Anthropic's pricing structure for models and features
---

This page provides detailed pricing information for Anthropic's models and features. All prices are in USD.

For the most current pricing information, visit [claude.com/pricing](https://claude.com/pricing).

## Model pricing

The following table shows pricing for all Claude models:

| Model                                                                                                                                | Base input tokens     | 5m cache writes | 1h cache writes | Cache hits and refreshes | Output tokens          |
| :----------------------------------------------------------------------------------------------------------------------------------- | :-------------------- | :-------------- | :-------------- | :----------------------- | :--------------------- |
| Claude Fable 5.1                                                                                                                     | $10 / MTok            | $12.50 / MTok   | $20 / MTok      | $0.25 / MTok<sup>1</sup> | $50 / MTok             |
| Claude Mythos 5.1 ([limited availability](https://support.claude.com/en/articles/14604842))                                          | $10 / MTok            | $12.50 / MTok   | $20 / MTok      | $0.25 / MTok<sup>1</sup> | $50 / MTok             |
| Claude Fable 5                                       
... [47720 more characters]
```
</details>

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/build-with-claude/citations.md",
 "prompt": "Answer exactly: (1) Do citations work with PDF documents and what location fields are returned (page numbers? 1-indexed? end exclusive?) (2) Is it compatible with structured outputs / output_config.format? Quote the sentence. (3) Do scanned/image-only PDFs support citations? (4) Does cited_text count toward output tokens? (5) Which models support it? (6) Any other limitations (custom content, chunking, Batch, caching). Quote key lines."
}
```

<details><summary>tool result</summary>

```
<persisted-output>
Output too large (73.1KB). Full output saved to: /Users/bakasur/.claude/projects/-Users-bakasur-Desktop-GoComet/cc5afe91-7c25-4a54-b70f-a005ddf58df4/tool-results/toolu_0144ZenAyFvH8rrbsETd2aiY.txt

Preview (first 2KB):
---
title: Citations
url: https://platform.claude.com/docs/en/build-with-claude/citations
description: Ground Claude's responses in your source documents. Citations return the exact passages that support each claim, so you can verify answers and surface sources to your users.
featureMetadata:
  status: ga
  zdr:
    eligibility: eligible
    note: Excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements).
  supportedPlatforms:
    Claude API: ga
    Claude Platform on AWS: ga
    Amazon Bedrock: ga
    Google Cloud: ga
    Microsoft Foundry: ga
---

Claude can provide detailed citations when answering questions about documents, helping you track and verify the sources behind each response.

All [active models](https://platform.claude.com/docs/en/models/overview) support citations.

<Tip>
  Share your feedback and suggestions about the citations feature using the [citations feedback form](https://forms.gle/9n9hSrKnKe3rpowH9).
</Tip>

The following example shows how to enable citations on a plain text document with the Messages API:

<CodeGroup>
  ```bash cURL
  curl https://api.anthropic.com/v1/messages \
    -H "content-type: application/json" \
    -H "x-api
... [756 more characters]
```
</details>

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/build-with-claude/pdf-support.md",
 "prompt": "Extract: how PDFs are processed (text plus page images?), token cost per page estimates, page/size limits, whether citations and Batch/caching work with PDFs, and any notes about scanned PDFs. Quote numbers."
}
```

<details><summary>tool result</summary>

```
<persisted-output>
Output too large (60.6KB). Full output saved to: /Users/bakasur/.claude/projects/-Users-bakasur-Desktop-GoComet/cc5afe91-7c25-4a54-b70f-a005ddf58df4/tool-results/toolu_01Nhe4sY4hTDqxMECQnmhJkK.txt

Preview (first 2KB):
---
title: PDF support
url: https://platform.claude.com/docs/en/build-with-claude/pdf-support
description: "Process PDFs with Claude: extract text, analyze charts, and understand visual content from your documents."
featureMetadata:
  status: ga
  zdr:
    eligibility: eligible
    note: Excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements).
  supportedPlatforms:
    Claude API: ga
    Claude Platform on AWS: ga
    Amazon Bedrock: ga
    Google Cloud: ga
    Microsoft Foundry: ga
---

You can ask Claude about any text, pictures, charts, and tables in PDFs you provide. Some sample use cases:

* Analyzing financial reports and understanding charts/tables
* Extracting key information from legal documents
* Assisting with document translation
* Converting document information into structured formats

## Before you begin

### Check PDF requirements

Claude works with any standard PDF. Ensure your request size meets these requirements:

| Requirement               | Limit                                                                                              |
| ------------------------- | ------------------------------------------------------------------
... [733 more characters]
```
</details>

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md",
 "prompt": "Extract: how output_config.format and strict tool use work, which models, JSON schema limitations (unsupported features like minimum/maximum, regex patterns, recursion), incompatibilities (citations, prefill, etc.), and whether it is GA or beta. Quote key incompatibility lines."
}
```

<details><summary>tool result</summary>

```
## Summary

**Status:** GA. The page metadata lists `status: ga` for structured outputs. Availability is GA on the Claude API, Claude Platform on AWS, Google Cloud, and Microsoft Foundry. On Amazon Bedrock it is GA only on the legacy Bedrock integration (Opus 4.6 and earlier), not on Claude in Amazon Bedrock. ZDR eligibility is "eligible," excluding Covered Models.

**Supported models:** claude-fable-5-1, claude-mythos-5-1, claude-fable-5, claude-mythos-5, claude-mythos-preview, claude-opus-5-5, claude-opus-5, claude-opus-4-8, claude-opus-4-7, claude-opus-4-6, claude-sonnet-5-5, claude-sonnet-5, claude-sonnet-4-6, claude-sonnet-4-5-20250929, claude-opus-4-5-20251101, claude-haiku-5-5, claude-haiku-4-5-20251001.

## The two features

- **JSON outputs (`output_config.format`)**: Claude's response text is constrained to a JSON schema.
- **Strict tool use (`strict: true`)**: tool names and inputs are schema-validated. Details are on the separate strict tool use page.

They can be combined in one request. The page says JSON outputs control "what Claude says," while strict tool use validates "how Claude calls your functions."

```json
"output_config": {
  "format": {
    "type": "json_schema",
    "schema": {
      "type": "object",
      "properties": { "name": {"type": "string"} },
      "required": ["name"],
      "additionalProperties": false
    }
  }
}
```

**Migration:** `output_format` is deprecated. The page says it "will be removed in the future," and that the `structured
... [2918 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "F=/Users/bakasur/.claude/projects/-Users-bakasur-Desktop-GoComet/cc5afe91-7c25-4a54-b70f-a005ddf58df4/tool-results/toolu_0144ZenAyFvH8rrbsETd2aiY.txt; grep -n -i -E \"page_location|page number|1-indexed|exclusive|structured output|output_config|incompatib|400|scanned|image|output token|cited_text|chunk|custom content|batch|cach\" \"$F\" | head -60",
 "description": "Grep saved citations doc for PDF page and compatibility details"
}
```

**Tool call: Bash**

```json
{
 "command": "F=/Users/bakasur/.claude/projects/-Users-bakasur-Desktop-GoComet/cc5afe91-7c25-4a54-b70f-a005ddf58df4/tool-results/toolu_01Nhe4sY4hTDqxMECQnmhJkK.txt; grep -n -i -E \"tokens per page|per page|1,500|3,000|image|scanned|citation|text extract|each page\" \"$F\" | head -40",
 "description": "Grep saved PDF support doc for token cost and processing details"
}
```

<details><summary>tool result</summary>

```
315:  * **Cost savings:** If your prompt-based approach asks Claude to output direct quotes, you may see cost savings because `cited_text` does not count toward your output tokens.
316:  * **Better citation reliability:** Because the API parses citations into the response formats described in the following sections and extracts `cited_text` directly, citations are guaranteed to contain valid pointers to the provided documents.
328:    * Include documents in any of the supported formats: [PDFs](https://platform.claude.com/docs/en/build-with-claude/citations#pdf-documents), [plain text](https://platform.claude.com/docs/en/build-with-claude/citations#plain-text-documents), or [custom content](https://platform.claude.com/docs/en/build-with-claude/citations#custom-content-documents) documents.
330:    * Only text citations are currently supported. Image citations are not yet possible.
334:    * Document contents are "chunked" to define the minimum granularity of possible citations. For example, sentence chunking lets Claude cite a single sentence or chain together multiple consecutive sentences to cite a paragraph or longer passage.
336:      * **For PDFs:** Text is extracted as described in [PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) and content is chunked into sentences. Citing images from PDFs is not currently supported.
337:      * **For plain text documents:** Content is chunked into sentences that can be cited from.
338:      * **For cust
... [6095 more characters]
```
</details>

<details><summary>tool result</summary>

```
40:  Dense PDFs (many small-font pages, complex tables, or heavy graphics) can fill the context window before reaching the page limit. Requests with large PDFs can also fail before reaching the page limit, even when using the Files API. Try splitting the document into sections; for large files, because each page is processed as an image, downsampling embedded images can also help.
54:  **Important:** To access Claude's full visual PDF understanding capabilities in the Converse API, you must enable citations. Without citations enabled, the API falls back to basic text extraction only. Learn more about [working with citations](https://platform.claude.com/docs/en/build-with-claude/citations).
59:1. **Converse Document Chat** (Original mode - Text extraction only)
61:   * Provides basic text extraction from PDFs
62:   * Cannot analyze images, charts, or visual layouts within PDFs
64:   * Automatically used when citations are not enabled
69:   * Can understand and analyze charts, graphs, images, and visual layouts
70:   * Processes each page as both text and image for comprehensive understanding
72:   * **Requires citations to be enabled** in the Converse API
76:* **Converse API:** Visual PDF analysis requires citations to be enabled. There is currently no option to use visual analysis without citations (unlike the InvokeModel API).
77:* **InvokeModel API:** Provides full control over PDF processing without forced citations.
81:If Claude isn't seeing images or charts in your PDFs 
... [1390 more characters]
```
</details>

**Tool call: WebSearch**

```json
{
 "query": "CaMeL \"Defeating Prompt Injections by Design\" DeepMind arXiv 2503.18813",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "Microsoft spotlighting datamarking encoding prompt injection Hines 2024 arXiv",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "\"Design Patterns for Securing LLM Agents against Prompt Injections\" 2025 plan-then-execute dual LLM",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "Simon Willison dual LLM pattern prompt injection quarantined privileged",
 "mode": "standard"
}
```

<details><summary>tool result</summary>

```
Web search results for query: ""Design Patterns for Securing LLM Agents against Prompt Injections" 2025 plan-then-execute dual LLM"

Links: [{"title":"Design Patterns for Securing LLM Agents against Prompt Injections","url":"https://arxiv.org/pdf/2506.08837"},{"title":"alphaxiv.org","url":"https://alphaxiv.org/overview/2506.08837v3"},{"title":"huggingface.co","url":"https://huggingface.co/papers/2506.08837"},{"title":"arxiv.org","url":"https://arxiv.org/abs/2506.08837v3"},{"title":"Simon Willison’s Weblog","url":"https://feeds.simonwillison.net/random/paper-review/"},{"title":"Design Patterns for Securing LLM Agents","url":"https://arxiv.org/html/2506.08837v1"},{"title":"Simon Willison’s Weblog","url":"https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/"},{"title":"www.emergentmind.com","url":"https://www.emergentmind.com/papers/2506.08837"},{"title":"Design Patterns for Securing LLM Agents against Prompt Injections","url":"https://conffab.com/elsewhere/design-patterns-for-securing-llm-agents-against-prompt-injections/"},{"title":"Design Patterns for Securing LLM Agents against Prompt Injections","url":"https://conffab.com/?p=8518"}]

Links: [{"title":"Design Patterns for Securing LLM Agents against Prompt Injections","url":"https://arxiv.org/pdf/2506.08837"},{"title":"[Papierüberprüfung] Architecting Resilient LLM Agents: A Guide to Secure Plan-then-Execute Implementations","url":"https://www.themoonlight.io/de/review/architecting-resilient-llm-agents-a-g
... [4327 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "Microsoft spotlighting datamarking encoding prompt injection Hines 2024 arXiv"

Links: [{"title":"License: CC BY 4.0","url":"https://arxiv.org/html/2403.14720v1"},{"title":"ceur-ws.org","url":"https://ceur-ws.org/Vol-3920/paper03.pdf"},{"title":"spotlighting datamarking","url":"https://github.com/realArcherL/spotlighting-datamarking"},{"title":"Defending Against Indirect Prompt Injection Attacks With Spotlighting","url":"https://www.microsoft.com/en-us/research/?p=1124166"},{"title":"cs.CLcs.LG25 Mar 2024","url":"https://chatpaper.com/de/paper/2969"},{"title":"arxiv.org","url":"https://arxiv.org/abs/2403.14720v1"},{"title":"[Papierüberprüfung] Defending Against Indirect Prompt Injection Attacks With Spotlighting","url":"https://www.themoonlight.io/de/review/defending-against-indirect-prompt-injection-attacks-with-spotlighting"},{"title":"[Literature Review] Defending Against Indirect Prompt Injection Attacks With Spotlighting","url":"https://www.themoonlight.io/en/review/defending-against-indirect-prompt-injection-attacks-with-spotlighting"},{"title":"Cyber Security News","url":"https://cybersecuritynews.com/indirect-prompt-injection-mitigations/amp/"},{"title":"[Literature Review] Defending Against Indirect Prompt Injection Attacks With Spotlighting","url":"https://themoonlight.io/review/defending-against-indirect-prompt-injection-attacks-with-spotlighting"}]

The paper is **arXiv:2403.14720**, "Defending Against Indirect Prompt Injection Attac
... [1997 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "CaMeL "Defeating Prompt Injections by Design" DeepMind arXiv 2503.18813"

Links: [{"title":"Defeating Prompt Injections by Design","url":"https://arxiv.org/pdf/2503.18813"},{"title":"arxiv.org","url":"https://arxiv.org/abs/2503.18813"},{"title":"css.csail.mit.edu","url":"https://css.csail.mit.edu/6.858/2026/readings/camel.pdf"},{"title":"[論文評述] Defeating Prompt Injections by Design","url":"https://www.themoonlight.io/tw/review/defeating-prompt-injections-by-design"},{"title":"[Revisión de artículo] Defeating Prompt Injections by Design","url":"https://www.themoonlight.io/es/review/defeating-prompt-injections-by-design"},{"title":"[Literature Review] Defeating Prompt Injections by Design","url":"https://www.themoonlight.io/review/defeating-prompt-injections-by-design"},{"title":"Daily Arxiv","url":"https://slashpage.com/haebom/1q3vdn2p9169gmxy49pr?tl=en"},{"title":"[Papierüberprüfung] Defeating Prompt Injections by Design","url":"https://www.themoonlight.io/de/review/defeating-prompt-injections-by-design"},{"title":"defeating prompt injections by design","url":"https://sotaverified.org/papers/defeating-prompt-injections-by-design"},{"title":"CaMeL Security Demonstration - Defending Against (most) Prompt Injections by Design","url":"https://radar.offseq.com/threat/camel-security-demonstration-defending-against-mos-1d19037f"}]

The paper is arXiv:2503.18813, **"Defeating Prompt Injections by Design,"** in the cs.CR category. Submitted on 24 Mar 202
... [2446 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "Simon Willison dual LLM pattern prompt injection quarantined privileged"

Links: [{"title":"Design Patterns for Securing LLM Agents against Prompt Injections","url":"https://arxiv.org/pdf/2506.08837"},{"title":"Simon Willison’s Weblog","url":"https://simonwillison.net/2023/Apr/25/dual-llm-pattern/"},{"title":"Simon Willison’s Weblog","url":"https://feeds.simonwillison.net/2023/Apr/25/dual-llm-pattern/"},{"title":"Simon Willison’s Weblog","url":"https://simonwillison.net/2025/apr/11/camel/"},{"title":"Simon Willison’s Weblog","url":"https://simonwillison.net/2025/Apr/11/camel/"},{"title":"Simon Willison’s Weblog","url":"https://feeds.simonwillison.net/2025/Apr/11/camel"},{"title":"Get the latest, first","url":"https://www.armosec.io/blog/design-patterns-for-securing-llm-agents/"},{"title":"This Guy Invented A Simple Way to Fight Prompt Injection: DualLLM","url":"https://blog.finxter.com/this-guy-invented-a-simple-way-to-fight-prompt-injection-dualllm/"},{"title":"a tale of two llms safety vs. complexity","url":"https://protectai.com/blog/a-tale-of-two-llms-safety-vs.-complexity"},{"title":"a tale of two llms safety vs. complexity","url":"https://protectai.com/test-blog/blog/a-tale-of-two-llms-safety-vs.-complexity"}]

Willison put forward this idea in April 2023 as a defense against prompt injection attacks.

**The two models**
- **Privileged LLM:** This model sits at the center of the system. Its instructions come from the user and other trusted
... [2220 more characters]
```
</details>

**Tool call: WebSearch**

```json
{
 "query": "Xiong \"Can LLMs Express Their Uncertainty\" verbalized confidence overconfident AUROC consistency hybrid ICLR 2024",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "2025 study verbalized confidence vs sampling consistency calibration Brier AUROC LLM extraction post-hoc Platt isotonic recalibration",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "LLM invoice reconciliation three-way match agent architecture deterministic rules LLM extraction accounts payable 2025",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "freight audit AI agent invoice contract rate verification LLM extraction deterministic rules engine 2025",
 "mode": "standard"
}
```

<details><summary>tool result</summary>

```
Web search results for query: "Xiong "Can LLMs Express Their Uncertainty" verbalized confidence overconfident AUROC consistency hybrid ICLR 2024"

Links: [{"title":"Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs","url":"https://arxiv.org/pdf/2306.13063"},{"title":"Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs","url":"https://slideslive.com/39017634/can-llms-express-their-uncertainty-an-empirical-evaluation-of-confidence-elicitation-in-llms"},{"title":"Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs","url":"https://slideslive.com/39017634/can-llms-express-their-uncertainty-an-empirical-evaluation-of-confidence-elicitation-in-llms?locale=cs"},{"title":"Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs","url":"https://slideslive.com/39017634"},{"title":"can llms express their uncertainty an empirical evaluation of con","url":"https://researchportal.hkust.edu.hk/en/publications/can-llms-express-their-uncertainty-an-empirical-evaluation-of-con/?"},{"title":"Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs","url":"https://iclr.cc/virtual/2024/poster/18135"},{"title":"arxiv.org","url":"https://arxiv.org/abs/2306.13063v2"},{"title":"arxiv.org","url":"https://arxiv.org/pdf/2503.14749v2"},{"title":"Can LLMs Express Their Uncertainty? an Empirical Evaluation of
... [5630 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "2025 study verbalized confidence vs sampling consistency calibration Brier AUROC LLM extraction post-hoc Platt isotonic recalibration"

Links: [{"title":"Pinocchio: Fast Uncertainty Estimates for Black-Box Language Models","url":"https://arxiv.org/pdf/2609.24881"},{"title":"Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs","url":"https://arxiv.org/pdf/2306.13063"},{"title":"When Can We Trust LLM Graders? Calibrating Confidence for Automated Assessment","url":"https://www.alphaxiv.org/abs/2603.29559"},{"title":"www.emergentmind.com","url":"https://www.emergentmind.com/papers/2604.19444"},{"title":"License: CC BY 4.0","url":"https://arxiv.org/html/2603.29559v1"},{"title":"arxiv.org","url":"https://arxiv.org/pdf/2402.13904v2"},{"title":"arxiv.org","url":"https://arxiv.org/pdf/2603.29559"},{"title":"evaluating llm confidence uncertainty 2026","url":"https://futureagi.com/blog/evaluating-llm-confidence-uncertainty-2026/"},{"title":"calibrating large language models with sample consistency  c93d278a","url":"https://object.cloud.sdsc.edu/v1/AUTH_da4962d3368042ac8337e2dfdd3e7bf3/ml-papers/AAAI/2025/calibrating_large_language_models_with_sample_consistency__c93d278a.pdf"}]

No single result matched every part of your query. I didn't find a 2025 study that compares verbalized and sampling-based confidence on LLM extraction tasks, with Platt and isotonic recalibration scored by Brier and AUROC. The closest match
... [3102 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "LLM invoice reconciliation three-way match agent architecture deterministic rules LLM extraction accounts payable 2025"

Links: [{"title":"Three-Way Matching Services","url":"https://www.gravitee.io/corpus/gen-1938/procure-to-pay/three-way-matching-services.html"},{"title":"Three-Way Matching Automation: Controls, Workflows, and AI Agent Governance","url":"https://gravitee.io/corpus/gen-2446/purchase-to-pay/three-way-matching-automation.html"},{"title":"Invoice Processing Agents","url":"https://gravitee.io/corpus/gen-2446/purchase-to-pay/invoice-processing-agents.html"},{"title":"labs.boomi.com","url":"https://labs.boomi.com/labs/financial-operations/invoice-reconciliation/intro"},{"title":"ai invoice reconciliation agent","url":"https://cassidyai.com/solutions/ai-invoice-reconciliation-agent"},{"title":"Finance and Procurement","url":"https://www.entrans.ai/case-study/ai-invoice-grn-reconciliation-enterprise-finance"},{"title":"Three-Way Matching Automation: Controls, Workflows, and AI Agent Governance","url":"https://26fba7053f.geosurge.ai/corpus/gen-2446/purchase-to-pay/three-way-matching-automation.html"},{"title":"autonomous agentic back office invoice matching payment","url":"https://dailyaiworld.com/workflow/autonomous-agentic-back-office-invoice-matching-payment"},{"title":"autonomous agentic back office invoice matching payment","url":"https://dailyaiworld.com/public/workflow/autonomous-agentic-back-office-invoice-matching-payment"}]

L
... [6926 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "freight audit AI agent invoice contract rate verification LLM extraction deterministic rules engine 2025"

Links: [{"title":"ai freight audit bill","url":"https://smartdev.com/de/ai-freight-audit-bill/"},{"title":"ai freight audit bill","url":"https://smartdev.com/ai-freight-audit-bill/"},{"title":"ai freight audit bill","url":"https://smartdev.com/kr/ai-freight-audit-bill/"},{"title":"ai freight audit bill","url":"https://smartdev.com/jp/ai-freight-audit-bill/"},{"title":"ai freight audit bill","url":"https://smartdev.com/fr/ai-freight-audit-bill/"},{"title":"freight invoicing and audit","url":"https://www.stacksync.com/use-case/freight-invoicing-and-audit"},{"title":"AI-Powered Freight Audit: Slash Logistics Billing Errors and Automate Invoice Reconciliation","url":"https://delos.so/blog/ai-freight-audit-logistics-optimization"},{"title":"LogisticsFreight Invoice Auditing","url":"https://www.agentui.ai/en/use-cases/logistics/freight-invoice-auditing"},{"title":"The Autonomous Audit: How AI is Catching Freight Invoice Errors in Real-Time","url":"https://racklify.com/encyclopedia/the-autonomous-audit-how-ai-is-catching-freight-invoice-errors-in-real-time"}]

Links: [{"title":"Invoice Information Extraction: Methods and Performance Evaluation","url":"https://arxiv.org/pdf/2510.15727"},{"title":"Automated Invoice Data Extraction: Using LLM and OCR","url":"https://arxiv.org/pdf/2511.05547"},{"title":"mm.linkedin.com","url":"https://mm.linkedin.com/
... [8033 more characters]
```
</details>

**Tool call: WebSearch**

```json
{
 "query": "APRICOT \"Calibrating Large Language Models Using Their Generations Only\" auxiliary model predicts correctness",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "Tian 2023 \"Just Ask for Calibration\" verbalized confidence RLHF models better calibrated than token probabilities",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "bitemporal data model valid time transaction time Python SQLite event sourcing as-of query library",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "Anthropic docs mitigate prompt injection untrusted documents Claude guidance 2026",
 "mode": "standard"
}
```

<details><summary>tool result</summary>

```
Web search results for query: "Tian 2023 "Just Ask for Calibration" verbalized confidence RLHF models better calibrated than token probabilities"

Links: [{"title":"Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with Human Feedback","url":"https://arxiv.org/pdf/2305.14975"},{"title":"arxiv.org","url":"https://arxiv.org/pdf/2305.14975v1"},{"title":"Allan Zhou","url":"https://aclanthology.org/people/allan-zhou/"},{"title":"Allan Zhou","url":"https://aclanthology.org/people/allan-zhou/unverified/"},{"title":"Katherine Tian","url":"https://aclanthology.org/people/katherine-tian/unverified/"},{"title":"Archit Sharma","url":"https://aclanthology.org/people/archit-sharma/unverified/"},{"title":"ar5iv.labs.arxiv.org","url":"https://ar5iv.labs.arxiv.org/html/2305.14975"},{"title":"just ask for calibration strategies for","url":"https://sotaverified.org/papers/just-ask-for-calibration-strategies-for"},{"title":"awesomepapers.io","url":"https://awesomepapers.io/large-language-models/publications/tian2023just"},{"title":"2023.emnlp main.330","url":"https://preview.aclanthology.org/setup/2023.emnlp-main.330"}]

The paper is by Katherine Tian, Eric Mitchell, and colleagues at Harvard and Stanford, and it appeared at EMNLP 2023 (pages 5433–5442).

**Motivation:** Pretrained models' token-level probabilities are generally well calibrated, but some studies have suggested that RLHF-LMs produce conditional probabilities that are v
... [2288 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "APRICOT "Calibrating Large Language Models Using Their Generations Only" auxiliary model predicts correctness"

Links: [{"title":"Calibrating Large Language Models Using Their Generations Only","url":"https://arxiv.org/pdf/2403.05973"},{"title":"calibrating large language models using their generations only","url":"https://pure.itu.dk/en/publications/calibrating-large-language-models-using-their-generations-only/"},{"title":"Calibrating Large Language Models Using Their Generations Only","url":"https://www.academia.edu/124666226/Calibrating_Large_Language_Models_Using_Their_Generations_Only"},{"title":"[Revue de papier] Calibrating Large Language Models Using Their Generations Only","url":"https://www.themoonlight.io/fr/review/calibrating-large-language-models-using-their-generations-only"},{"title":"[Literature Review] Calibrating Large Language Models Using Their Generations Only","url":"https://www.themoonlight.io/en/review/calibrating-large-language-models-using-their-generations-only"},{"title":"arxiv.org","url":"https://arxiv.org/abs/2403.05973?context=cs"},{"title":"Calibrating Large Language Models Using Their Generations Only","url":"https://liner.com/review/calibrating-large-language-models-using-their-generations-only"},{"title":"Calibrating Large Language Models Using Their Generations Only","url":"https://preview.aclanthology.org/setup/2024.acl-long.824"},{"title":"Calibrating Large Language Models Using Their Generations Only","url
... [2215 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "Anthropic docs mitigate prompt injection untrusted documents Claude guidance 2026"

Links: [{"title":"• Messages","url":"https://platform.claude.com/docs/en/docs/mitigating-jailbreaks-prompt-injections"},{"title":"what is a prompt injection attack","url":"https://www.tavus.io/blog/what-is-a-prompt-injection-attack"},{"title":"AI, News, and Ethics","url":"https://www.tavus.io/post/what-is-a-prompt-injection-attack"},{"title":"www.mintlify.com","url":"https://www.mintlify.com/asgeirtj/system_prompts_leaks/anthropic/injections"},{"title":"How does Anthropic mitigate prompt injections?","url":"https://answers.securityscientist.net/q/9032/how-does-anthropic-mitigate-prompt-injections"},{"title":"Mitigate jailbreaks and prompt injections","url":"https://platform.claude.com/docs/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks"},{"title":"ant1102711103125 anthropic vulnerability october 2025","url":"https://blog.rankiteo.com/ant1102711103125-anthropic-vulnerability-october-2025/"},{"title":"mitigate jailbreaks","url":"https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks.md"},{"title":"ai agent security prompt injection token flooding","url":"https://www.mindstudio.ai/blog/ai-agent-security-prompt-injection-token-flooding"}]

The most authoritative result is Anthropic's official guide, "Mitigate jailbreaks and prompt injections," on platform.claude.com. I didn't find a 2026-specific revision in these
... [2904 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "bitemporal data model valid time transaction time Python SQLite event sourcing as-of query library"

Links: [{"title":"github.com","url":"https://github.com/elh/bitempura"},{"title":"pypi.org","url":"https://pypi.org/project/bth5/0.0.1/"},{"title":"awesome.ecosyste.ms","url":"https://awesome.ecosyste.ms/projects/github.com%2Felh%2Fbitempura"},{"title":"pkg.go.dev","url":"https://pkg.go.dev/github.com/elh/bitempura@v0.2.3"},{"title":"pkg.go.dev","url":"https://pkg.go.dev/github.com/elh/bitempura@v0.2.0"},{"title":"awesome.ecosyste.ms","url":"https://awesome.ecosyste.ms/projects/github.com%2Fverberktstan%2Fbitten"},{"title":"elk 22 2 19 1207 100","url":"https://aj.tubitak.gov.tr/elektrik/issues/elk-14-22-2/elk-22-2-19-1207-100.pdf"},{"title":"vldb.org","url":"https://vldb.org/vldb_journal/index.php/component/article_manager/article/685"},{"title":"Harness-engineering db-temporal-data","url":"https://openskillindex.com/skills/intense-visions-harness-engineering-db-temporal-data-d1c92f"}]

Links: [{"title":"Expand description","url":"https://docs.rs/bitemporal-runtime"},{"title":"pypi.org","url":"https://pypi.org/project/kang/"},{"title":"as of","url":"https://piccolo-orm.readthedocs.io/en/1.35.0/piccolo/query_clauses/as_of.html"},{"title":"as of","url":"https://piccolo-orm.readthedocs.io/en/1.2.0/piccolo/query_clauses/as_of.html"},{"title":"searchable timestamps","url":"https://github.com/johnbywater/eventsourcing/blob/v9.2.11/docs/topics/examples/
... [4269 more characters]
```
</details>

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks.md",
 "prompt": "Quote verbatim the recommendations for indirect prompt injection from documents/tool results: where to place untrusted content (tool_result blocks?), labeling, system prompt policy, any mention of spotlighting, datamarking, dual-LLM, least privilege, or classifiers. Keep it short."
}
```

<details><summary>tool result</summary>

```
---
title: Mitigate jailbreaks and prompt injections
url: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks
description: Defend your application against jailbreaks and prompt injection with input screening, hardened system prompts, and safe handling of untrusted tool content.
---

Jailbreaking and prompt injection are attempts to make Claude ignore its guidelines or your instructions. While Claude is inherently resilient to such attacks, the additional steps on this page strengthen your guardrails, particularly against uses that violate Anthropic's [Terms of Service](https://www.anthropic.com/legal/commercial-terms) or [Usage Policy](https://www.anthropic.com/legal/aup).

These attacks fall into two categories with different threat models:

* **Jailbreaks and direct prompt injection**, where the *user* of your application is the adversary and crafts inputs intended to bypass your guardrails.
* **Indirect prompt injection**, where the user is trusted but Claude processes *third-party content* (web pages, emails, documents, tool results) that contains adversarial instructions.

## Jailbreaks and direct prompt injection

In this threat model, a user is deliberately crafting inputs to manipulate your application into producing content or taking actions you don't want it to. These mitigations strengthen your application's guardrails:

* **Harmlessness screens:** Use a lightweight model like Claude Haiku 5.5 to pre-screen user input bef
... [10998 more characters]
```
</details>

**Tool call: WebSearch**

```json
{
 "query": "Martin Fowler bitemporal history valid time record time",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "Anthropic \"Building effective agents\" workflows vs agents simplest solution",
 "mode": "standard"
}
```

<details><summary>tool result</summary>

```
Web search results for query: "Martin Fowler bitemporal history valid time record time"

Links: [{"title":"Bitemporal History","url":"https://www.martinfowler.com/articles/bitemporal-history.html"},{"title":"Article icon","url":"https://www.dataversity.net/?p=6839"},{"title":"Article icon","url":"https://www.dataversity.net/articles/bitemporal-data-modeling-learn-history/"},{"title":"Article icon","url":"https://www.dataversity.net/bitemporal-data-modeling-learn-history/"},{"title":"bitemporality more than a design pattern","url":"https://juxt.pro/blog/bitemporality-more-than-a-design-pattern"},{"title":"Bitemporal History","url":"https://www.goodreads.com/author_blog_posts/21166503-bitemporal-history?tab=book"},{"title":"www.infoq.com","url":"https://www.infoq.com/news/2008/01/bitemporal"},{"title":"EMF Temporality","url":"https://wiki.eclipse.org/images/6/62/EMF-Temporality.pdf"},{"title":"20071107195752%21EMF Temporality","url":"https://wiki.eclipse.org/images/archive/6/62/20071107195752%21EMF-Temporality.pdf"}]

Martin Fowler's main piece on this is his article ["Bitemporal History"](https://www.martinfowler.com/articles/bitemporal-history.html), dated 07 April 2021. I only saw excerpts, so the points below come from those excerpts and from secondary sources that quote Fowler.

**The core idea**
- The model splits time into two tracks: one for the true timeline of events and one for when the system learned about them. Bitemporal history treats time as two dimensions: actu
... [2188 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "Anthropic "Building effective agents" workflows vs agents simplest solution"

Links: [{"title":"mer.vin","url":"https://mer.vin/category/ai/news/page/9/"},{"title":"Anthropic’s Research on GenAI Building Blocks","url":"https://cobusgreyling.substack.com/p/anthropics-research-on-genai-building"},{"title":"• Biweekly Engineering","url":"https://biweekly-engineering.beehiiv.com/p/building-effective-agents-lessons-from-anthropic-biweekly-engineering-episode-37"},{"title":"when not to build ai agents anthropics workflow vs agent playbook","url":"https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/"},{"title":"when not to build ai agents anthropics workflow vs agent playbook","url":"https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/?amp=1"},{"title":"Building effective agents","url":"https://scrapbox.io/nikkie-memos/Building effective agents"},{"title":"Anthropic Revealed Secrets to Building Powerful Agents","url":"https://videohighlight.com/v/0v7TQIh_kes"},{"title":"building effective agents","url":"https://www.aihero.dev/building-effective-agents"},{"title":"Engineering at Anthropic","url":"https://www.anthropic.com/research/building-effective-agents"}]

Links: [{"title":"Anthropic’s Research on GenAI Building Blocks","url":"https://cobusgreyling.substack.com/p/anthropics-research-on-genai-building"},{"title":"Building Effective Agents","url":"https://docs.latitude.so/exam
... [4128 more characters]
```
</details>

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations.md",
 "prompt": "Quote the recommendations about extracting direct quotes first, verifying with citations / retracting claims without supporting quotes, allowing \"I don't know\", and best-of-N verification. Short."
}
```

<details><summary>tool result</summary>

```
---
title: Reduce hallucinations
url: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
description: Minimize hallucinations in Claude's outputs by allowing uncertainty, grounding responses in direct quotes, and verifying claims with citations.
---

Even the most advanced language models, like Claude, can sometimes generate text that is factually incorrect or inconsistent with the given context. This phenomenon, known as "hallucination," can undermine the reliability of your AI-driven solutions. This guide will explore techniques to minimize hallucinations and ensure Claude's outputs are accurate and trustworthy.

## Basic hallucination minimization strategies

* **Allow Claude to say "I don't know":** Explicitly give Claude permission to admit uncertainty. This simple technique can drastically reduce false information.

<Accordion title="Example: Analyzing a merger & acquisition report">
  ```text User wrap
  As our M&A advisor, analyze this report on the potential acquisition of AcmeCo by ExampleCorp.

  <report>
  {{REPORT}}
  </report>

  Focus on financial projections, integration risks, and regulatory hurdles. If you're unsure about any aspect or if the report lacks necessary information, say "I don't have enough information to confidently assess this."
  ```
</Accordion>

* **Use direct quotes for factual grounding:** For tasks involving long documents (>20k tokens), ask Claude to extract word-for-word quotes first before
... [2517 more characters]
```
</details>

**Tool call: WebSearch**

```json
{
 "query": "PAL Program-aided Language Models Gao 2022 offload arithmetic to Python interpreter",
 "mode": "standard"
}
```

**Tool call: WebSearch**

```json
{
 "query": "LLM calibration selective prediction structured extraction field-level confidence logistic regression features agreement 2025 document extraction",
 "mode": "standard"
}
```

<details><summary>tool result</summary>

```
Web search results for query: "PAL Program-aided Language Models Gao 2022 offload arithmetic to Python interpreter"

Links: [{"title":"PAL: Program-aided Language Models","url":"https://deepai.org/publication/pal-program-aided-language-models"},{"title":"arxiv.org","url":"https://arxiv.org/abs/2211.10435v1"},{"title":"PAL: Program-aided Language Models","url":"https://cdnjs.deepai.org/publication/pal-program-aided-language-models"},{"title":"Quick review","url":"https://liner.com/review/pal-programaided-language-models"},{"title":"icml.cc","url":"https://icml.cc/virtual/2023/poster/23864"},{"title":"github.com","url":"https://github.com/reasoning-machines/pal"},{"title":"PAL: Program-aided Language Models","url":"https://api.deepai.org/publication/pal-program-aided-language-models"},{"title":"par.nsf.gov","url":"https://par.nsf.gov//servlets/purl/10479607"},{"title":"science.ecosyste.ms","url":"https://science.ecosyste.ms/projects/10117"},{"title":"Our new X account is live! Follow @wizwand_team for updates","url":"https://www.wizwand.com/paper/68fa6e771e209131cea400b7"}]

**Yes, that's the core idea of the paper.** Gao et al. (arXiv:2211.10435, submitted 18 Nov 2022) have the LLM write code as its reasoning steps and hand execution to a Python interpreter, so the model doesn't do the calculating itself.

**The problem they targeted**
The authors observed that models can break a problem into the right steps yet still make logic or arithmetic errors when solving each step. Whi
... [2689 more characters]
```
</details>

<details><summary>tool result</summary>

```
Web search results for query: "LLM calibration selective prediction structured extraction field-level confidence logistic regression features agreement 2025 document extraction"

Links: [{"title":"Beyond Logprobs: A Multi-Signal Confidence Engine for LLM-Based Document Field Extraction","url":"https://arxiv.org/pdf/2606.24420"},{"title":"Valid Per-Field Selective Risk Control for Document Extraction: Three Failure Modes, a Validity Ladder, and When Conditioning Pays","url":"https://arxiv.org/pdf/2608.14639"},{"title":"Enhanced machine learning model accuracy through post-hoc confidence score calibration","url":"https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12236201"},{"title":"rs 10721490","url":"https://www.researchsquare.com/article/rs-10721490"},{"title":"0241e4ca 7c06 4de4 b523 40fd7624be95","url":"https://www.opentrain.ai/tools/hf-eval-papers/paper/0241e4ca-7c06-4de4-b523-40fd7624be95/"},{"title":"papers.cool","url":"https://papers.cool/arxiv/2603.00924"},{"title":"www.emergentmind.com","url":"https://www.emergentmind.com/papers/2604.12491"},{"title":"confidence score","url":"https://rets.ai/glossary/confidence-score"},{"title":"aws bda provides confidence scores of times right for 1ccef333","url":"https://opper.ai/ai-roundtable/questions/aws-bda-provides-confidence-scores-of-times-right-for-1ccef333"},{"title":"Share your thoughts, 1 month free Claude Pro on usSee more","url":"https://www.wizwand.com/paper/6a3b64d2206542251d7c98d1"}]

Links: [{"title"
... [5466 more characters]
```
</details>

**Tool call: Bash**

```json
{
 "command": "F=/Users/bakasur/.claude/projects/-Users-bakasur-Desktop-GoComet/cc5afe91-7c25-4a54-b70f-a005ddf58df4/tool-results/toolu_01Nhe4sY4hTDqxMECQnmhJkK.txt; sed -n 1040,1060p \"$F\"",
 "description": "Read PDF token cost section from saved doc"
}
```

**Tool call: WebFetch**

```json
{
 "url": "https://platform.claude.com/docs/en/build-with-claude/vision.md",
 "prompt": "Give the image token formula (tokens \u2248 width*height/750?), maximum tokens per image for current models (Opus 5.5, Sonnet 5.5, Haiku 5.5), and the example token count for a ~1000x1000 or letter-size page image. Short, quote numbers."
}
```

<details><summary>tool result</summary>

```
  </Step>
</Steps>

### Estimate your costs

The token count of a PDF file depends on the total text extracted from the document and the number of pages:

* Text token costs: Each page typically uses 1,500–3,000 tokens per page depending on content density. Standard API pricing applies with no additional PDF fees.
* Image token costs: Because each page is converted into an image, the same [image-based cost calculations](https://platform.claude.com/docs/en/build-with-claude/vision#evaluate-image-size) are applied.

You can use [token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) to estimate costs for your specific PDFs.

## Optimize PDF processing

### Improve performance

Follow these best practices for optimal results:

* Place PDFs before text in your requests
* Use standard fonts
* Ensure text is clear and legible
```
</details>

<details><summary>tool result</summary>

```
---
title: Vision
url: https://platform.claude.com/docs/en/build-with-claude/vision
description: Claude's vision capabilities allow it to understand and analyze images, opening up exciting possibilities for multimodal interaction.
---

This guide describes how to send images to Claude, the limits and costs that apply, and where to find guidance for [coordinate-based workflows](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates).

***

## Send images to Claude

Use Claude's vision capabilities through:

* [claude.ai](https://claude.ai/). Upload an image like you would a file, or drag and drop an image directly into the chat window.
* [Playground](https://platform.claude.com/playground) in the Claude Console. Add images directly to any User message block.
* API request. See the following examples.

On the API, provide images to Claude as `image` content blocks using one of three source types:

1. A base64-encoded image embedded in the request body
2. A URL reference to an image hosted online
3. A `file_id` returned by the [Files API](https://platform.claude.com/docs/en/build-with-claude/files) (upload once, reference many times)

<Note>
  On Amazon Bedrock and Google Cloud, only base64-encoded sources are currently available.
</Note>

<Tip>
  Just as [placing long documents before your query](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#long-context-prompting) improves results in text prompts, Cla
... [46302 more characters]
```
</details>

**Tool call: WebFetch**

```json
{
 "url": "https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/",
 "prompt": "List the six design patterns named in the paper with a one-line description each, especially context-minimization and dual LLM. Also any link to \"lethal trifecta\" post URL."
}
```

<details><summary>tool result</summary>

```
1. **Action-Selector Pattern:** The agent picks from a fixed set of actions, and tool outputs never feed back into it.
2. **Plan-Then-Execute Pattern:** The agent plans its tool calls in advance, so untrusted tool output can change the content of later steps but not which actions run.
3. **LLM Map-Reduce Pattern:** Sub-agents process untrusted items separately and return constrained results, such as a yes/no relevance judgment, which are then aggregated.
4. **Dual LLM Pattern:** A privileged LLM coordinates a quarantined LLM that handles untrusted content. The quarantined LLM returns symbolic variables, so the privileged LLM never sees the raw untrusted text. The author describes this as his own 2023 pattern, which influenced CaMeL.
5. **Code-Then-Execute Pattern:** The privileged LLM writes code in a restricted DSL that specifies tool calls and data flow, so tainted data can be tracked through the process. This is the CaMeL approach.
6. **Context-Minimization Pattern:** Unneeded content, such as the original user prompt, is removed from the context after it has served its purpose, so it cannot carry an injection forward. The paper's example converts a quote request into a database query and drops the user's prompt before returning results.

**Lethal trifecta post:** https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
```
</details>

## Claude 2026-10-08 16:33:41

I checked Anthropic's pricing, citations, PDF, structured-output, vision and prompt-injection pages live (October 2026). The research findings come from papers and practitioner sources; most of the freight and accounts-payable material is vendor writing, not measured results.

## 1. Grounded extraction with verbatim citations

- **Citations work on PDFs and return page numbers.** The feature is generally available (GA) on all active models. Each PDF citation is a `page_location` with `cited_text`, `start_page_number` (counted from 1) and `end_page_number` (exclusive, so subtract 1 for the last page). `cited_text` does not count as output tokens. https://platform.claude.com/docs/en/build-with-claude/citations
- **Limits.** PDF text is split into sentences for citing. Scanned PDFs with no extractable text cannot be cited, and images cannot be cited. "Custom content" documents are not split further, and their citations return a block index. If you load OCR output (from rapidocr or Claude vision) or Excel rows as one block per page or row, that index gives you a page or row reference for scans and sheets.
- **Citations do not work with structured outputs.** The docs say: "If you enable citations on any user-provided document … and also include the `output_config.format` parameter … the API returns a 400 error." Citations do work with prompt caching and the Batch API.
- **Structured outputs** (`output_config.format`, and `strict: true` on tools) are GA. The schema cannot use `minimum`/`maximum`, `minLength`/`maxLength`, or recursion. https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  - On `claude-opus-5-5` and `claude-sonnet-5-5`, forcing a tool call (`tool_choice` `any` or `tool`) returns a 400. Use `output_config.format`, or `strict: true` with `auto`.
  - I could not confirm that SDK 1.8.0 exposes these parameters. Test it on day one.
- **Quote-then-verify (standard practice).** Anthropic's own guidance: pull word-for-word quotes first, then reason only from them, and drop any claim with no supporting quote. https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
  - Practical setup: have structured output return `{value, quote, page}`, then check in code that the quote appears in that page's text (from pypdf or OCR).
  - The other option is two calls: a citations call to get the evidence, then a structured-output call to get the typed facts.

## 2. LLM extracts facts, code computes money and rules

- **Standard practice: the LLM reads and explains; versioned code with effective dates does the tolerance math, matching and pay decision.** Practitioner write-ups agree on this split. Examples: https://www.elementum.ai/blog/how-ai-powered-invoice-automation-works and https://gravitee.io/corpus/gen-2446/purchase-to-pay/three-way-matching-automation.html
- I found no independent, peer-reviewed test of an end-to-end LLM three-way-match or freight-audit system. Vendor accuracy claims (for example "99.9%") come with no method.
- **Why the split works:** PAL (Gao et al. 2022) showed LLMs break problems into steps correctly but make arithmetic mistakes. Handing the computation to Python beat chain-of-thought by large margins. https://arxiv.org/abs/2211.10435
- **Anthropic's view:** use fixed code paths ("workflows") over open-ended agents unless the task needs the autonomy. https://www.anthropic.com/research/building-effective-agents
- **Counterpoint:** Loop's engineering team writes carrier-specific rules into prompts. That is flexible, but code does not enforce it. https://www.loop.com/engineering-blog/teaching-llms-the-supply-chain-entity-context-rules-and-failure-analysis

## 3. Prompt-injection defence

- **Anthropic's guidance (standard practice):** https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks
  - Put untrusted content only inside `tool_result` blocks.
  - JSON-encode it and label where it came from.
  - State in the system prompt that this content is data, not orders.
  - Optionally screen it first with a Haiku classifier.
  - Give the model as little access as possible, and red-team it.
- **Spotlighting (Microsoft, 2024):** three methods (delimiting, datamarking, encoding). Attack success fell from over 50% to under 2% on GPT-3.5/4. It is a well-known, cheap layer, but the results are on older models. https://arxiv.org/abs/2403.14720
- **Dual LLM (Willison, 2023):** a quarantined model with no tools reads the untrusted text and returns only constrained values or placeholders. https://simonwillison.net/2023/Apr/25/dual-llm-pattern/
  - The "lethal trifecta" framing: an agent with no way to send data out cannot leak it. https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- **CaMeL (Google DeepMind / ETH, 2025):** builds the control flow from the trusted request and tracks where each value came from. It solves 77% of AgentDojo tasks with provable security, against 84% undefended. This is still research. https://arxiv.org/abs/2503.18813
- **Design-patterns paper (2025):** six patterns, including LLM map-reduce and context-minimization. Its rule: once an agent has read untrusted input, that input must not be able to trigger consequential actions. https://arxiv.org/abs/2506.08837 and https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/
- **Fit for this task:** extraction-only, no-tools workers whose output must pass a schema check are the simplest defensible design. They match dual LLM and map-reduce.

## 4. Confidence calibration (AUROC and Brier)

- **Verbalized confidence** (the model states a number) is better calibrated than token probabilities on RLHF models, including Claude: about 50% lower calibration error (ECE). https://arxiv.org/abs/2305.14975
- **But it is overconfident and ranks poorly.** Stated values cluster at 80–100 in steps of 5, and AUROC is often around 0.52–0.60. Agreement across several samples beats verbalized confidence; combining the two is best. https://arxiv.org/abs/2306.13063
- **Sample consistency** beats post-hoc calibration methods. https://arxiv.org/abs/2402.13904
- **Feature-based scoring:**
  - A logistic regression on features from prompt variations and answer consistency improves AUROC by up to 10 points or more (TMLR 2025). https://arxiv.org/abs/2406.04370
  - APRICOT trains a separate model to predict correctness and gives the best AUROC for spotting wrong answers. https://arxiv.org/abs/2403.05973
  - A 2026 preprint on document field extraction: a two-pass disagreement signal plus a boosted classifier reaches ROC AUC 0.928. Verbalized confidence and self-consistency were close to useless at practical thresholds. https://arxiv.org/abs/2606.24420 (experimental)
- **Practical takeaway:** combine signals (quote verified, cross-pass agreement, rule determinism, source authority, verbalized confidence) and fit a logistic (Platt) model on a labeled dev set. Isotonic regression overfits on small label sets.

## 5. Models, prices and cost per 1,000 documents

Per million tokens, from https://platform.claude.com/docs/en/about-claude/pricing:

| Model ID | Input | Output | Cache read | Batch input / output |
|---|---|---|---|---|
| `claude-haiku-5-5` (prompt ≤100K tokens; 5× higher above) | $0.10 | $0.50 | $0.01 | $0.05 / $0.25 |
| `claude-sonnet-5-5` | $2 | $10 | $0.10 | $1 / $5 |
| `claude-opus-5-5` | $4 | $20 | $0.20 | $2 / $10 |

- Cache writes cost 1.25× base input (5-minute) or 2× (1-hour). Batch is 50% off, and the discounts stack.
- Claude 4.7 and later models use about 30% more tokens for the same text.
- Opus 5.5 cannot turn off thinking, which is billed as output. Its default effort is `medium`; set it to `low` for extraction.
- **PDF tokens:** about 1,500–3,000 text tokens per page, plus the page image. On 4.7+ models an image costs ⌈w/28⌉×⌈h/28⌉ tokens, capped at 4,784. A 150-dpi letter page is about 2.7K, so roughly 4.7K tokens per page in total. https://platform.claude.com/docs/en/build-with-claude/vision

**Estimate per 1,000 documents** (assumes 3 pages each, about 14K input, a 2K cached prompt, and 2.5K output including thinking):

| Model | Standard | With Batch |
|---|---|---|
| Haiku 5.5 | about $2.70 | about $1.35 |
| Sonnet 5.5 | about $53 | about $27 |
| Opus 5.5 | about $106 | about $53 |

Sending text only (no page images) cuts input by about 55%.

## 6. Bitemporal fact store

- **Standard concept:** two time axes. Valid (actual) time is when a fact held in the real world; transaction (record) time is when the system learned it. Corrections add new rows and never overwrite old ones. https://www.martinfowler.com/articles/bitemporal-history.html and https://juxt.pro/blog/bitemporality-more-than-a-design-pattern
- **No dominant small Python library exists.** Candidates are niche or partial: `eventsourcing` handles one time axis only, and `novodb` is non-commercial.
- **What small tools do (and what fits here):** an append-only SQLite table with `valid_from`/`valid_to` plus `recorded_at`/`superseded_at`, queried as of both times. A JSON file is fine at this scale but loses indexed as-of queries. Reference designs: https://github.com/elh/bitempura
