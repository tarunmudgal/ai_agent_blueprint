"""05 — A golden-set eval harness for the Incident Response Pipeline.

Mirrors Chapter 1's examples/11_eval_harness.py, but grades the whole
CLASSIFY + ROUTE pair, not a bare classification: a pipeline stage that
looks right in isolation can still feed the wrong thing to a deterministic
routing rule downstream, so the eval grades the outcome that actually
matters - whether the ticket got routed the way a human would expect.

Demonstrates:
  * a golden set of (ticket, expected_category, expected_routing) cases
  * running each ticket through the REAL classify stage, then the REAL
    (code-only) route stage - no simulated payloads here, unlike 03 and 04
  * a per-case pass/fail table and an overall accuracy figure

What to look for in the output:
  1. The FAIL rows, same as Chapter 1: read each one and decide whether the
     prompt or the golden label is wrong.
  2. A case can get the category right and the routing wrong, or vice
     versa, if urgency drifts across the escalation threshold - the table
     grades both independently so you can tell which failed.
  3. Eight cases is a smoke test. This is here to be extended, not trusted
     as-is - see Chapter 1's own honesty about golden-set size.

Run:  python3 examples/05_pipeline_eval.py
"""
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import BaseModel, Field, ValidationError  # noqa: E402

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
    rule,
    ticket_text,
)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
PASS_THRESHOLD = 0.75

ESCALATE_URGENCY_THRESHOLD = 4
ESCALATE_CATEGORY = "account_access"


def load_system_prompt(filename: str) -> str:
    """Read a prompt file and strip its YAML frontmatter, keeping the body."""
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


CLASSIFIER_PROMPT = load_system_prompt("ticket_classifier.system.md")


class TicketClassification(BaseModel):
    category: str = Field(
        description="one of: billing, technical, account_access, "
                    "feature_request, other",
    )
    urgency: int = Field(ge=1, le=5)
    reason: str


def route(classification: TicketClassification) -> bool:
    """Identical rule to Stage 2 of 02_incident_response_pipeline.py.

    Returns True if the ticket should escalate to a human.
    """
    return (
        classification.urgency >= ESCALATE_URGENCY_THRESHOLD
        or classification.category == ESCALATE_CATEGORY
    )


# (ticket, expected_category, expected_escalate)
GOLDEN_CASES: list[tuple[str, str, bool]] = [
    (ticket_text, "billing", True),
    ("I was charged twice for the September invoice. Please refund the "
     "duplicate.", "billing", False),
    ("The export button spins forever and never downloads the CSV. Chrome "
     "141, macOS.", "technical", False),
    ("I can't log in - the password reset email never arrives. Checked "
     "spam.", "account_access", True),
    ("Any chance you could add a dark mode? My team works nights.",
     "feature_request", False),
    ("Just wanted to say the new dashboard is lovely. No issue, no reply "
     "needed.", "other", False),
    ("SSO via Okta stopped working for the whole engineering group this "
     "morning.", "account_access", True),
    ("API returns 500 on POST /v2/reports about one time in ten.",
     "technical", False),
]


@dataclass
class CaseResult:
    index: int
    ticket: str
    expected_category: str
    actual_category: str | None
    category_passed: bool
    expected_escalate: bool
    actual_escalate: bool | None
    routing_passed: bool
    note: str


def run_case(client: Any, index: int, ticket: str,
             expected_category: str, expected_escalate: bool) -> CaseResult:
    """Run CLASSIFY then ROUTE for real, grade both against the golden case."""
    interaction = client.interactions.create(
        model=MODEL,
        input=ticket,
        system_instruction=CLASSIFIER_PROMPT,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": TicketClassification.model_json_schema(),
        },
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
    )

    try:
        classification = TicketClassification.model_validate_json(
            interaction.output_text
        )
    except ValidationError as exc:
        return CaseResult(
            index=index,
            ticket=ticket,
            expected_category=expected_category,
            actual_category=None,
            category_passed=False,
            expected_escalate=expected_escalate,
            actual_escalate=None,
            routing_passed=False,
            note=f"invalid JSON ({exc.error_count()} err)",
        )

    escalate = route(classification)
    return CaseResult(
        index=index,
        ticket=ticket,
        expected_category=expected_category,
        actual_category=classification.category,
        category_passed=(classification.category == expected_category),
        expected_escalate=expected_escalate,
        actual_escalate=escalate,
        routing_passed=(escalate == expected_escalate),
        note="",
    )


def print_table(results: list[CaseResult]) -> None:
    header = (f"{'#':<3}{'':<6}{'exp_cat':<17}{'act_cat':<17}"
              f"{'exp_esc':<9}{'act_esc':<9}{'note'}")
    print(header)
    print("-" * 74)
    for r in results:
        overall = "PASS" if (r.category_passed and r.routing_passed) else "FAIL"
        act_cat = r.actual_category if r.actual_category is not None else "-"
        act_esc = str(r.actual_escalate) if r.actual_escalate is not None else "-"
        print(f"{r.index:<3}{overall:<6}{r.expected_category:<17}{act_cat:<17}"
              f"{str(r.expected_escalate):<9}{act_esc:<9}{r.note}")


def main() -> None:
    client = get_client()

    banner(f"Golden-set eval: {len(GOLDEN_CASES)} cases against {MODEL}")

    results: list[CaseResult] = []
    for index, (ticket, expected_category, expected_escalate) in enumerate(
        GOLDEN_CASES, start=1
    ):
        result = run_case(client, index, ticket, expected_category, expected_escalate)
        results.append(result)
        print(f"  ran case {index}/{len(GOLDEN_CASES)}")

    banner("Per-case results")
    print_table(results)

    passed = sum(1 for r in results if r.category_passed and r.routing_passed)
    accuracy = passed / len(results) if results else 0.0

    rule()
    print(f"category accuracy: "
          f"{sum(1 for r in results if r.category_passed)}/{len(results)}")
    print(f"routing accuracy : "
          f"{sum(1 for r in results if r.routing_passed)}/{len(results)}")

    banner("Result")
    print(f"combined accuracy: {passed}/{len(results)} = {accuracy:.1%}   "
          f"threshold: {PASS_THRESHOLD:.0%}")

    if accuracy < PASS_THRESHOLD:
        print("\nBELOW THRESHOLD - exiting non-zero so CI blocks the merge.")
        sys.exit(1)

    print("\nAt or above threshold.")


if __name__ == "__main__":
    main()
