# AI Evals Lab

A hands-on course in **evals and AI engineering**, built to be worked through *with*
Claude Code as your tutor. It is aimed at a **lead engineer**: you'll learn to build
evals yourself, and to set the standards your team follows when it ships AI features.

## How it works

1. Open this folder in Claude Code: `cd ~/git/ai-evals-lab && claude`
2. Type **`/start`**. Claude asks about your role and team, then sets your path.
3. Work through the modules with the slash commands below.

| Command | What it does |
|---|---|
| `/start` | Onboarding: captures your context and goals, recommends a path |
| `/lesson [n]` | Teaches module *n* interactively (or the next unfinished one) |
| `/lab [n]` | Guides you through a hands-on lab, with hints instead of answers |
| `/quiz [n]` | Five questions on a module, with feedback |
| `/apply [topic]` | Applies a concept to *your* team; drafts a real artifact in `playbook/` |
| `/review-eval [path]` | Audits an eval (yours or one from work) against a checklist |
| `/progress` | Shows where you are and what's next |

## What's inside

```
curriculum/   10 modules (00-09) + labs.md
labs/         a working eval harness you'll run, break, and improve
  evalkit/    app.py (system under test), graders.py, stats.py, llm.py
  data/       tickets.jsonl (dev set), tickets_holdout.jsonl (test set)
  prompts/    triage_v1.txt (deliberately weak; you'll write v2)
  run_eval.py, compare.py, calibrate_judge.py
playbook/     lead-engineer templates: eval strategy, PR checklist, rollout plan
notes/        your context and learning journal (Claude keeps these up to date)
PROGRESS.md   your checklist
```

## The system under test

A **support-ticket triage assistant**: it reads a customer ticket and returns a category,
a priority, and a first reply. It's small enough to understand in five minutes, and it
still has the problems real AI features have: ambiguous labels, prompt injection,
policy constraints, open-ended text quality, and nondeterminism.

## Running the labs

```bash
cd labs
uv run python run_eval.py --mock     # free & offline: a rule-based fake model
uv run python run_eval.py            # real Claude
```

**Mock mode** lets you learn the mechanics without spending anything. Labs 5 and later
are more useful with real calls. For those, set `ANTHROPIC_API_KEY` (or run `ant auth login`).
A full run of 20 cases with the judge makes about 40 API calls, which costs well under
a dollar on the default model (`claude-opus-5-5`). You can switch models with
`EVAL_MODEL=claude-sonnet-5-5` or `EVAL_MODEL=claude-haiku-5-5`, and switch the judge
with `JUDGE_MODEL=...`.

## Time

About 10–14 hours in total. Each module takes roughly 30–45 minutes of reading and
discussion, and each lab 30–60 minutes.
