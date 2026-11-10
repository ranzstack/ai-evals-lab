"""The SYSTEM UNDER TEST: a support-ticket triage assistant.

Given a customer ticket it returns:
  - category  (billing | bug | feature_request | account | other)
  - priority  (low | medium | high | urgent)
  - reply     (a short first response to the customer)

This is the thing you are evaluating. In real life it would be your team's
AI feature. The prompt lives in labs/prompts/<name>.txt so you can version it.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

from .llm import MODEL, Usage, complete_json

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

CATEGORIES = ["billing", "bug", "feature_request", "account", "other"]
PRIORITIES = ["low", "medium", "high", "urgent"]

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


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in PROMPTS_DIR.glob("*.txt")))
        raise SystemExit(f"Prompt '{name}' not found. Available: {available}")
    return path.read_text()


def triage(ticket: str, prompt_name: str, *, mock: bool = False, seed: int = 0) -> tuple[dict, Usage]:
    if mock:
        return mock_triage(ticket, seed=seed), Usage(model="mock")
    system = load_prompt(prompt_name)
    return complete_json(system=system, user=f"<ticket>\n{ticket}\n</ticket>", schema=OUTPUT_SCHEMA, model=MODEL)


# ---------------------------------------------------------------------------
# Mock model: a keyword-rule "model" so you can run every lab for free.
# It is deliberately flawed in realistic ways (keyword traps, a policy
# violation, and a bit of randomness) so your graders have something to catch.
# ---------------------------------------------------------------------------

_RULES = [
    ("billing", r"charge|invoice|refund|billing|payment|discount|vat|plan"),
    ("bug", r"error|crash|broken|bug|500|429|doesn't work|does nothing|slow|typo|deleted"),
    ("feature_request", r"would love|feature|add (an )?option|could you add|integrate"),
    ("account", r"password|log ?in|account|2fa|email address|sesión|cuenta"),
]


def mock_triage(ticket: str, seed: int = 0) -> dict:
    text = ticket.lower()
    rng = random.Random(f"{ticket}|{seed}")

    category = "other"
    for cat, pattern in _RULES:
        if re.search(pattern, text):
            category = cat
            break

    if re.search(r"urgent|asap|production|down|all users|now!", text):
        priority = "urgent"
    elif "!!!" in text or "can't" in text or "cannot" in text:
        priority = "high"
    elif category == "feature_request":
        priority = "low"
    else:
        priority = "medium"

    # Nondeterminism: ~15% of the time, nudge priority by one level.
    if rng.random() < 0.15:
        i = PRIORITIES.index(priority)
        priority = PRIORITIES[max(0, min(3, i + rng.choice([-1, 1])))]

    reply = f"Thanks for reaching out! We've logged your {category.replace('_', ' ')} request."
    if category == "billing" and "refund" in text:
        reply += " We will refund you right away."  # <- violates refund policy
    elif category == "bug":
        reply += " Our engineers are looking into it and we'll update you within one business day."
    else:
        reply += " A member of our team will get back to you soon."
    return {"category": category, "priority": priority, "reply": reply}
