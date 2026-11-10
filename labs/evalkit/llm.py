"""Thin wrapper around the Anthropic SDK used by the labs.

Everything that talks to Claude goes through `complete_json`, so you only have
one place to look when you want to understand (or change) how calls are made.

Credentials: the SDK picks up ANTHROPIC_API_KEY, or a profile created with
`ant auth login`. Nothing is hard-coded here.
"""

from __future__ import annotations

import json
import os  # access to environment variables, like process.env in Node
import time
from dataclasses import dataclass

# Model under test, and the model that acts as LLM-as-judge.
# Override with env vars, e.g.  EVAL_MODEL=claude-sonnet-5-5 python run_eval.py
# os.environ.get(name, default) = process.env.NAME ?? default
MODEL = os.environ.get("EVAL_MODEL", "claude-opus-5-5")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-opus-5-5")

# USD per 1M tokens (input, output). Used for the cost column in reports.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "mock": (0.0, 0.0),
}

# Models that accept the server-side refusal fallback ("fallbacks": "default").
# {...} with plain values (no key: value pairs) is a set: a collection of unique items.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1"}

# One shared API client, created the first time it's needed (see _get_client).
_client = None  # None is Python's null


# A custom error type. `class Refused(Exception)` means "Refused extends Exception".
class Refused(Exception):
    """The model declined the request (stop_reason == 'refusal')."""


# Token counts and timing for one call. Every grader and task returns one of
# these so the report can total up cost and latency.
@dataclass
class Usage:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0

    # @property makes a method readable like a field: usage.cost_usd, not usage.cost_usd()
    # (like a JS getter).
    @property
    def cost_usd(self) -> float:
        p_in, p_out = PRICES.get(self.model, (0.0, 0.0))
        return (self.input_tokens * p_in + self.output_tokens * p_out) / 1_000_000  # _ in numbers is just for readability


def _get_client():
    # `global` lets this function reassign the module-level _client variable.
    # Without it, Python would create a new local variable instead.
    global _client
    if _client is None:
        import anthropic  # imported lazily so --mock works without the SDK

        _client = anthropic.Anthropic(max_retries=4)  # the SDK retries rate-limit and server errors itself
    return _client


def complete_json(
    *,
    system: str,
    user: str,
    schema: dict,
    model: str = MODEL,
    effort: str = "low",
    max_tokens: int = 4000,
) -> tuple[dict, Usage]:
    """Call Claude and get back a dict that is guaranteed to match `schema`.

    Uses structured outputs (output_config.format) so we never have to parse
    free text. `effort` trades quality for cost/latency: "low" is plenty for
    classification; try "medium"/"high" and *measure* whether it helps.
    """
    # dict(a=1, b=2) is another way to write {"a": 1, "b": 2}.
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        system=system,  # the instructions (the prompt file, or the judge rubric)
        messages=[{"role": "user", "content": user}],  # the input (the ticket)
        output_config={
            "effort": effort,
            "format": {"type": "json_schema", "schema": schema},  # force JSON matching the schema
        },
    )
    if model in _FALLBACK_MODELS:
        # If a safety classifier declines, the API retries on a fallback model.
        kwargs["betas"] = ["server-side-fallback-2026-07-01"]
        kwargs["fallbacks"] = "default"

    start = time.perf_counter()  # a high-resolution timer, like performance.now()
    # **kwargs spreads the dict into named arguments, like create({...kwargs}) in JS.
    resp = _get_client().beta.messages.create(**kwargs)
    usage = Usage(
        model=model,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        latency_s=time.perf_counter() - start,
    )

    # stop_reason says why the model stopped. Anything other than a normal
    # finish is turned into an error, which run_eval.py counts as a FAILED case.
    if resp.stop_reason == "refusal":
        raise Refused(str(getattr(resp, "stop_details", None)))  # getattr(obj, name, default) = obj?.name ?? default
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("Hit max_tokens before finishing the JSON output")

    # The response is a list of content blocks. next(...) returns the first
    # block whose type is "text", like resp.content.find(b => b.type === "text").
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text), usage  # json.loads = JSON.parse
