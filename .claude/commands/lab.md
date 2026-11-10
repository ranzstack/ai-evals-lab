---
description: Guide me through a hands-on lab (hints, not answers)
argument-hint: "[lab number]"
---

Guide me through **Lab $ARGUMENTS** from `curriculum/labs.md` (if no number is given, use the next unfinished lab in `PROGRESS.md`).

Rules:
- State the lab's goal and the steps up front, then go step by step.
- **I do the work.** Give me the command to run, or tell me which file to edit, and let me try. If I'm stuck, give hints in increasing order of specificity (nudge → pointer to file/line → partial solution). Give the full solution only if I ask for it.
- When there's output, ask me what I notice *before* you interpret it.
- Before any step that calls the real API (anything without `--mock`), tell me roughly how many calls it makes and get a yes from me.
- When I finish, log a one-line result in the "Lab results log" of `PROGRESS.md` (date, lab, key number, insight), and tick the Lab box.
- End by asking: "Where would this show up on your team?" Then use `notes/my-context.md` to make it concrete.
