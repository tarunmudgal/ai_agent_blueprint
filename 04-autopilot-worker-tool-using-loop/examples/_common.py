"""Shared scaffolding for every example in Blueprint 4 — The Autopilot Worker.

Nothing in this module talks to the network at import time. It only:
  * loads a local .env so GEMINI_API_KEY is available,
  * pins the model in ONE place,
  * hands back a configured client with a human-readable error if the key
    is missing,
  * holds the fixtures this chapter's two running examples depend on -
    ticket_text and doc_refund_policy, byte-identical to Chapters 1-3's own
    _common.py, plus the two NEW fixtures this chapter introduces,
    WEATHER_DATA and CUSTOMER_HISTORY,
  * prints usage and section banners consistently,
  * defines Tool, the minimal shape every tool-using loop example in this
    chapter registers its functions with,
  * defines run_agent_loop, the one new piece of infrastructure this
    chapter adds: a small, framework-free think -> act -> observe -> repeat
    runner built directly on the Interactions API's own step types.

Import it from any example:

    from _common import (
        MODEL, get_client, ticket_text, doc_refund_policy,
        WEATHER_DATA, CUSTOMER_HISTORY, banner, report_usage,
        Tool, run_agent_loop,
    )

Every example adds this directory to sys.path itself, so the scripts run
from the repository root (`python3 examples/01_weather_alert_worker.py`) as
well as from inside `examples/`.
"""


import json
import os
import sys
from dataclasses import dataclass
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency guidance, not logic
    print(
        "Missing dependency: python-dotenv\n"
        "Run: python3 -m pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise

# Look for a .env in the current directory and every parent, so it works
# whether you launch from the repo root or from examples/.
load_dotenv()

# ---------------------------------------------------------------------------
# Model pin
# ---------------------------------------------------------------------------
# One constant, imported everywhere, exactly as in Chapters 1-3. A tool loop
# does not change this story - every turn of the loop still calls the same
# one model.
#
# The pinned model below is a Gemini 3 stable model. Its default
# thinking_level is "medium" and it supports minimal | low | medium | high.
#
# Honest caveat: the Interactions API "supported models" table on
# ai.google.dev does not list it, yet Google's own quickstart and thinking
# guides use exactly this pairing. The table looks stale. If you hit a
# model-not-supported error, Gemini 2.5 Flash is the documented fallback -
# change the one line below and note that the 2.5 series does NOT support
# thinking_level="minimal".
#
# This assignment is the ONLY model string in the whole examples/ folder.
MODEL: str = "gemini-3.5-flash"

# Chapters 1-3 default to store=False: every call there is single-shot, so
# there is no "next turn" worth keeping server-side. A tool-using loop is
# different — it can run for several turns, and the alternative to
# store=True + previous_interaction_id is manually replaying the entire
# growing conversation (every prior thought, function_call, and
# function_result step) on every single iteration. That is exactly the
# bookkeeping previous_interaction_id exists to avoid, so this chapter
# departs from Chapters 1-3's convention on purpose: STORE_DEFAULT is True
# here, not False.
STORE_DEFAULT: bool = True

# A hard ceiling on how many turns a single run_agent_loop() call may take.
# Never treat this as optional: an ill-specified tool loop that never
# terminates is a real, named risk in this chapter (see 04_max_turns_cap.py),
# not a hypothetical edge case.
DEFAULT_MAX_TURNS: int = 6


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
def get_client() -> Any:
    """Return a configured genai Client, or exit with an actionable message.

    The SDK reads GEMINI_API_KEY from the environment on its own. We check
    first only so the failure is a sentence a human can act on rather than
    an authentication stack trace 40 lines deep.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your-key-here":
        raise SystemExit(
            "\n"
            "GEMINI_API_KEY is not set (or is still the placeholder).\n"
            "\n"
            "Fix it in one of two ways:\n"
            "  1. cp .env.example .env  and paste your key into .env\n"
            "  2. export GEMINI_API_KEY='...'   (this shell only)\n"
            "\n"
            "Get a key at https://aistudio.google.com/apikey\n"
        )

    try:
        from google import genai
    except ImportError:
        raise SystemExit(
            "\n"
            "Missing dependency: google-genai\n"
            "Run: python3 -m pip install -r requirements.txt\n"
            "The Interactions API needs google-genai >= 1.55.0.\n"
        )

    # No argument needed: Client() picks up GEMINI_API_KEY itself.
    return genai.Client()


# ---------------------------------------------------------------------------
# Canonical fixture 1 — the support ticket driving Example B, the Support
# Ticket Autopilot. Byte-identical to Chapters 1-3's own _common.py: Example
# B depends on it being the exact same ticket Chapter 1 classified, Chapter
# 2 routed, and Chapter 3 grounded.
# ---------------------------------------------------------------------------
ticket_text: str = """Hi, I was charged twice for my October subscription. I can see two
identical GBP 49.00 charges on the same card, both dated 3 October. I have already
tried logging in to check my invoices but the billing page just spins forever.
Could someone refund the duplicate? This is the second month it has happened."""


# ---------------------------------------------------------------------------
# Canonical fixture 2 — the refund policy Example B's lookup_refund_policy
# tool searches. Byte-identical to Chapter 3's own _common.py.
# ---------------------------------------------------------------------------
doc_refund_policy: str = """Refund and Duplicate Charge Policy (Billing Handbook, Section 4)

Customers charged more than once for the same billing period due to a system error
are eligible for an automatic refund of the duplicate charge, no support ticket
required, once the duplicate is confirmed in the payment ledger. Confirmed duplicate
charges are refunded within 5-7 business days to the original payment method.

If a customer reports being charged twice in two or more consecutive billing cycles,
the account must be flagged for manual review by the billing operations team before
any further automatic refund is issued, since repeat duplication usually indicates a
deeper account or integration problem rather than a one-off system error.

Refunds for any other reason (dissatisfaction, accidental purchase, downgrade
requests) fall outside this section and are handled under the standard cancellation
policy instead."""


# ---------------------------------------------------------------------------
# New fixtures — simulated external systems this chapter's tools read from.
# These stand in for a real weather API and a real CRM/billing-history
# lookup. No example in this chapter calls a real external service; both
# tables are small, deterministic, in-memory dicts.
# ---------------------------------------------------------------------------
WEATHER_DATA: dict[str, dict[str, Any]] = {
    "London": {"condition": "heavy rain", "wind_kph": 42, "temp_c": 11},
    "Phoenix": {"condition": "clear", "wind_kph": 8, "temp_c": 39},
    "Chicago": {"condition": "thunderstorm", "wind_kph": 55, "temp_c": 24},
}

CUSTOMER_HISTORY: dict[str, dict[str, Any]] = {
    "cust_4471": {"name": "J. Alvarez", "duplicate_charges_this_year": 2,
                  "account_standing": "good"},
}


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------
def banner(title: str, width: int = 74) -> None:
    """Print a section header so long console output stays readable."""
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def rule(width: int = 74) -> None:
    """A lighter separator for sub-sections."""
    print("-" * width)


def report_usage(interaction: Any, label: str = "usage") -> None:
    """Print the token breakdown for a completed interaction.

    Field names come straight from the Interactions API usage object:
      total_input_tokens, total_output_tokens, total_thought_tokens,
      total_cached_tokens, total_tool_use_tokens, total_tokens

    Only the first two are reliably present on every response, so the
    optional ones go through getattr with a 0 default. Reading
    `usage.total_thought_tokens` directly is a very common way to crash a
    script the first time you run it against a non-thinking response.
    """
    usage = getattr(interaction, "usage", None)
    if usage is None:
        print(f"[{label}] no usage object on this response")
        return

    inp = getattr(usage, "total_input_tokens", 0)
    out = getattr(usage, "total_output_tokens", 0)
    thought = getattr(usage, "total_thought_tokens", 0) or 0
    cached = getattr(usage, "total_cached_tokens", 0) or 0
    tools = getattr(usage, "total_tool_use_tokens", 0) or 0
    total = getattr(usage, "total_tokens", 0)

    print(
        f"[{label}] input={inp}  output={out}  thinking={thought}  "
        f"cached={cached}  tools={tools}  total={total}"
    )
    # Billing reality check: you pay for thinking tokens at the output rate
    # even though you only ever see the summary.
    if thought:
        print(f"[{label}] billed as output: {out + thought} tokens "
              f"({out} visible + {thought} hidden thinking)")


def truncate(text: str, limit: int = 400) -> str:
    """Shorten text for console display without hiding that it was cut."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n... [{len(text) - limit} more characters]"


# ---------------------------------------------------------------------------
# Tool — the new mechanics this chapter teaches. Deliberately minimal: a
# tool is a name, a function-calling declaration (the schema the model
# sees), the actual Python callable to run locally when the model asks for
# it, and a flag marking whether this tool's real-world equivalent would be
# irreversible (send an email, issue a refund, escalate to a real system) -
# the human-in-the-loop approval gate this chapter keeps naming.
#
# There is no dispatcher class beyond this: run_agent_loop looks tools up
# by name out of a plain list. That is the whole "tool allowlist" — a
# static, fixed-at-design-time set of callables the model may choose among,
# even though the SEQUENCE it calls them in is not fixed in advance.
# ---------------------------------------------------------------------------
@dataclass
class Tool:
    """One tool the model may choose to call during a run_agent_loop() run.

    `declaration` is the plain-dict function-calling schema handed to
    `tools=[...]` on every client.interactions.create call in the loop -
    see GEMINI-API-FACTS.md's "Function calling / tools" section for the
    exact shape (type/name/description/parameters).

    `fn` is the real Python callable executed locally, never by the SDK -
    there is no automatic function calling in this API. It is called as
    `fn(**arguments)`, so its parameter names must match the declaration's
    `parameters.properties` keys exactly.

    `requires_review` marks a tool whose real-world equivalent would be
    irreversible (sending an email, issuing a refund, escalating to a real
    system). Every such tool in this chapter's examples is itself already a
    simulation that only prints what it would do — `requires_review` is
    recorded here so a loop's transcript can be audited afterwards (see
    03_audit_guard.py) for whether the model reached for one of these
    without having done the grounding work first.
    """

    name: str
    declaration: dict[str, Any]
    fn: Any
    requires_review: bool = False


# ---------------------------------------------------------------------------
# run_agent_loop — the reusable think -> act -> observe -> repeat runner
# every example script in this chapter builds on. Maps directly onto the
# Interactions API's own step types:
#   thought          -> the model's reasoning for this turn (not required to
#                        author use it, but it's on interaction.steps if
#                        thinking is enabled)
#   function_call    -> the "act": the model asking to run one tool
#   function_result  -> the "observe": your code's answer, submitted back
#                        with previous_interaction_id
#
# Two, and only two, ways out of the loop:
#   1. the "happy path" — a turn's steps contain no function_call step, so
#      the model believes it is done; interaction.output_text is the
#      answer.
#   2. the hard cap — max_turns is exceeded before (1) happens. This is a
#      real failure mode this chapter treats as first-class, not an
#      afterthought: it is handled by returning a clearly-labeled
#      {"status": "max_turns_reached", ...} dict instead of looping
#      forever.
# ---------------------------------------------------------------------------
def run_agent_loop(
    client: Any,
    objective: str,
    tools: list[Tool],
    max_turns: int = DEFAULT_MAX_TURNS,
) -> dict[str, Any]:
    """Run a tool-using loop to completion, or until max_turns is hit.

    Uses stateful mode (store=True, the API default) with
    previous_interaction_id to carry the conversation forward turn by turn -
    the deliberate departure from Chapters 1-3's store=False convention
    this chapter names explicitly. Only the newest function_result is sent
    as `input` on every turn after the first; the server already holds the
    rest of the history.

    Returns one of:
      {"status": "done", "answer": str, "transcript": list[dict]}
      {"status": "max_turns_reached", "transcript": list[dict]}

    `transcript` is a plain list of dicts, each one turn's worth of
    bookkeeping: the interaction id, any function_call made, and the
    function_result (if any) submitted back. It is this chapter's
    "loop trace" — the thing worth logging in full now that the sequence of
    steps is no longer fixed in advance.
    """
    declarations = [tool.declaration for tool in tools]
    tools_by_name = {tool.name: tool for tool in tools}

    transcript: list[dict[str, Any]] = []

    interaction = client.interactions.create(
        model=MODEL,
        input=objective,
        tools=declarations,
        store=True,
    )

    turn = 1
    while True:
        fc_step = next(
            (s for s in interaction.steps if s.type == "function_call"), None
        )

        if fc_step is None:
            # No more function_call steps: the model believes it is done.
            # This is the "happy path" exit — the only one where the model,
            # not the loop budget, decided the run was finished.
            transcript.append({
                "turn": turn,
                "interaction_id": interaction.id,
                "function_call": None,
                "function_result": None,
                "output_text": interaction.output_text,
            })
            return {
                "status": "done",
                "answer": interaction.output_text,
                "transcript": transcript,
            }

        tool = tools_by_name.get(fc_step.name)
        if tool is None:
            # The model asked for a tool outside the allowlist. This should
            # not happen if `tools=` only ever lists what we registered, but
            # a fixed, known-in-advance allowlist is exactly the safety
            # boundary that makes this an error worth halting on, rather
            # than a silently-ignored no-op.
            transcript.append({
                "turn": turn,
                "interaction_id": interaction.id,
                "function_call": {"name": fc_step.name, "arguments": fc_step.arguments},
                "function_result": None,
                "error": f"tool {fc_step.name!r} is not in the allowlist",
            })
            return {"status": "max_turns_reached", "transcript": transcript}

        # ACT: execute the matching Python function locally. The SDK never
        # does this for you - there is no automatic function calling here.
        result = tool.fn(**fc_step.arguments)

        transcript.append({
            "turn": turn,
            "interaction_id": interaction.id,
            "function_call": {"name": fc_step.name, "arguments": fc_step.arguments},
            "function_result": result,
        })

        if turn >= max_turns:
            # The hard cap. Treated as a real, named failure mode: halt and
            # surface it, rather than submitting one more function_result
            # and looping forever.
            return {"status": "max_turns_reached", "transcript": transcript}

        # OBSERVE: submit the function_result, carrying the conversation
        # forward with previous_interaction_id (stateful mode) instead of
        # replaying the whole growing history ourselves.
        interaction = client.interactions.create(
            model=MODEL,
            input=[{
                "type": "function_result",
                "name": fc_step.name,
                "call_id": fc_step.id,
                "result": [{"type": "text", "text": json.dumps(result)}],
            }],
            tools=declarations,
            store=True,
            previous_interaction_id=interaction.id,
        )
        turn += 1
