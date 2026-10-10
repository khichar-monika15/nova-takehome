# AI use

## Tools

Claude Code (the Anthropic command-line agent) with the model `claude-opus-5-5` did almost all the work in one session. It read the brief and the grader code, made the plan, wrote the code and the tests, and drafted the documents. Subagents did separate jobs, and each has its own log. All ran on `claude-opus-5-5` except one, named below. Two studied the grader and the data, and one checked current practice on the web. One built a blind answer key for the exam mailbox from the documents alone, without the code. One wrote the new eval mailboxes. One reviewed the whole branch on Claude Fable before the first submission. In the final pass, two more reviewed the submission: one graded it against SUBMISSION.md, and one looked for risks on the hidden set. The session used the Superpowers skills for its process: brainstorming, plan writing, plan execution, test-driven development and systematic debugging.

OpenAI `gpt-5.5` and `gpt-5.4-mini`, and Claude Opus 5.5 through Amazon Bedrock, were not coding tools. They were the models inside the program for the local runs, because no Anthropic API key was available.

## How you worked with them

The person in the session gave the goal and made the decisions. The person chose the 48-hour deadline and the approach "the model reads, code decides". The person also chose OpenAI and then Bedrock for local runs, and this GitHub account. Claude asked before each of these decisions, and the log shows the questions and the answers.

Checks did not rely on reading the code. The grader's own tools scored the work. A blind subagent built the exam answer key with its own scripts, without seeing the code. The answer sheet of the program matched it on 9 of 9 rows. Every rule has a unit test that failed before the code existed.

The AI got these things wrong, and the log shows each fix:

- The first rules used the practice contract's charge codes and exact lane text. The new eval mailboxes found it (12 of 21 cases passed), and the fix reads charge kinds by meaning.
- A late fee on an invoice that only the AP register held was skipped. The worked example found it.
- A failed model call was saved as a finished document of type "other". In one run, this lost the AP register. Failed documents now stay open and get a second try.
- One test expected the wrong normalized invoice id, and one test used a label that its own fixture did not hold.
- The brief to the eval subagent said a one-off waiver made the next month a finding. The subagent followed GLOSSARY.md instead, which says the opposite, and that was right.
- The two final reviewers found defects that the tests had missed. Examples are a later amendment that did not beat a feedback fact, and a one-off fact that acted as standing. Each fix has a test that failed first.
- The first log export kept 8 characters of a key, because they were part of a search command. The exporter now removes any piece of a local key file.

## Written without AI

No code, test or document in this repository was written without AI. The decisions in the section above came from the person in the session.

## Prompt log

The full log is in `ai_log/`: `session.md` is the main session, and each `subagent-*.md` file is one subagent. `ai_log/export_log.py` made them from the Claude Code session files. The script cuts tool results to 1,500 characters and tool inputs to 2,500 characters. It replaces OpenAI and Bedrock API keys, and any piece of a local key file, with a marker. Nothing else was removed or changed.
