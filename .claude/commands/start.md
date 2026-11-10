---
description: Onboard - learn about me and my team, then recommend a learning path
---

Run the onboarding for this learning project.

1. Read `notes/my-context.md` and `PROGRESS.md`. If context is already filled in, summarize it back and ask what changed, then skip to step 4.
2. Ask me these, **two or three at a time** (not all at once), conversationally:
   - What does my team build, and how big is it?
   - Which AI/LLM features do we ship or plan to ship (or none yet)?
   - How do we currently decide an AI change is good enough to ship?
   - What's my biggest worry about AI quality or reliability right now?
   - What do I want to be able to *do* after this course? (Push for concrete outcomes, e.g. "set up an eval gate in CI", "review AI PRs with confidence", "pitch an eval strategy to my director".)
   - How comfortable am I with Python and basic statistics?
3. Write the answers into `notes/my-context.md`.
4. Recommend a path: which modules to go deep on, and which to skim, given my goals. Everyone does 0–2 and 9.
5. Check the lab environment works: run `cd labs && uv run python run_eval.py --mock --limit 3 --no-judge` (use `~/.local/bin/uv` if `uv` isn't on PATH). Explain in two sentences what the output shows.
6. Suggest I continue with `/lesson 0`.
