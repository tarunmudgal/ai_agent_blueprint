"""02 — The Incident Response Pipeline: Chapter 1's three prompts, chained.

    ticket_text -> CLASSIFY (Ch1) -> ROUTE (plain code) -> REWRITE (Ch1)
                -> LOG SUMMARY (Ch1)

Demonstrates:
  * reusing three of Chapter 1's exact prompts, unmodified, as pipeline
    stages - a pipeline is not always a new prompt written for the
    occasion, it is often old prompts wired into a new order
  * Stage 2, ROUTE, is a FIXED, deterministic Python rule and makes NO
    model call at all: `urgency >= 4 or category == "account_access"`
    escalates, otherwise the ticket continues automatically. A "stage" in
    this blueprint is a unit of the pipeline, not necessarily an LLM call.
  * feeding one stage's structured output into the next stage's prompt as
    plain text - the classifier's Pydantic object becomes part of the
    rewriter's input, and the whole run becomes part of the summarizer's
    input

What to look for in the output:
  1. Stage 2 prints no token usage and makes no network call - watch for
     the explicit "no model call" line in its output.
  2. The rewriter (Stage 3) still enforces its original three-line
     contract even though its input here is "ticket + classification"
     rather than a bare stack trace - the prompt itself never changed.
  3. The final one-line log record is what an on-call engineer would
     actually scan, not the four stages that produced it.

Run:  python3 examples/02_incident_response_pipeline.py
"""
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    Pipeline,
    Stage,
    banner,
    get_client,
    report_usage,
    rule,
    ticket_text,
)
from pydantic import BaseModel, Field, ValidationError  # noqa: E402

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_system_prompt(filename: str) -> str:
    """Read a prompt file and strip its YAML frontmatter, keeping the body."""
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


CLASSIFIER_PROMPT = load_system_prompt("ticket_classifier.system.md")
REWRITER_PROMPT = load_system_prompt("error_rewriter.system.md")
SUMMARIZER_PROMPT = load_system_prompt("summarizer.system.md")

ESCALATE_URGENCY_THRESHOLD = 4
ESCALATE_CATEGORY = "account_access"


class TicketClassification(BaseModel):
    """Ch1 §3.4's exact shape - the seam between Stage 1 and everything after."""

    category: str = Field(
        description="one of: billing, technical, account_access, "
                    "feature_request, other",
    )
    urgency: int = Field(ge=1, le=5)
    reason: str


class RoutingDecision(BaseModel):
    """Stage 2's output - built in Python, never returned by the model."""

    escalate: bool
    rule_fired: str


def make_classify_stage(client: Any) -> Stage:
    """Stage 1 — CLASSIFY. Chapter 1's ticket_classifier prompt, verbatim."""

    def run(ticket: str) -> TicketClassification:
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
        report_usage(interaction, label="classify")
        try:
            return TicketClassification.model_validate_json(
                interaction.output_text
            )
        except ValidationError as exc:
            raise ValueError(f"classify returned an off-contract payload: {exc}") from exc

    return Stage(name="classify", run=run, output_schema=TicketClassification)


def route(classification: TicketClassification) -> RoutingDecision:
    """Stage 2 — ROUTE. Plain Python. NO model call, on purpose.

    This is the running example, across this whole chapter, of a pipeline
    stage that is not an LLM call at all. The rule is fixed and decided
    before the pipeline ever runs - it reacts to the classifier's OUTPUT
    VALUE, not to some open-ended judgement a model would have to make, so
    it stays inside a "strict, pre-determined order": every input either
    trips the rule or it does not, there is no dynamic re-planning.
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


def make_route_stage() -> Stage:
    """Wrap the plain `route` function as a Stage, for uniform pipeline use.

    No client is threaded in here at all - the strongest signal in this
    file that this stage never touches the network.
    """
    return Stage(name="route", run=route, output_schema=RoutingDecision)


def make_rewrite_stage(client: Any) -> Stage:
    """Stage 3 — REWRITE. Chapter 1's error_rewriter prompt, verbatim.

    Repurposed here: instead of a bare stack trace, its input is the
    ticket plus the classifier's own reasoning, framed as the "raw error"
    the prompt was written to plain-language-ify. The prompt text itself
    is untouched.
    """

    def run(state: tuple[str, TicketClassification, RoutingDecision]) -> str:
        ticket, classification, routing = state
        raw_input = (
            f"Ticket: {ticket}\n\n"
            f"Internal classification: category={classification.category}, "
            f"urgency={classification.urgency}, reason={classification.reason}\n"
            f"Routing: {'escalated to a human' if routing.escalate else 'handled automatically'}"
        )
        interaction = client.interactions.create(
            model=MODEL,
            input=raw_input,
            system_instruction=REWRITER_PROMPT,
            generation_config={"thinking_level": "low"},
            store=STORE_DEFAULT,
        )
        report_usage(interaction, label="rewrite")
        return interaction.output_text

    return Stage(name="rewrite", run=run)


def make_log_summary_stage(client: Any, ticket: str,
                            classification: TicketClassification,
                            routing: RoutingDecision) -> Stage:
    """Stage 4 — LOG SUMMARY. Chapter 1's summarizer prompt, verbatim.

    Applied here to a synthesized document combining the whole run, rather
    than to a single incident memo - the prompt's grounding rules do not
    care where the text came from, only that it is the sole source.
    """

    def run(rewritten_response: str) -> str:
        synthesized = (
            f"Support ticket handling record.\n\n"
            f"Original ticket: {ticket}\n\n"
            f"Classification: category={classification.category}, "
            f"urgency={classification.urgency}. Reason: {classification.reason}\n\n"
            f"Routing decision: "
            f"{'escalated to a human agent' if routing.escalate else 'handled automatically'} "
            f"({routing.rule_fired}).\n\n"
            f"Customer-facing response sent:\n{rewritten_response}"
        )
        interaction = client.interactions.create(
            model=MODEL,
            input=synthesized,
            system_instruction=SUMMARIZER_PROMPT,
            generation_config={"thinking_level": "low"},
            store=STORE_DEFAULT,
        )
        report_usage(interaction, label="log_summary")
        return interaction.output_text

    return Stage(name="log_summary", run=run)


def main() -> None:
    client = get_client()

    banner("Incident Response Pipeline — Stage 1: CLASSIFY")
    classify_stage = make_classify_stage(client)
    classification = classify_stage.run(ticket_text)
    print(f"category={classification.category}  urgency={classification.urgency}")
    print(f"reason: {classification.reason}")

    rule()
    banner("Stage 2: ROUTE — plain Python, no model call")
    route_stage = make_route_stage()
    routing = route_stage.run(classification)
    print("(no client.interactions.create() call in this stage)")
    print(f"escalate={routing.escalate}  rule_fired: {routing.rule_fired}")

    rule()
    banner("Stage 3: REWRITE")
    rewrite_stage = make_rewrite_stage(client)
    rewritten = rewrite_stage.run((ticket_text, classification, routing))
    print(rewritten)

    rule()
    banner("Stage 4: LOG SUMMARY")
    log_stage = make_log_summary_stage(client, ticket_text, classification, routing)
    log_paragraph = log_stage.run(rewritten)
    print(log_paragraph)

    banner("Final one-line log record")
    print(
        f"ticket=October-double-charge category={classification.category} "
        f"urgency={classification.urgency} "
        f"escalated={routing.escalate} summary={log_paragraph[:80]!r}"
    )


if __name__ == "__main__":
    main()
