---
description: Teach a curriculum module interactively (default - next unfinished one)
argument-hint: "[module number]"
---

Teach module **$ARGUMENTS** from `curriculum/` (if no number is given, pick the first module whose Lesson box is unchecked in `PROGRESS.md`).

How to teach it:
1. Read the module file and `notes/my-context.md`.
2. Open with the module's **one-sentence big idea** and why it matters to *my* work (use my context).
3. Go through the key concepts **one at a time**. For each: explain briefly (under ~150 words), show a concrete example (from `labs/` when possible: cite the file and line, or run a quick `--mock` command and show the output), then ask me one check-for-understanding question. **Wait for my answer** before moving on. Correct misconceptions directly.
4. Cover the module's "As a lead engineer" section as a discussion, not a lecture. Ask how it would play out on my team.
5. Wrap up with a 3-bullet recap, then point to the module's lab (`/lab n`) or quiz (`/quiz n`).
6. Tick the Lesson box in `PROGRESS.md`. Offer to add a journal entry to `notes/journal.md`.

Keep it a conversation. If I ask to go faster, compress. If I'm confused, slow down and use another example.
