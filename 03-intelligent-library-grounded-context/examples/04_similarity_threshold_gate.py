"""04 — Part IV's refusal gate: a minimum-similarity short-circuit.

Retrieval never signals "none of these chunks are actually relevant enough"
on its own - cosine similarity always returns a number, even for a
completely unrelated query. This example adds ONE explicit constant,
MIN_SIMILARITY, and refuses to call the model at all when the top retrieved
score falls below it.

Demonstrates:
  * a MIN_SIMILARITY constant used as a hard gate before generation
  * the gate triggering on the unanswerable query (no chunk in the corpus
    is really about a CEO's phone number) and short-circuiting straight to
    the NONE / "Data unavailable" path WITHOUT spending a model call
  * the same gate NOT triggering on a well-matched query, where the top
    chunk clears the threshold and generation proceeds normally

What to look for in the output:
  1. The gated case never prints a [ground] usage line for a generation
     call - the whole point is that it costs nothing beyond the embedding
     call, because the code decided the answer before asking the model.
  2. MIN_SIMILARITY here is a chosen constant, not a value Google's docs
     recommend - this sheet does not confirm a universal threshold for
     the embedding model this chapter pins as EMBED_MODEL, so treat this
     number as a starting point to tune against your own corpus and
     golden set, not a fact to trust blindly.

Run:  python3 examples/04_similarity_threshold_gate.py
"""
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    Corpus,
    banner,
    chunk_text,
    doc_api_rate_limits,
    doc_onboarding_faq,
    doc_refund_policy,
    document_text,
    get_client,
    report_usage,
    rule,
)
from pydantic import BaseModel, Field, ValidationError  # noqa: E402

# Chosen for this corpus and these example queries, not a Google-recommended
# universal value - this sheet does not confirm one for the embedding model
# this chapter pins as EMBED_MODEL. Tune it against your own golden set
# (see 06_retrieval_eval.py).
MIN_SIMILARITY: float = 0.5


class GroundedAnswer(BaseModel):
    """Chapter 1's exact §4.1 contract, reproduced unchanged."""

    supporting_quote: str = Field(
        description="Verbatim span copied from the source. If no span supports "
                    "an answer, use the exact string: NONE"
    )
    answer: str = Field(
        description="Answer derived only from supporting_quote. If "
                    "supporting_quote is NONE, use the exact string: "
                    "Data unavailable"
    )


GROUNDED_ANSWER_SYSTEM = (
    "Answer the question using ONLY the supplied source text. Copy a "
    "verbatim span into supporting_quote that proves your answer. If "
    "nothing in the source answers the question, set supporting_quote to "
    "exactly NONE and answer to exactly 'Data unavailable'. Never answer "
    "from outside knowledge."
)


def build_corpus() -> Corpus:
    chunks = []
    for doc_name, text in [
        ("document_text", document_text),
        ("doc_refund_policy", doc_refund_policy),
        ("doc_onboarding_faq", doc_onboarding_faq),
        ("doc_api_rate_limits", doc_api_rate_limits),
    ]:
        chunks.extend(chunk_text(text, doc_name))
    return Corpus(chunks)


def ground(client: Any, question: str, source_chunk_text: str) -> GroundedAnswer | None:
    raw_input = f"Source:\n{source_chunk_text}\n\nQuestion: {question}"
    interaction = client.interactions.create(
        model=MODEL,
        input=raw_input,
        system_instruction=GROUNDED_ANSWER_SYSTEM,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": GroundedAnswer.model_json_schema(),
        },
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
    )
    report_usage(interaction, label="ground")
    try:
        return GroundedAnswer.model_validate_json(interaction.output_text)
    except ValidationError:
        return None


def answer_with_gate(client: Any, corpus: Corpus, question: str) -> None:
    rule()
    print(f"question: {question}")

    chunk, score = corpus.search(client, question, k=1)[0]
    print(f"  top chunk: [{chunk.label}] score={score:.3f}  "
          f"(gate: MIN_SIMILARITY={MIN_SIMILARITY})")

    if score < MIN_SIMILARITY:
        print(
            f"  -> GATE TRIGGERED: {score:.3f} < {MIN_SIMILARITY} - "
            f"short-circuiting to NONE / 'Data unavailable' "
            f"WITHOUT calling the model"
        )
        return

    print("  -> gate cleared, calling the model")
    result = ground(client, question, chunk.text)
    if result is None:
        print("  -> off-contract response, escalate to a human")
    elif result.supporting_quote == "NONE":
        print(f"  -> NONE / {result.answer!r}")
    else:
        print(f"  -> answer: {result.answer}  (source: [{chunk.label}])")


def main() -> None:
    client = get_client()

    banner("Building the corpus")
    corpus = build_corpus()
    corpus.build(client)

    banner("The refusal gate: MIN_SIMILARITY short-circuits generation")

    print("\ncase 1: unanswerable query -> expect the gate to trigger")
    answer_with_gate(
        client, corpus, "What is the CEO's direct phone number?"
    )

    print("\ncase 2: well-matched query -> expect the gate NOT to trigger")
    answer_with_gate(
        client, corpus,
        "How many customers were charged twice in the October incident?",
    )

    rule()
    print(
        "The gate is a cost and safety control, not a correctness "
        "guarantee: a score above the threshold still needs Chapter 1's "
        "substring verification, and a score below it can still occasionally "
        "be a real match this threshold was tuned too aggressively for. "
        "See 05_wrong_chunk_demo.py for the failure mode this gate does "
        "NOT catch."
    )


if __name__ == "__main__":
    main()
