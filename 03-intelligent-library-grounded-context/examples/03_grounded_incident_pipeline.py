"""03 — Example B, "Grounded Incident Response": the extended 5-stage pipeline.

    ticket_text -> CLASSIFY (Ch1) -> ROUTE (plain code) -> GROUND (new, Ch3)
                -> REWRITE (Ch1) -> LOG SUMMARY (Ch1)

This chapter inserts exactly ONE new stage into Chapter 2's own Incident
Response Pipeline, between ROUTE and REWRITE. Chapter 1 gave this pipeline
its prompts. Chapter 2 gave it structure and reuse discipline. Chapter 3
gives it a memory it can look things up in: the rewrite stage's
customer-facing explanation now cites the actual refund policy, instead of
the model inventing plausible-sounding policy language from its own
training data.

Demonstrates:
  * Chapter 2's exact Stage/Pipeline classes, imported unchanged from
    _common.py, now composing THREE kinds of stage in one run: a reused
    Ch1 prompt (CLASSIFY), plain code with no model call (ROUTE), and a
    retrieval stage that calls embed_content rather than
    interactions.create (GROUND) - before REWRITE (another reused Ch1
    prompt) and LOG SUMMARY (a third).
  * the GROUND stage embedding the ticket's own text as a RETRIEVAL_QUERY
    and retrieving the most relevant chunk from the same four-document
    corpus built in 01/02 - in this case, doc_refund_policy.
  * passing both the ticket AND the retrieved policy chunk into REWRITE, so
    the rewritten explanation is grounded rather than invented.

What to look for in the output:
  1. GROUND prints no interactions.create() usage line - like ROUTE, it is
     a stage that does touch the network, but through embed_content, never
     through the model that would generate prose.
  2. The retrieved chunk and its similarity score are printed explicitly -
     this pipeline never hides which document justified the final answer.
  3. This pattern retrieves and grounds. It does not act: nothing in this
     pipeline issues the refund, only drafts an explanation citing the
     policy for a human (or a downstream, separately-approved system) to
     act on. The moment a stage here started writing to a database or
     sending an email on its own initiative, this would quietly become
     Blueprint 4.

Run:  python3 examples/03_grounded_incident_pipeline.py
"""
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    Chunk,
    Corpus,
    Pipeline,
    Stage,
    banner,
    chunk_text,
    doc_api_rate_limits,
    doc_onboarding_faq,
    doc_refund_policy,
    document_text,
    get_client,
    report_usage,
    rule,
    ticket_text,
)
from pydantic import BaseModel, Field, ValidationError  # noqa: E402

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

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
REWRITER_PROMPT = load_system_prompt("error_rewriter.system.md")
SUMMARIZER_PROMPT = load_system_prompt("summarizer.system.md")


class TicketClassification(BaseModel):
    """Ch1's exact shape - the seam between CLASSIFY and everything after."""

    category: str = Field(
        description="one of: billing, technical, account_access, "
                    "feature_request, other",
    )
    urgency: int = Field(ge=1, le=5)
    reason: str


class RoutingDecision(BaseModel):
    """ROUTE's output - built in Python, never returned by the model."""

    escalate: bool
    rule_fired: str


class GroundingResult(BaseModel):
    """GROUND's output: the chunk retrieved for this ticket, plus its score.

    Not a model response - constructed in Python from Corpus.search().
    """

    chunk_label: str
    chunk_text: str
    similarity: float


def build_corpus() -> Corpus:
    """Same four-document corpus as 01 and 02, rebuilt here so this script
    is independently runnable."""
    chunks: list[Chunk] = []
    for doc_name, text in [
        ("document_text", document_text),
        ("doc_refund_policy", doc_refund_policy),
        ("doc_onboarding_faq", doc_onboarding_faq),
        ("doc_api_rate_limits", doc_api_rate_limits),
    ]:
        chunks.extend(chunk_text(text, doc_name))
    return Corpus(chunks)


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
    """Stage 2 — ROUTE. Plain Python, reused verbatim from Chapter 2. NO
    model call, on purpose."""
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
    """Wrap `route` as a Stage - no client threaded in, no network at all."""
    return Stage(name="route", run=route, output_schema=RoutingDecision)


def make_ground_stage(client: Any, corpus: Corpus, ticket: str) -> Stage:
    """Stage 3 — GROUND. New this chapter.

    Embeds the ticket's own text as a RETRIEVAL_QUERY and retrieves the
    single most relevant chunk from the four-document corpus. This is the
    ONE new problem Chapter 1 structurally could not solve: deciding WHICH
    document belongs in the next prompt, when there are too many documents
    to paste all of them.
    """

    def run(state: tuple[TicketClassification, RoutingDecision]) -> tuple[
        TicketClassification, RoutingDecision, GroundingResult
    ]:
        classification, routing = state
        top = corpus.search(client, ticket, k=1)
        chunk, score = top[0]
        grounding = GroundingResult(
            chunk_label=chunk.label, chunk_text=chunk.text, similarity=score
        )
        return classification, routing, grounding

    return Stage(name="ground", run=run, output_schema=GroundingResult)


def make_rewrite_stage(client: Any, ticket: str) -> Stage:
    """Stage 4 — REWRITE. Chapter 1's error_rewriter prompt, verbatim.

    Now given the retrieved policy chunk in addition to the ticket and the
    classification, so the customer-facing explanation cites the actual
    refund policy instead of the model inventing plausible-sounding policy
    language.
    """

    def run(state: tuple[TicketClassification, RoutingDecision, GroundingResult]) -> str:
        classification, routing, grounding = state
        raw_input = (
            f"Ticket: {ticket}\n\n"
            f"Internal classification: category={classification.category}, "
            f"urgency={classification.urgency}, reason={classification.reason}\n"
            f"Routing: {'escalated to a human' if routing.escalate else 'handled automatically'}\n\n"
            f"Retrieved policy (source: {grounding.chunk_label}):\n"
            f"{grounding.chunk_text}"
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


def make_log_summary_stage(
    client: Any,
    ticket: str,
    classification: TicketClassification,
    routing: RoutingDecision,
    grounding: GroundingResult,
) -> Stage:
    """Stage 5 — LOG SUMMARY. Chapter 1's summarizer prompt, verbatim."""

    def run(rewritten_response: str) -> str:
        synthesized = (
            f"Support ticket handling record.\n\n"
            f"Original ticket: {ticket}\n\n"
            f"Classification: category={classification.category}, "
            f"urgency={classification.urgency}. Reason: {classification.reason}\n\n"
            f"Routing decision: "
            f"{'escalated to a human agent' if routing.escalate else 'handled automatically'} "
            f"({routing.rule_fired}).\n\n"
            f"Grounding source: {grounding.chunk_label} "
            f"(similarity={grounding.similarity:.3f})\n\n"
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

    banner("Building the corpus (shared by GROUND)")
    corpus = build_corpus()
    corpus.build(client)
    print(f"indexed {len(corpus.chunks)} chunks")

    rule()
    banner("Stage 1: CLASSIFY (Ch1 prompt, reused verbatim)")
    classify_stage = make_classify_stage(client)
    classification = classify_stage.run(ticket_text)
    print(f"category={classification.category}  urgency={classification.urgency}")
    print(f"reason: {classification.reason}")

    rule()
    banner("Stage 2: ROUTE (plain code, no model call)")
    route_stage = make_route_stage()
    routing = route_stage.run(classification)
    print("(no client call in this stage)")
    print(f"escalate={routing.escalate}  rule_fired: {routing.rule_fired}")

    rule()
    banner("Stage 3: GROUND (new this chapter - retrieval, no generation)")
    ground_stage = make_ground_stage(client, corpus, ticket_text)
    classification, routing, grounding = ground_stage.run((classification, routing))
    print("(embed_content call only - no interactions.create() in this stage)")
    print(f"retrieved: [{grounding.chunk_label}] similarity={grounding.similarity:.3f}")
    print(f"chunk text: {grounding.chunk_text}")

    rule()
    banner("Stage 4: REWRITE (Ch1 prompt, now grounded in the retrieved chunk)")
    rewrite_stage = make_rewrite_stage(client, ticket_text)
    rewritten = rewrite_stage.run((classification, routing, grounding))
    print(rewritten)

    rule()
    banner("Stage 5: LOG SUMMARY (Ch1 prompt, reused verbatim)")
    log_stage = make_log_summary_stage(
        client, ticket_text, classification, routing, grounding
    )
    log_paragraph = log_stage.run(rewritten)
    print(log_paragraph)

    banner("Final one-line log record")
    print(
        f"ticket=October-double-charge category={classification.category} "
        f"urgency={classification.urgency} "
        f"escalated={routing.escalate} "
        f"grounded_on={grounding.chunk_label} "
        f"summary={log_paragraph[:80]!r}"
    )

    rule()
    print(
        "This pipeline retrieves and grounds a customer-facing explanation. "
        "It does not act: nothing here issues the refund. Automatically "
        "issuing it based on this output would be Blueprint 4, not this "
        "pattern."
    )


if __name__ == "__main__":
    main()
