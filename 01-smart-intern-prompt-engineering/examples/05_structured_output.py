"""05 — Structured output: stop parsing prose.

Demonstrates:
  * a Pydantic model as the contract
  * response_format with mime_type application/json and the model's
    model_json_schema()
  * validating the reply with model_validate_json()
  * what to actually DO when validation fails, which in a single-shot
    system is the interesting half of the problem

What to look for in the output:
  1. The happy path prints typed Python attributes, not a string you have
     to regex.
  2. The schema constrains the SHAPE of the answer, not its CORRECTNESS.
     A syntactically perfect JSON object can still hold the wrong
     category. Schemas buy you parseability; evals (11) buy you accuracy.
  3. The failure demo shows the three responses available to you when the
     JSON does not validate: reject, degrade, or escalate. There is no
     fourth option called "retry silently" - a Smart Intern has no loop.

Run:  python3 examples/05_structured_output.py
"""
import json
import sys

from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import BaseModel, Field, ValidationError  # noqa: E402

from _common import (  # noqa: E402
    CATEGORIES,
    MODEL,
    SAMPLE_TICKETS,
    STORE_DEFAULT,
    banner,
    get_client,
    report_usage,
    rule,
    ticket_text,
)


class TicketClassification(BaseModel):
    """The contract between the model and everything downstream of it."""

    category: str = Field(
        description="Exactly one of: " + ", ".join(CATEGORIES),
    )
    urgency: int = Field(
        ge=1,
        le=5,
        description="1 = no rush, 5 = customer's business is stopped",
    )
    reason: str = Field(
        description="One short sentence justifying the category, quoting "
                    "the ticket where possible",
    )


SYSTEM_INSTRUCTION = (
    "You are a support-ticket triage classifier. Choose exactly one category "
    "from: " + ", ".join(CATEGORIES) + ". Base the urgency on customer impact "
    "described in the ticket, not on the customer's tone. Return JSON only."
)


def classify(client: Any, ticket: str) -> TicketClassification | None:
    """Classify one ticket, returning None if the contract was broken."""
    interaction = client.interactions.create(
        model=MODEL,
        input=ticket,
        system_instruction=SYSTEM_INSTRUCTION,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            # Pydantic generates the JSON Schema; we never hand-write it.
            # Change the model class and the contract follows automatically.
            "schema": TicketClassification.model_json_schema(),
        },
        generation_config={
            # Classification is fact-extraction, not reasoning. Google's own
            # guidance says minimal/low here. See 06 for the cost of getting
            # this wrong.
            "thinking_level": "low",
        },
        store=STORE_DEFAULT,
    )

    report_usage(interaction, label="classify")

    try:
        return TicketClassification.model_validate_json(interaction.output_text)
    except ValidationError as exc:
        # This is the branch people forget to write. It WILL execute one day.
        print("VALIDATION FAILED - the model returned something off-contract.")
        print(f"raw output: {interaction.output_text!r}")
        print(f"pydantic said: {exc.error_count()} error(s)")
        for err in exc.errors()[:3]:
            loc = ".".join(str(p) for p in err["loc"]) or "<root>"
            print(f"  - {loc}: {err['msg']}")
        return None


def demo_validation_failure() -> None:
    """Show the failure branch without needing the model to misbehave.

    Reproducing a real bad response on demand is unreliable, so we feed
    the validator payloads that are wrong in the three ways that actually
    happen in production.
    """
    banner("What a broken contract looks like")

    bad_payloads = [
        ('{"category": "billing", "urgency": 9, "reason": "x"}',
         "out-of-range value - schema said 1-5"),
        ('{"category": "billing", "reason": "x"}',
         "missing required field"),
        ("Here is the JSON you asked for:\n"
         '```json\n{"category": "billing", "urgency": 2, "reason": "x"}\n```',
         "valid JSON wrapped in prose and a code fence"),
    ]

    for payload, description in bad_payloads:
        rule()
        print(f"case: {description}")
        try:
            parsed = TicketClassification.model_validate_json(payload)
            print(f"  parsed fine: {parsed}")
        except ValidationError as exc:
            print(f"  rejected: {exc.error_count()} error(s) - "
                  f"{exc.errors()[0]['msg']}")

    rule()
    print(
        "Your three options, and you must pick one before you ship:\n"
        "  REJECT   - fail the request loudly. Correct when a wrong answer\n"
        "             is worse than no answer (anything billing-adjacent).\n"
        "  DEGRADE  - fall back to a safe default, e.g. category='other',\n"
        "             urgency=3, and flag it for a human queue.\n"
        "  ESCALATE - hand the raw ticket to a person untouched.\n"
        "Retrying is not on this list. A retry loop is Blueprint 4."
    )


def main() -> None:
    client = get_client()

    banner("Structured classification of the sample tickets")
    # The canonical ticket first, then two terser ones, so you can see the
    # same contract hold across a realistic multi-paragraph ticket and a
    # one-liner.
    for ticket in [ticket_text, *SAMPLE_TICKETS[1:3]]:
        rule()
        print(f"ticket: {ticket}")
        result = classify(client, ticket)
        if result is None:
            print("  -> DEGRADED to category='other', urgency=3, needs review")
            continue
        # Typed attributes. No string parsing anywhere downstream.
        print(f"  -> category={result.category}  urgency={result.urgency}")
        print(f"     reason: {result.reason}")

    demo_validation_failure()

    banner("The schema we sent")
    print(json.dumps(TicketClassification.model_json_schema(), indent=2))


if __name__ == "__main__":
    main()
