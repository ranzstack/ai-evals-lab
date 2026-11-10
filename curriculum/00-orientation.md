# 00 — Orientation: AI engineering and where evals fit

> **Big idea:** AI engineering is software engineering where one component is
> *probabilistic*. Evals are the tests for that component, and they matter more
> than unit tests do, because you can't read the model's "source code".

## What is AI engineering?

AI engineering means building products on top of foundation models (like Claude) rather
than training models yourself. The day-to-day work includes:

- **Prompt and context design**: system prompts, examples, retrieved documents, tool definitions.
- **Orchestration**: chaining calls, tool use, agents, retries, fallbacks.
- **Structured outputs**: getting reliable JSON or typed results out of a model (see `labs/evalkit/llm.py`).
- **Evaluation**: measuring whether the system does what you need. *(This course.)*
- **Operations**: cost, latency, rate limits, monitoring, and incident response for nondeterministic behaviour.

## What's different from traditional software

| Traditional code | LLM-powered feature |
|---|---|
| Deterministic: same input, same output | Can vary from run to run |
| Behaviour is specified by code you can read | Behaviour emerges from prompt + model + context |
| Unit tests assert exact outputs | Many outputs are "good" in different ways |
| A bug is a defect in a line | A "bug" is often a *rate*: fails 7% of the time on angry customers |
| Upgrading a dependency rarely changes behaviour | A model or prompt change can shift everything |

The last two rows matter most. **Quality becomes a distribution, not a boolean**, so you
need a way to measure that distribution. That measurement is an eval.

## A working definition

> An **eval** is a repeatable experiment that runs your AI system on a set of inputs,
> scores the outputs against criteria you care about, and reports metrics you can compare
> across versions.

The key word is *repeatable*: an eval lets you answer "did this change make things
better or worse?" with evidence instead of a feeling.

## The lab system

Read `labs/evalkit/app.py`. The triage assistant takes a ticket and returns a category, a
priority, and a reply. Then skim `labs/data/tickets.jsonl`. You'll spend the course
measuring and improving this assistant.

## As a lead engineer

Your job shifts from *"is the code correct?"* to *"do we have evidence it's good enough,
and will we notice when it stops being good enough?"* Questions to start asking in design
reviews:

1. What does "good" mean for this feature, written down?
2. How will we know if a prompt or model change makes it worse?
3. What's the cost of a wrong answer, and who pays it?

## Lab: setup

`/start` checks your environment. If you'd like to run it by hand:
`cd labs && uv run python run_eval.py --mock --limit 3`.
