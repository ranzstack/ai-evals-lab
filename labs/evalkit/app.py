"""The SYSTEM UNDER TEST: a support-ticket triage assistant.

Given a customer ticket it returns:
  - category  (billing | bug | feature_request | account | other)
  - priority  (low | medium | high | urgent)
  - reply     (a short first response to the customer)

This is the thing you are evaluating. In real life it would be your team's
AI feature. The prompt lives in labs/prompts/<name>.txt so you can version it.
"""

# Python tip: a string in triple quotes at the very top of a file is a
# "docstring" - documentation for the module. It's like a JSDoc block in JS.

# Lets us write type hints like `dict | None` on older Python versions too.
from __future__ import annotations

import random  # random numbers (used to fake the model's run-to-run variation)
import re  # regular expressions, like JS RegExp
from pathlib import Path  # file paths as objects: Path("a") / "b" joins them

# A leading dot means "from this same package" (the evalkit/ folder),
# like `require("./llm")` in Node.
from .llm import MODEL, Usage, complete_json

# __file__ is this file's path. .resolve() makes it absolute, .parent goes up
# one folder. So: evalkit/app.py -> evalkit/ -> labs/ -> labs/prompts
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# ALL_CAPS names are constants by convention (Python doesn't enforce it).
# These lists define the only labels the assistant is allowed to return.
CATEGORIES = ["billing", "bug", "feature_request", "account", "other"]
PRIORITIES = ["low", "medium", "high", "urgent"]  # ordered: index 0 = least severe

# A JSON Schema the real model's answer must match. Python dicts look just like
# JS objects. "enum" restricts a field to a fixed list of values, so the model
# can't invent a category like "urgent-billing".
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "priority": {"type": "string", "enum": PRIORITIES},
        "reply": {"type": "string"},
    },
    "required": ["category", "priority", "reply"],
    "additionalProperties": False,
}


# `def` defines a function. `name: str` is a type hint (like TypeScript), and
# `-> str` is the return type. Hints are documentation only; Python doesn't
# enforce them at runtime.
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"  # f"..." is a template string, like `${name}.txt` in JS
    if not path.exists():
        # List the prompt files that DO exist, to make the error helpful.
        # `p.stem` is the filename without its extension.
        available = ", ".join(sorted(p.stem for p in PROMPTS_DIR.glob("*.txt")))
        raise SystemExit(f"Prompt '{name}' not found. Available: {available}")  # `raise` = `throw`
    return path.read_text()


# The `*` in the parameter list means everything after it must be passed by
# name: triage(text, "triage_v1", mock=True), not triage(text, "triage_v1", True).
# `tuple[dict, Usage]` means it returns two values at once: (output, usage).
def triage(ticket: str, prompt_name: str, *, mock: bool = False, seed: int = 0) -> tuple[dict, Usage]:
    if mock:
        # Free, offline path: keyword rules instead of a real model call.
        return mock_triage(ticket, seed=seed), Usage(model="mock")
    # Real path: load the versioned prompt, wrap the ticket in tags so the model
    # can tell where the customer's text starts and ends, and ask Claude for
    # JSON that matches OUTPUT_SCHEMA.
    system = load_prompt(prompt_name)
    return complete_json(system=system, user=f"<ticket>\n{ticket}\n</ticket>", schema=OUTPUT_SCHEMA, model=MODEL)


# ---------------------------------------------------------------------------
# Mock model: a keyword-rule "model" so you can run every lab for free.
# It is deliberately flawed in realistic ways (keyword traps, a policy
# violation, and a bit of randomness) so your graders have something to catch.
# ---------------------------------------------------------------------------

# A list of (category, regex) pairs, checked in order; the first match wins.
# The r"..." prefix makes a "raw string", so backslashes in regexes don't need
# escaping. The | inside a regex means "or".
_RULES = [
    ("billing", r"charge|invoice|refund|billing|payment|discount|vat|plan"),
    ("bug", r"error|crash|broken|bug|500|429|doesn't work|does nothing|slow|typo|deleted"),
    ("feature_request", r"would love|feature|add (an )?option|could you add|integrate"),
    ("account", r"password|log ?in|account|2fa|email address|sesión|cuenta"),
]
# (A leading underscore, as in _RULES, means "private to this module" by convention.)


def mock_triage(ticket: str, seed: int = 0) -> dict:
    text = ticket.lower()
    # A random generator seeded from (ticket, seed): the same ticket + seed
    # always gives the same "random" result, so runs are reproducible.
    # A different seed acts like a different run of the model.
    rng = random.Random(f"{ticket}|{seed}")

    # --- category: first rule whose regex appears in the text ---
    category = "other"
    for cat, pattern in _RULES:  # unpacks each (category, regex) pair into two variables
        if re.search(pattern, text):  # re.search = "does this pattern appear anywhere?"
            category = cat
            break

    # --- priority: keyword heuristics (elif = "else if") ---
    if re.search(r"urgent|asap|production|down|all users|now!", text):
        priority = "urgent"
    elif "!!!" in text or "can't" in text or "cannot" in text:  # `in` checks for a substring
        priority = "high"
    elif category == "feature_request":
        priority = "low"
    else:
        priority = "medium"

    # Nondeterminism: ~15% of the time, nudge priority by one level.
    if rng.random() < 0.15:  # rng.random() returns a float in [0, 1)
        i = PRIORITIES.index(priority)  # position in the list, e.g. "high" -> 2
        # Move up or down one level, clamped so it stays between 0 and 3.
        priority = PRIORITIES[max(0, min(3, i + rng.choice([-1, 1])))]

    # --- reply: a canned template ---
    reply = f"Thanks for reaching out! We've logged your {category.replace('_', ' ')} request."
    if category == "billing" and "refund" in text:
        reply += " We will refund you right away."  # <- violates refund policy
    elif category == "bug":
        reply += " Our engineers are looking into it and we'll update you within one business day."
    else:
        reply += " A member of our team will get back to you soon."
    # Return a dict with the same shape the real model returns.
    return {"category": category, "priority": priority, "reply": reply}
