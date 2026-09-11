"""Shared scaffolding for every example in Blueprint 5 — The Connected Boardroom.

Nothing in this module talks to the network at import time. It only:
  * loads a local .env so GEMINI_API_KEY is available,
  * pins the model in ONE place,
  * hands back a configured client with a human-readable error if the key
    is missing,
  * holds the fixtures this chapter's two running examples depend on -
    ticket_text, document_text, and doc_refund_policy, byte-identical to
    Chapters 1-4's own _common.py, plus the NEW fixture this chapter
    introduces, BILLING_ANOMALY_ROWS,
  * prints usage and section banners consistently,
  * re-exports Chapter 4's exact Tool dataclass and run_agent_loop runner —
    this chapter's Supervisor IS Chapter 4's tool-calling loop, reused
    without modification. Nothing here redesigns that mechanic,
  * adds the one genuinely new piece of vocabulary this chapter needs: a
    Specialist dataclass (a name, a persona, and a callable), and
    make_specialist_tool(), which wraps a Specialist into a Tool whose body
    is a nested client.interactions.create call instead of a plain
    function touching local data. That single helper is the whole
    "a tool's implementation can itself be another agent" idea, made
    concrete.

Import it from any example:

    from _common import (
        MODEL, get_client, ticket_text, document_text, doc_refund_policy,
        BILLING_ANOMALY_ROWS, banner, report_usage, truncate,
        Tool, run_agent_loop, Specialist, make_specialist_tool,
    )

Every example adds this directory to sys.path itself, so the scripts run
from the repository root (`python3 examples/01_ops_boardroom.py`) as well
as from inside `examples/`.
"""


import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable

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
# One constant, imported everywhere, exactly as in Chapters 1-4. A Supervisor
# plus three specialists is still, underneath, four calls to this same one
# model — a boardroom does not change this story.
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

# Specialists are single-shot, stateless calls: each one does one focused
# job and returns, with no "next turn" of its own worth keeping server-side
# — matching Chapters 1-3's original convention. store=False is the
# default every Specialist.run should use.
SPECIALIST_STORE_DEFAULT: bool = False

# The Supervisor's OWN loop, by contrast, is genuinely multi-turn tool
# calling — matching Chapter 4's convention. store=True lets the server
# hold the growing conversation so only the newest function_result needs
# to be sent on each turn.
SUPERVISOR_STORE_DEFAULT: bool = True

# A hard ceiling on how many turns a single run_agent_loop() call may take.
# Never treat this as optional: an ill-specified tool loop that never
# terminates is a real, named risk (Chapter 4's 04_max_turns_cap.py), and a
# Supervisor's loop is no exception just because its "tools" are specialists
# rather than plain functions.
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
# Canonical fixture 1 — the support ticket. Byte-identical to Chapters 1-4's
# own _common.py: this chapter's Example A depends on it being the exact
# same ticket Chapter 1 classified, Chapter 2 routed, Chapter 3 grounded,
# and Chapter 4's autopilot decided on.
# ---------------------------------------------------------------------------
ticket_text: str = """Hi, I was charged twice for my October subscription. I can see two
identical GBP 49.00 charges on the same card, both dated 3 October. I have already
tried logging in to check my invoices but the billing page just spins forever.
Could someone refund the duplicate? This is the second month it has happened."""


# ---------------------------------------------------------------------------
# Canonical fixture 2 — the post-incident review document. Byte-identical to
# Chapters 1-3's own _common.py.
# ---------------------------------------------------------------------------
document_text: str = """Post-incident review: payment gateway degradation, 3 October.

Between 02:11 and 03:47 UTC, the billing service returned elevated errors on card
charge attempts. The upstream payment provider acknowledged a partial outage in their
authorisation tier during the same window.

Impact: 1,842 charge attempts failed. 96 customers were charged twice because our
retry logic did not check for an existing authorisation before resubmitting. No card
data was exposed.

Root cause: the retry wrapper treated a gateway timeout as a definitive failure. A
timeout is ambiguous — the charge may or may not have completed. The wrapper had no
idempotency key, so the retry created a second authorisation.

Remediation: idempotency keys on all charge submissions, shipped 9 October. Timeout
handling now reconciles against the provider before retrying. Duplicate charges were
refunded within 48 hours. Outstanding: we still have no alert on duplicate-charge rate,
tracked as BILL-2291."""


# ---------------------------------------------------------------------------
# Canonical fixture 3 — the refund policy. Byte-identical to Chapter 4's own
# _common.py (itself byte-identical to Chapter 3's).
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
# New fixture — a small simulated billing anomaly dataset, standing in for a
# real SQL source. No example in this chapter queries a real database. This
# is Example B's stand-in for the article's "isolated SQL analyst."
# ---------------------------------------------------------------------------
BILLING_ANOMALY_ROWS: list[dict[str, Any]] = [
    {"date": "2026-10-03", "duplicate_charges": 96, "total_charge_attempts": 1842},
    {"date": "2026-10-04", "duplicate_charges": 11, "total_charge_attempts": 1790},
    {"date": "2026-10-05", "duplicate_charges": 2, "total_charge_attempts": 1810},
]

# A small simulated customer-history table, reused by the simplified
# support_specialist in Example A (see 01_ops_boardroom.py). Deliberately
# tiny, matching Chapter 4's own CUSTOMER_HISTORY in spirit.
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
# Tool / run_agent_loop — REUSED, VERBATIM IN SHAPE, from Chapter 4. This
# chapter's whole idea is that a Supervisor is Chapter 4's tool-calling loop
# applied recursively: the only thing that changes is what lives inside
# `fn`. Chapter 4's fn bodies touched a simulated weather table or a
# simulated CRM lookup. This chapter's fn bodies make a nested
# client.interactions.create call to a specialist instead. The Tool
# dataclass and run_agent_loop function themselves are NOT redesigned.
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
    `parameters.properties` keys exactly. In this chapter, `fn` is very
    often `make_specialist_tool`'s own closure, which itself performs a
    full nested client.interactions.create call to a specialist rather
    than touching plain data.

    `requires_review` marks a tool whose real-world equivalent would be
    irreversible (sending an email, issuing a refund, escalating to a real
    system). None of this chapter's specialist-wrapping tools are
    irreversible on their own — the specialists only draft text — but the
    flag is kept for parity with Chapter 4's Tool shape and for any example
    that wants to mark a specialist call as sensitive to audit.
    """

    name: str
    declaration: dict[str, Any]
    fn: Any
    requires_review: bool = False


def run_agent_loop(
    client: Any,
    objective: str,
    tools: list[Tool],
    max_turns: int = DEFAULT_MAX_TURNS,
) -> dict[str, Any]:
    """Run a tool-using loop to completion, or until max_turns is hit.

    This is the Supervisor mechanism for this whole chapter, unchanged from
    Chapter 4: uses stateful mode (store=True, the API default) with
    previous_interaction_id to carry the conversation forward turn by turn.
    Only the newest function_result is sent as `input` on every turn after
    the first; the server already holds the rest of the history.

    Returns one of:
      {"status": "done", "answer": str, "transcript": list[dict]}
      {"status": "max_turns_reached", "transcript": list[dict]}

    `transcript` is a plain list of dicts, each one turn's worth of
    bookkeeping: the interaction id, any function_call made, and the
    function_result (if any) submitted back. In this chapter, a
    "function_call" turn is the Supervisor dispatching to a specialist, and
    the "function_result" is that specialist's full output coming back.
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
        # In this chapter, this is the moment a "tool call" turns into a
        # full nested specialist agent invocation.
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


# ---------------------------------------------------------------------------
# Specialist / make_specialist_tool — the ONE genuinely new piece of
# vocabulary this chapter adds. Everything above this point is Chapter 4,
# unmodified. A Specialist is nothing more than a name, a persona
# (system_instruction), and a callable that performs its own, separate
# client.interactions.create call. make_specialist_tool is the concrete
# proof that "a tool's body can be another disciplined agent": it wraps a
# Specialist into a Chapter-4-shaped Tool whose declaration takes one
# string argument (the input to hand the specialist) and whose fn calls
# specialist.run(...).
# ---------------------------------------------------------------------------
@dataclass
class Specialist:
    """A narrow, single-persona agent invoked by a Supervisor as a tool.

    `name` — the specialist's identifier, also used as the Supervisor
    tool's function name (so keep it a valid identifier, e.g.
    `data_analyst_specialist`).

    `system_instruction` — this specialist's OWN, separate persona. It is
    never merged with the Supervisor's system_instruction or with any
    other specialist's — that separation is the entire point of this
    chapter's pattern.

    `run` — a callable taking one input string and returning one output
    string. Its implementation makes its own, independent
    client.interactions.create call with store=False (stateless — see
    SPECIALIST_STORE_DEFAULT above). It does NOT share
    previous_interaction_id with the Supervisor or with any other
    specialist unless a specific example states a reason to.
    """

    name: str
    system_instruction: str
    run: Callable[[str], str]


def make_specialist_tool(
    specialist: Specialist,
    description: str,
    input_description: str = "The input to hand this specialist.",
) -> Tool:
    """Wrap a Specialist into a Chapter-4-shaped Tool for a Supervisor loop.

    The returned Tool's declaration takes exactly one string argument
    (named `specialist_input`); its `fn` calls `specialist.run(...)` and
    returns the specialist's plain-text output wrapped in a small dict, so
    it can be JSON-serialized as a function_result like any other tool
    result in this series.

    This is the concrete mechanic behind "a tool's implementation can
    itself be another disciplined agent": from the Supervisor's point of
    view, this is just another entry in `tools=[...]`. From the
    specialist's point of view, being called this way is indistinguishable
    from being called directly — it still only ever sees the one input
    string `run()` gives it, and does its own separate model call.
    """
    declaration: dict[str, Any] = {
        "type": "function",
        "name": specialist.name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                "specialist_input": {
                    "type": "string",
                    "description": input_description,
                },
            },
            "required": ["specialist_input"],
        },
    }

    def fn(specialist_input: str) -> dict[str, Any]:
        output = specialist.run(specialist_input)
        return {"specialist": specialist.name, "output": output}

    return Tool(name=specialist.name, declaration=declaration, fn=fn)
