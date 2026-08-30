"""04 — Partial failure: schema-valid but semantically wrong.

Section 4.1's central failure mode is not "the model returned broken JSON" -
Pydantic already catches that (see 03). The dangerous case is the one
Pydantic CANNOT catch: a response that is perfectly schema-valid and
completely wrong, and every downstream stage trusts it blindly because
nothing about its shape looks off.

This script needs no live model call to demonstrate, on purpose: forcing a
real model to make a specific wrong judgement call is not repeatable, so
this manually constructs a plausible-but-wrong TicketClassification and
runs it through the SAME deterministic Stage 2 ROUTE code from
02_incident_response_pipeline.py, to show the routing follow it without
question.

Demonstrates:
  * a schema-valid TicketClassification that is nonetheless the wrong
    category for the ticket it claims to describe
  * ROUTE (Stage 2) making its decision purely from the object's fields,
    with no way to tell the object is wrong
  * why this failure mode needs an eval set (05_pipeline_eval.py), not a
    schema, to catch it

What to look for in the output:
  1. Both classifications validate cleanly - `model_validate` never raises.
  2. The WRONG classification still produces a confident, well-formed
     routing decision. Nothing in the pipeline "notices" the mistake.
  3. The only thing that would have caught this is a human, or an eval
     harness with a known-correct label to compare against.

Run:  python3 examples/04_partial_failure_demo.py
"""
from _common import banner, rule, ticket_text
from pydantic import BaseModel, Field

ESCALATE_URGENCY_THRESHOLD = 4
ESCALATE_CATEGORY = "account_access"


class TicketClassification(BaseModel):
    category: str = Field(
        description="one of: billing, technical, account_access, "
                    "feature_request, other",
    )
    urgency: int = Field(ge=1, le=5)
    reason: str


class RoutingDecision(BaseModel):
    escalate: bool
    rule_fired: str


def route(classification: TicketClassification) -> RoutingDecision:
    """Identical logic to Stage 2 in 02_incident_response_pipeline.py.

    Reused here unchanged, on purpose: the point of this demo is that the
    routing code is completely correct and still produces a wrong outcome,
    because the object it trusts is wrong.
    """
    if (
        classification.urgency >= ESCALATE_URGENCY_THRESHOLD
        or classification.category == ESCALATE_CATEGORY
    ):
        return RoutingDecision(
            escalate=True,
            rule_fired=(
                f"urgency={classification.urgency} >= "
                f"{ESCALATE_URGENCY_THRESHOLD} or "
                f"category == {ESCALATE_CATEGORY!r}"
            ),
        )
    return RoutingDecision(
        escalate=False,
        rule_fired="no escalation rule matched - continuing automatically",
    )


def main() -> None:
    banner("The ticket in question")
    print(ticket_text)
    print(
        "\nThe ticket describes: a duplicate charge (billing), a login page "
        "that hangs (arguably account_access, arguably a technical symptom), "
        "and a repeat occurrence ('the second month'). A reasonable human "
        "classifier would call this billing, urgency 4 - real money, no "
        "workaround, recurring."
    )

    rule()
    banner("Correct classification (schema-valid, semantically right)")
    correct = TicketClassification(
        category="billing",
        urgency=4,
        reason="Customer reports two identical GBP 49.00 charges, recurring "
               "for a second month.",
    )
    print(correct.model_dump_json(indent=2))
    correct_routing = route(correct)
    print(f"-> routing: escalate={correct_routing.escalate} "
          f"({correct_routing.rule_fired})")

    rule()
    banner("Wrong classification (schema-valid, semantically wrong)")
    print(
        "Manually constructed - not produced by a live call - to show what "
        "happens when the model latches onto 'billing page spins' and "
        "misreads the ticket as a login problem instead of a refund request. "
        "Nothing about the object's SHAPE is wrong."
    )
    wrong = TicketClassification(
        category="account_access",
        urgency=2,
        reason="Customer mentions the billing page not loading.",
    )
    print(wrong.model_dump_json(indent=2))
    wrong_routing = route(wrong)
    print(f"-> routing: escalate={wrong_routing.escalate} "
          f"({wrong_routing.rule_fired})")

    rule()
    banner("The gap this exposes")
    print(
        "Both objects passed model_validate_json() with zero errors. ROUTE\n"
        "made a perfectly logical decision from each one. The correct case\n"
        "escalates a real billing emergency; the wrong case quietly closes\n"
        "it as a low-urgency access hiccup, with no error, no exception,\n"
        "and no signal anywhere in the pipeline that anything went wrong.\n"
        "\n"
        "A schema catches malformed output. It cannot catch confidently\n"
        "wrong output - that is what a golden-set eval (05_pipeline_eval.py)\n"
        "is for: compare against a KNOWN label, not against a shape."
    )


if __name__ == "__main__":
    main()
