"""02 — Example A, "The Ops Library": grounded Q&A over the whole corpus.

Three questions against the built corpus:
  1. Answered clearly by document_text (the postmortem).
  2. Requires picking doc_refund_policy over document_text despite lexical
     overlap on "charged twice" - the retrieval-quality test case named
     explicitly in this chapter's context sheet.
  3. Unanswerable by the corpus at all (asking for a phone number no
     document contains).

For each question: retrieve the top-k chunks, then apply Chapter 1's exact
GroundedAnswer pattern - UNCHANGED field names, UNCHANGED verbatim-substring
verification - against the single best-scoring chunk.

Demonstrates:
  * Chapter 1's GroundedAnswer Pydantic model, reproduced faithfully
  * the verification principle applied per retrieved chunk instead of one
    whole pasted document
  * the NONE / "Data unavailable" path surviving contact with retrieval,
    not just with a single pasted document

What to look for in the output:
  1. Question 2 retrieves doc_refund_policy, not document_text, even though
     both mention "charged twice" - this is semantic similarity, not
     keyword overlap, doing its job.
  2. Question 3's top chunk still has SOME similarity score (cosine
     similarity is never exactly zero for real text), but the model still
     has to say NONE, because no chunk actually answers it. A nonzero
     score is not the same as a relevant chunk - see 04 for the gate that
     automates this decision.

Run:  python3 examples/02_ops_library_qa.py
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


class GroundedAnswer(BaseModel):
    """Chapter 1's exact §4.1 contract, reproduced unchanged, field for field."""

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

QUESTIONS: list[str] = [
    "How many customers were charged twice in the October incident?",
    "If a customer says they were charged twice, are they automatically "
    "owed a refund?",
    "What is the CEO's direct phone number?",
]


def build_corpus() -> Corpus:
    """Same four-document corpus as 01_build_corpus.py, rebuilt here so this
    script is independently runnable."""
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
    """Apply Chapter 1's GroundedAnswer pattern to one retrieved chunk."""
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
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc.error_count()} error(s)")
        return None


def answer_question(client: Any, corpus: Corpus, question: str) -> None:
    rule()
    print(f"question: {question}")

    top = corpus.search(client, question, k=3)
    best_chunk, best_score = top[0]
    print(f"  retrieved top chunk: [{best_chunk.label}] score={best_score:.3f}")
    for chunk, score in top[1:]:
        print(f"  runner-up:           [{chunk.label}] score={score:.3f}")

    result = ground(client, question, best_chunk.text)
    if result is None:
        print("  -> off-contract response, escalate to a human")
        return

    if result.supporting_quote == "NONE":
        print(f"  -> NONE / {result.answer!r} (corpus does not answer this)")
    elif result.supporting_quote not in best_chunk.text:
        # The quote was paraphrased or fabricated - treat the whole answer
        # as untrusted, exactly as Chapter 1 taught for a single pasted
        # document.
        print(
            f"  -> UNTRUSTED: supporting_quote not found verbatim in "
            f"[{best_chunk.label}] - route to a human"
        )
    else:
        print(f"  -> source: [{best_chunk.label}]")
        print(f"     quote: {result.supporting_quote!r}")
        print(f"     answer: {result.answer}")


def main() -> None:
    client = get_client()

    banner("Building the corpus")
    corpus = build_corpus()
    corpus.build(client)
    print(f"indexed {len(corpus.chunks)} chunks")

    banner("Example A — The Ops Library: three questions")
    for question in QUESTIONS:
        answer_question(client, corpus, question)

    rule()
    print(
        "Note question 2: both document_text and doc_refund_policy mention "
        "'charged twice', but only doc_refund_policy answers a policy "
        "question about entitlement to a refund. Retrieval picked the right "
        "document by meaning, not by keyword overlap."
    )


if __name__ == "__main__":
    main()
