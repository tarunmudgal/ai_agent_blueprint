"""Example A — The Ops Boardroom: one Supervisor, one specialist.

The smallest possible boardroom. Before building the full three-specialist
team in 02_quarterly_billing_review.py, this establishes the core mechanic
this whole chapter rests on: a Supervisor's "tool" whose body is itself a
full, separate agent invocation, rather than a plain function touching
local data.

`support_specialist` here is a deliberately SIMPLIFIED stand-in for
Chapter 4's entire Support Ticket Autopilot loop (lookup_refund_policy,
check_customer_history, escalate_to_human, draft_customer_reply, looped
until a decision). This example does not rebuild that multi-turn loop —
it gives the specialist the refund policy and the account history
directly in one input, and lets it reason in a single call. Read Chapter
4 for the full multi-turn version of this exact decision.

The Supervisor is given an objective referencing ticket_text, decides to
dispatch to support_specialist (its only registered specialist), gets back
a structured outcome, and reports a summary. Nothing here sends a real
email, issues a real refund, or escalates to a real system — every
action-shaped output stays a draft/simulation, consistent with every prior
chapter.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    CUSTOMER_HISTORY,
    MODEL,
    Specialist,
    banner,
    doc_refund_policy,
    get_client,
    make_specialist_tool,
    report_usage,
    run_agent_loop,
    ticket_text,
)

SUPPORT_SPECIALIST_SYSTEM_INSTRUCTION = """\
You are a billing support specialist. You are given one customer situation
(a ticket, plus a short account-history note) and must decide the
outcome: escalate to a human, or draft a customer reply.

This is a simplified, single-shot stand-in for Chapter 4's full Support
Ticket Autopilot loop: you are given the refund policy and the account
history directly in your input, rather than calling tools of your own to
fetch them.

Decision rule:
- A duplicate charge in a single billing period, confirmed in the ledger,
  is normally eligible for an automatic refund — draft a customer reply
  explaining the refund.
- If the customer has been charged twice in two or more consecutive
  billing cycles, the account must instead be flagged for manual review —
  escalate, and do not draft an automatic refund reply for this case.

Return a short, structured plain-text summary: the decision (escalate or
draft_reply), the reason, and — if drafting — the reply text. Never claim
anything was actually sent or actually refunded; this is a draft awaiting
human action, not a completed action.
"""


def run_support_specialist(client, specialist_input: str) -> str:
    """The support_specialist's own, separate model call.

    Stateless (store=False), matching Chapters 1-3's single-shot
    convention — this specialist does one focused job and returns. It does
    not share previous_interaction_id with the Supervisor.
    """
    interaction = client.interactions.create(
        model=MODEL,
        input=specialist_input,
        system_instruction=SUPPORT_SPECIALIST_SYSTEM_INSTRUCTION,
        store=False,
    )
    report_usage(interaction, label="support_specialist")
    return interaction.output_text


def main() -> None:
    """Run the Ops Boardroom: one Supervisor, one specialist, end to end."""
    client = get_client()

    support_specialist = Specialist(
        name="support_specialist",
        system_instruction=SUPPORT_SPECIALIST_SYSTEM_INSTRUCTION,
        run=lambda specialist_input: run_support_specialist(client, specialist_input),
    )

    support_tool = make_specialist_tool(
        support_specialist,
        description=(
            "Hand a customer support situation to the billing support "
            "specialist, who decides whether to escalate to a human or "
            "draft a customer reply. Give it the full ticket text plus any "
            "relevant account history and policy text as one input string."
        ),
        input_description=(
            "The full customer situation: ticket text, account history, "
            "and relevant policy, combined into one string for the "
            "specialist to reason over."
        ),
    )

    history = CUSTOMER_HISTORY["cust_4471"]
    specialist_input = (
        f"Ticket:\n{ticket_text}\n\n"
        f"Account history for cust_4471: {history}\n\n"
        f"Refund policy:\n{doc_refund_policy}"
    )

    objective = (
        "A customer situation needs handling. Here is everything you need "
        "to pass to the support specialist if you dispatch to it:\n\n"
        f"{specialist_input}\n\n"
        "Get it resolved and summarize the outcome for me. You have exactly "
        "one specialist available: support_specialist. Call it with the "
        "situation above as its input, then report what it decided."
    )

    banner("Example A — The Ops Boardroom")
    print("Supervisor's only specialist: support_specialist "
          "(a simplified stand-in for Chapter 4's whole autopilot loop)\n")

    result = run_agent_loop(client, objective, [support_tool], max_turns=4)

    banner("Supervisor dispatch")
    for step in result["transcript"]:
        fc = step.get("function_call")
        if fc is None:
            continue
        print(f"turn {step['turn']}: dispatched to {fc['name']}")
        fr = step.get("function_result") or {}
        print(f"  specialist output:\n  {fr.get('output', '')}")

    banner("Supervisor's final summary")
    print(f"status: {result['status']}")
    if result["status"] == "done":
        print(result["answer"])
    else:
        print("Loop hit MAX_TURNS before the Supervisor considered itself "
              "done — surfacing to a human rather than looping forever.")


if __name__ == "__main__":
    main()
