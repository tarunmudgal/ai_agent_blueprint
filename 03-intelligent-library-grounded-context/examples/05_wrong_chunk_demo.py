"""05 — Part IV's "wrong but real chunk" failure mode, made deterministic.

Chapter 1's substring-verification technique catches a HALLUCINATED quote:
if supporting_quote is not found verbatim in the source, the answer is
untrusted. It does NOT catch a confidently-answered question grounded in
the wrong (but real) chunk - because the quote genuinely IS in the source
text, verbatim. Verification proves the quote is real. It does not prove
the quote is FROM THE RIGHT DOCUMENT for this question.

This script needs no network call to make the point: it manually
constructs a plausible-but-incorrect retrieval and feeds a hand-written
GroundedAnswer straight to the same verification logic used everywhere
else in this chapter, showing it PASSES verification while being
substantively wrong.

Demonstrates:
  * a question about the REFUND POLICY answered using a quote pulled from
    doc_onboarding_faq (a real chunk, wrong document)
  * that Chapter 1's exact `supporting_quote in source_chunk_text` check
    passes, because the quote is genuinely verbatim in that (wrong) chunk
  * why this means retrieval quality and answer verification are two
    SEPARATE concerns - fixing one does not fix the other

What to look for in the output:
  1. The verification step prints PASS. Read the question and the answer
     together and you can see it is wrong anyway - the check has no way to
     know that on its own.
  2. This is not a bug in the substring check; it is a structural limit of
     what a substring check can prove. It proves "not fabricated." It does
     not prove "relevant" or "correct."

Run:  python3 examples/05_wrong_chunk_demo.py    (no API key required)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import banner, doc_onboarding_faq, doc_refund_policy, rule  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402


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


def verify(result: GroundedAnswer, source_chunk_text: str) -> str:
    """Chapter 1's exact verification principle, applied to one chunk."""
    if result.supporting_quote == "NONE":
        return "UNANSWERABLE (model said NONE)"
    if result.supporting_quote not in source_chunk_text:
        return "UNTRUSTED (quote not found verbatim in source - fabricated or paraphrased)"
    return "PASS (quote is verbatim in the source chunk)"


def main() -> None:
    banner("The failure mode verification alone cannot catch")

    question = (
        "If a customer reports being charged twice, are they automatically "
        "entitled to a refund?"
    )
    print(f"question: {question}")

    rule()
    print("What SHOULD have been retrieved: doc_refund_policy's first chunk.")
    correct_chunk_preview = doc_refund_policy.split("\n\n")[0]
    print(f"  {correct_chunk_preview[:160]}...")

    rule()
    print(
        "What we are simulating retrieving instead: a real chunk from "
        "doc_onboarding_faq that happens to contain the word 'account' near "
        "billing language, plausible enough for a retrieval step to rank "
        "highly on a noisier corpus or a worse embedding."
    )
    wrong_chunk = doc_onboarding_faq.split("\n\n")[1]  # the billing-email Q&A
    print(f"  wrong chunk (doc_onboarding_faq): {wrong_chunk}")

    rule()
    print(
        "A hand-written model response that quotes the WRONG chunk "
        "verbatim, but answers the REFUND question confidently anyway:"
    )
    # This is not what a well-behaved model call would actually produce for
    # this question against this chunk - it is a deliberately constructed
    # worst case, hand-written here (no network call) to make the point
    # deterministic rather than dependent on ever reproducing this exact
    # model misbehavior on demand.
    fabricated_result = GroundedAnswer(
        supporting_quote="Billing email and login email are separate fields, "
                          "set independently from Account Settings > Billing.",
        answer="Yes, customers are automatically refunded for duplicate charges.",
    )
    print(f"  supporting_quote: {fabricated_result.supporting_quote!r}")
    print(f"  answer:           {fabricated_result.answer!r}")

    rule()
    banner("Running it through Chapter 1's exact verification check")
    verdict = verify(fabricated_result, wrong_chunk)
    print(f"verdict: {verdict}")

    rule()
    print(
        "The quote IS verbatim in the (wrong) chunk, so verification PASSES "
        "- but the answer is not actually grounded in anything about refund "
        "policy at all. The retrieval step chose the wrong document; the "
        "verification step only ever checks the ONE document it was given. "
        "Catching this requires better retrieval (a real relevance signal, "
        "a similarity gate as in 04, or a human review step) - substring "
        "verification alone structurally cannot see it."
    )


if __name__ == "__main__":
    main()
