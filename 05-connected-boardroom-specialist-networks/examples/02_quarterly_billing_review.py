"""Example B — The Quarterly Billing Review (the chapter's centerpiece).

The article's own scenario, built literally: "an isolated SQL analyst, a
mathematical tool runner, and a document researcher." Three specialists,
each with a DELIBERATELY narrow and DELIBERATELY conflicting persona:

  - data_analyst_specialist   -- strict, literal, numbers-only. Given
                                  BILLING_ANOMALY_ROWS. Forbidden from
                                  speculating about cause.
  - policy_specialist         -- grounded-retrieval persona, reusing
                                  Chapter 3's GroundedAnswer discipline
                                  against doc_refund_policy (simplified
                                  keyword lookup, same simplification
                                  Chapter 4 already made).
  - communications_specialist -- warm, empathetic, customer-facing.
                                  Deliberately the OPPOSITE persona from
                                  the data analyst. Drafts (never sends) a
                                  customer explanation from the other two
                                  specialists' VERBATIM outputs.

The Supervisor's own system_instruction explicitly forbids it from doing
any specialist's job itself: no computing statistics, no reciting policy
from its own memory, no drafting customer language on its own. Its ONLY
job is deciding which specialists to call, in what order, and assembling
their outputs into one final report.

Call-count honesty: this run is, at minimum, the Supervisor's own turns
PLUS three specialist calls (data analyst, policy, communications) — a
boardroom's cost compounds a THIRD way beyond a fixed pipeline (Chapter 2)
or a single tool loop (Chapter 4). See 05-reusable-artifacts.md and
06-production.md for the full accounting.

Nothing here sends a real email, issues a real refund, or writes to a real
system. The communications specialist's draft is explicitly marked as a
draft, never sent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    BILLING_ANOMALY_ROWS,
    MODEL,
    Specialist,
    banner,
    doc_refund_policy,
    get_client,
    make_specialist_tool,
    report_usage,
    rule,
    run_agent_loop,
)

DATA_ANALYST_SYSTEM_INSTRUCTION = """\
You are a data analyst. You are given a small set of billing-anomaly rows
(date, duplicate_charges, total_charge_attempts) and nothing else.

Rules — absolute:
- Report ONLY what the given rows show. Compute rates directly from the
  numbers you were given (duplicate_charges / total_charge_attempts).
- Do not speculate about cause. Do not mention root causes, remediation,
  or anything not present in the rows themselves.
- Do not soften, hedge, or add reassurance. Precision, not comfort — a
  different specialist handles tone.
- Do not draft any customer-facing language. Out of scope for you.

Output a short, literal report: per-date duplicate-charge counts, attempt
counts, and the computed rate for each date, plus the trend across the
dates given. Nothing else.
"""

POLICY_SYSTEM_INSTRUCTION = """\
You are a policy researcher. You are given the full text of the refund and
duplicate-charge policy and a question to answer against it.

Reuse Chapter 3's GroundedAnswer discipline: every claim you make must be
traceable to a specific passage in the policy text you were given. If the
policy text does not clearly answer the question, say so explicitly
rather than filling the gap with plausible-sounding but unsupported text.

This is a simplified keyword lookup over the policy, not Chapter 3's real
embedding-based Corpus and similarity search — the grounding discipline is
what carries over; see Chapter 3 for the real retrieval mechanics.

Output a short answer to the question asked, quoting or closely
paraphrasing the exact policy passage(s) that support it. Do not draft
customer-facing language and do not compute or restate any statistics —
both are other specialists' jobs.
"""

COMMUNICATIONS_SYSTEM_INSTRUCTION = """\
You are a customer communications writer. You are given two other
specialists' outputs verbatim — a data analyst's numeric findings and a
policy specialist's grounded policy answer — and must draft a warm,
empathetic customer-facing explanation from them.

Persona — deliberately the opposite of the data analyst: warm and
empathetic, not clipped or dry. This is not a contradiction to resolve —
it is the whole reason this chapter splits personas into separate
specialists instead of cramming both into one system prompt.

Rules:
- Use the data analyst's numbers and the policy specialist's policy
  citation VERBATIM as the facts underlying your draft. Do not invent a
  number, date, or policy clause you were not given.
- If either input is missing or marked failed, say so honestly rather
  than inventing a fact to fill the gap.

Boundaries: this draft is NEVER sent. You are producing a DRAFT for a
human to review and send. Do not claim or imply anything was already
sent, refunded, or actioned — say "we will," not "we have." Do not
compute your own statistics and do not recite policy from your own
general knowledge.
"""

SUPERVISOR_SYSTEM_INSTRUCTION = """\
You are the Supervisor of a small specialist team: data_analyst_specialist,
policy_specialist, and communications_specialist. Each is a separate,
narrowly-scoped agent with its own persona. You are not.

Your only job is deciding which specialists to call, in what order, and
assembling what they return into one final report. Nothing more.

Explicitly forbidden — do not do any specialist's job yourself:
- Do NOT compute any statistic, percentage, or rate yourself. That is
  data_analyst_specialist's job. If you need a number, call it.
- Do NOT recite or paraphrase refund policy from your own memory or
  training. That is policy_specialist's job. If you need to know what
  policy says, call it.
- Do NOT draft customer-facing language yourself. That is
  communications_specialist's job, and it needs the other two
  specialists' actual outputs to do it — call them first.

Ordering: call data_analyst_specialist and policy_specialist BEFORE
communications_specialist — the communications draft depends on both of
their outputs as verbatim inputs, not on your own summary of them.

Your final answer must be traceable back to what the specialists actually
returned — quote or closely paraphrase their outputs rather than
inventing new facts, numbers, or policy language of your own. If a
specialist's result looks incomplete or missing, say so honestly in your
final report rather than filling the gap yourself.
"""


def _run_specialist(client, system_instruction: str, specialist_input: str, label: str) -> str:
    """One specialist's own, separate, stateless model call.

    store=False, matching Chapters 1-3's single-shot convention. This
    specialist call shares nothing — no previous_interaction_id — with the
    Supervisor's own loop or with any other specialist.
    """
    interaction = client.interactions.create(
        model=MODEL,
        input=specialist_input,
        system_instruction=system_instruction,
        store=False,
    )
    report_usage(interaction, label=label)
    return interaction.output_text


def main() -> None:
    """Run the Quarterly Billing Review boardroom end to end."""
    client = get_client()

    def run_data_analyst(specialist_input: str) -> str:
        output = _run_specialist(
            client, DATA_ANALYST_SYSTEM_INSTRUCTION, specialist_input,
            label="data_analyst_specialist",
        )
        banner("data_analyst_specialist output")
        print(output)
        return output

    def run_policy(specialist_input: str) -> str:
        output = _run_specialist(
            client, POLICY_SYSTEM_INSTRUCTION, specialist_input,
            label="policy_specialist",
        )
        banner("policy_specialist output")
        print(output)
        return output

    def run_communications(specialist_input: str) -> str:
        output = _run_specialist(
            client, COMMUNICATIONS_SYSTEM_INSTRUCTION, specialist_input,
            label="communications_specialist",
        )
        banner("communications_specialist output (DRAFT — NOT SENT)")
        print(output)
        return output

    data_analyst_specialist = Specialist(
        name="data_analyst_specialist",
        system_instruction=DATA_ANALYST_SYSTEM_INSTRUCTION,
        run=run_data_analyst,
    )
    policy_specialist = Specialist(
        name="policy_specialist",
        system_instruction=POLICY_SYSTEM_INSTRUCTION,
        run=run_policy,
    )
    communications_specialist = Specialist(
        name="communications_specialist",
        system_instruction=COMMUNICATIONS_SYSTEM_INSTRUCTION,
        run=run_communications,
    )

    tools = [
        make_specialist_tool(
            data_analyst_specialist,
            description=(
                "Get a strict, literal, numbers-only report from the data "
                "analyst. Give it the raw billing-anomaly rows as input; it "
                "will not speculate about cause and will not draft any "
                "customer-facing language."
            ),
            input_description="The raw billing-anomaly rows, as text, for the analyst to compute rates from.",
        ),
        make_specialist_tool(
            policy_specialist,
            description=(
                "Ask the policy specialist a grounded question against the "
                "refund and duplicate-charge policy. It will only answer "
                "from the policy text it is given and will say so if the "
                "policy does not cover the question."
            ),
            input_description="The full policy text plus the specific question to answer against it.",
        ),
        make_specialist_tool(
            communications_specialist,
            description=(
                "Ask the communications specialist to draft a warm, "
                "empathetic customer explanation. Give it the data "
                "analyst's and policy specialist's VERBATIM outputs as "
                "input — never a paraphrase of them. Produces a DRAFT, "
                "never sent."
            ),
            input_description=(
                "The data analyst's verbatim output and the policy "
                "specialist's verbatim output, combined into one input "
                "string for the communications specialist to draft from."
            ),
        ),
    ]

    rows_text = "\n".join(
        f"{r['date']}: {r['duplicate_charges']} duplicate charges out of "
        f"{r['total_charge_attempts']} attempts"
        for r in BILLING_ANOMALY_ROWS
    )

    objective = (
        SUPERVISOR_SYSTEM_INSTRUCTION
        + "\n\nWe had a spike in duplicate charges this quarter. Get the "
        "facts, check what policy says, and draft a customer-facing "
        "explanation.\n\n"
        f"Billing anomaly rows (for data_analyst_specialist, if you call it):\n{rows_text}\n\n"
        f"Refund policy text (for policy_specialist, if you call it):\n{doc_refund_policy}\n\n"
        "Question for policy_specialist: are duplicate charges like these "
        "eligible for an automatic refund, and under what condition would "
        "manual review be required instead?\n\n"
        "Call data_analyst_specialist and policy_specialist first, then "
        "call communications_specialist with their verbatim outputs, then "
        "assemble a final report from all three."
    )

    banner("Example B — The Quarterly Billing Review")
    print("Three specialists, deliberately conflicting personas: "
          "data_analyst_specialist, policy_specialist, communications_specialist\n")
    rule()

    result = run_agent_loop(client, objective, tools, max_turns=8)

    banner("Supervisor dispatch order")
    call_count = 0
    for step in result["transcript"]:
        fc = step.get("function_call")
        if fc is None:
            continue
        call_count += 1
        print(f"turn {step['turn']}: dispatched to {fc['name']}")

    banner("Supervisor's final assembled report")
    print(f"status: {result['status']}")
    if result["status"] == "done":
        print(result["answer"])
    else:
        print("Loop hit MAX_TURNS before the Supervisor considered itself "
              "done — surfacing to a human rather than looping forever.")

    banner("Cost-stacking honesty")
    print(
        f"Total specialist dispatches this run: {call_count}. Cost here is "
        "the Supervisor's own turns PLUS every specialist call it made — "
        "at minimum 1 (Supervisor's first turn) + 3 (one per specialist) "
        "= 4 model calls, likely more once the Supervisor's own "
        "synthesis turn is counted. Compare Chapter 2's fixed N-stage "
        "pipeline cost and Chapter 4's turns-taken loop cost — a "
        "boardroom's cost compounds a third way on top of both."
    )


if __name__ == "__main__":
    main()
