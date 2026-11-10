# 07 — Evaluating agents and RAG systems

> **Big idea:** Multi-step systems fail in multi-step ways. Grade the
> **outcome** first, then use **component** and **trajectory** evals to
> find out *where* things went wrong.

## RAG (retrieval-augmented generation)

A RAG system retrieves documents and then generates an answer from them. Evaluate the
two halves separately, as well as end to end:

| Stage | Question | Example metrics |
|---|---|---|
| Retrieval | Did we fetch the right documents? | recall@k (is the needed doc in the top k?), precision@k, MRR |
| Generation: faithfulness | Is the answer supported by the retrieved documents? | LLM judge: "does every claim appear in the sources?" |
| Generation: relevance | Does it answer the question that was asked? | LLM judge, or reference match |
| End to end | Is the final answer correct and useful? | reference answers + judge |

Why separate them? If end-to-end accuracy is 70%, you need to know whether retrieval is
missing documents (fix chunking, embeddings, or the query) or generation is ignoring
them (fix the prompt). Different problems need different fixes.

A **retrieval dataset** is simply (question, IDs of the relevant documents). It's cheap to
build and fast to run, because no generation is needed.

## Agents (tool-using, multi-step)

An agent decides which tools to call, in what order, and when to stop. What to grade:

1. **Outcome** (most important): is the final state correct? Did the ticket get filed, the test pass, or the file get created? Grade the **state of the world** where you can, because it's more robust than grading text.
2. **Trajectory**: was the path reasonable? Did it call the right tools with valid arguments? Did it loop, or give up early? Useful for diagnosis, but don't over-constrain it. There are often several valid paths, so grading against one "golden trajectory" punishes valid creativity.
3. **Efficiency**: number of turns, tokens, cost, and wall-clock time.
4. **Safety**: did it take actions it shouldn't have (deleting data, emailing customers, spending money)? Make these hard-fail guardrails.

Practical tips:
- **Sandbox environments.** Agent evals need a reset-able world: a temporary repo, a fake API, a test database.
- **More trials.** Agents are higher-variance than single calls. pass^k matters a lot here.
- **Transcripts are gold.** Save the full trajectory, and read failed ones. Most insights come from reading, not from metrics.
- **Give the agent what a user would give it.** If the eval prompt hands over the exact file and line, you're testing hint-following, not investigation.

## Conversational and multi-turn systems

Single-turn evals miss problems that only appear deep into a conversation: drifting
persona, forgotten constraints, compounding errors. Options include scripted multi-turn
cases, and a **simulated user** (an LLM playing a customer with a goal), followed by a
judge on the whole transcript.

## As a lead engineer

- **Ask "which layer failed?"** When an agent or RAG feature underperforms, insist on component-level numbers before anyone rewrites the prompt.
- **Blast radius.** For agents that take actions, the eval plan must include safety guardrails and their pass rates, not just success rates.
- **Cost governance.** Agent eval runs can get expensive. Budget them, and use small smoke sets for PRs and full runs nightly.

## Lab

→ **Lab 6** (design exercise): design an eval for an agent or RAG feature, ideally one from your work.
