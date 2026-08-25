"""11 — A golden-set eval harness in one file, no test framework.

A single-shot system has no runtime safety net, so the safety net has to
live at build time. This is the smallest thing that counts as one: a list
of inputs with known-correct answers, run on every prompt change.

Demonstrates:
  * a golden set of (ticket, expected_category) cases
  * structured classification so grading is exact, not fuzzy
  * a per-case pass/fail table, overall accuracy, and a confusion summary
  * a non-zero exit code when accuracy drops below a threshold, so this
    can be wired into CI

What to look for in the output:
  1. The FAIL rows. Accuracy is a headline; the failures are the content.
     Read every one and decide whether the prompt is wrong or the golden
     label is wrong. Both happen, and the second is more common than
     people admit.
  2. The confusion pairs. A classifier that confuses billing with
     account_access has a definitional problem in the prompt, not a
     capability problem in the model. That is fixable with words.
  3. Token cost of a full run. This is what a prompt change costs you to
     verify. Budget for it; run it anyway.

Honest limits of this harness:
  * Eight cases is a smoke test, not a measurement. Two hundred is a
    measurement.
  * Recommended temperature on Gemini 3 is the default 1.0, so runs are
    not bit-identical. Do not treat a single point of accuracy movement as
    signal - re-run before believing it.
  * It grades category only. Urgency is graded separately below, with a
    tolerance, because "3 vs 4" is a judgement call even between humans.

Run:  python3 examples/11_eval_harness.py
"""
import sys
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import BaseModel, Field, ValidationError  # noqa: E402

from _common import (  # noqa: E402
    CATEGORIES,
    GOLDEN_TICKETS,
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
    rule,
)

# Fail the run below this. Pick a number you would actually block a merge
# on, not an aspirational one.
PASS_THRESHOLD = 0.80

SYSTEM_INSTRUCTION = (
    "You are a support-ticket triage classifier. Choose exactly one category "
    "from: " + ", ".join(CATEGORIES) + ".\n"
    "Priority when a ticket spans several: account_access > billing > "
    "technical > feature_request > other.\n"
    "Score urgency 1-5 on customer impact, not customer tone.\n"
    "Return JSON only."
)


class Classification(BaseModel):
    category: str = Field(description="One of: " + ", ".join(CATEGORIES))
    urgency: int = Field(ge=1, le=5)


@dataclass
class CaseResult:
    index: int
    ticket: str
    expected: str
    actual: str | None
    urgency: int | None
    passed: bool
    note: str
    input_tokens: int
    output_tokens: int
    thought_tokens: int
    seconds: float


def run_case(client: Any, index: int, ticket: str, expected: str) -> CaseResult:
    """Classify one ticket and grade it against the golden label."""
    started = time.perf_counter()
    actual: str | None = None
    urgency: int | None = None
    note = ""

    interaction = client.interactions.create(
        model=MODEL,
        input=ticket,
        system_instruction=SYSTEM_INSTRUCTION,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": Classification.model_json_schema(),
        },
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
    )
    elapsed = time.perf_counter() - started

    try:
        parsed = Classification.model_validate_json(interaction.output_text)
        actual = parsed.category
        urgency = parsed.urgency
        # An off-menu category is a schema-shaped failure, not a wrong
        # answer, and it deserves its own note in the table.
        if actual not in CATEGORIES:
            note = f"off-menu category {actual!r}"
    except ValidationError as exc:
        note = f"invalid JSON ({exc.error_count()} err)"

    usage = getattr(interaction, "usage", None)
    return CaseResult(
        index=index,
        ticket=ticket,
        expected=expected,
        actual=actual,
        urgency=urgency,
        passed=(actual == expected),
        note=note,
        input_tokens=getattr(usage, "total_input_tokens", 0) or 0,
        output_tokens=getattr(usage, "total_output_tokens", 0) or 0,
        thought_tokens=getattr(usage, "total_thought_tokens", 0) or 0,
        seconds=elapsed,
    )


def print_table(results: list[CaseResult]) -> None:
    """Per-case pass/fail, one line each."""
    header = (f"{'#':<3}{'':<6}{'expected':<17}{'actual':<17}"
              f"{'urg':<5}{'note'}")
    print(header)
    print("-" * 74)
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        actual = r.actual if r.actual is not None else "-"
        urgency = str(r.urgency) if r.urgency is not None else "-"
        print(f"{r.index:<3}{mark:<6}{r.expected:<17}{actual:<17}"
              f"{urgency:<5}{r.note}")


def print_failures(results: list[CaseResult]) -> None:
    """The failures in full, because the summary is not the point."""
    failures = [r for r in results if not r.passed]
    if not failures:
        print("no failures")
        return
    for r in failures:
        rule()
        print(f"case {r.index}: expected {r.expected}, got {r.actual}")
        print(f"  ticket: {r.ticket}")
        print("  ask yourself: is the PROMPT wrong, or is the LABEL wrong?")


def print_confusion(results: list[CaseResult]) -> None:
    """Which pairs of categories the classifier cannot tell apart."""
    pairs: dict[tuple[str, str], int] = {}
    for r in results:
        if not r.passed and r.actual:
            key = (r.expected, r.actual)
            pairs[key] = pairs.get(key, 0) + 1
    if not pairs:
        print("no confusions")
        return
    for (expected, actual), count in sorted(
        pairs.items(), key=lambda kv: -kv[1]
    ):
        print(f"  {expected} -> {actual}  x{count}")
    print(
        "\nA repeated confusion pair is a definition problem. Fix it by\n"
        "writing the boundary into the system instruction, or by adding a\n"
        "few-shot example that sits exactly on it (see 04)."
    )


def main() -> None:
    client = get_client()

    banner(f"Golden-set eval: {len(GOLDEN_TICKETS)} cases against {MODEL}")

    results: list[CaseResult] = []
    for index, (ticket, expected) in enumerate(GOLDEN_TICKETS, start=1):
        result = run_case(client, index, ticket, expected)
        results.append(result)
        print(f"  ran case {index}/{len(GOLDEN_TICKETS)} "
              f"({result.seconds:.2f}s)")

    banner("Per-case results")
    print_table(results)

    passed = sum(1 for r in results if r.passed)
    accuracy = passed / len(results) if results else 0.0

    banner("Failures in detail")
    print_failures(results)

    banner("Confusion pairs")
    print_confusion(results)

    banner("Run cost")
    total_in = sum(r.input_tokens for r in results)
    total_out = sum(r.output_tokens for r in results)
    total_think = sum(r.thought_tokens for r in results)
    total_time = sum(r.seconds for r in results)
    print(f"input tokens   : {total_in}")
    print(f"output tokens  : {total_out}")
    print(f"thinking tokens: {total_think}")
    print(f"billed as output: {total_out + total_think}")
    print(f"wall clock     : {total_time:.1f}s for {len(results)} cases")

    banner("Result")
    print(f"accuracy: {passed}/{len(results)} = {accuracy:.1%}   "
          f"threshold: {PASS_THRESHOLD:.0%}")

    if accuracy < PASS_THRESHOLD:
        print("\nBELOW THRESHOLD - exiting non-zero so CI blocks the merge.")
        sys.exit(1)

    print("\nAt or above threshold.")
    print(
        "Now go add cases. Every production misclassification you ever see\n"
        "should end up in this list. That is how a golden set stops being a\n"
        "smoke test and starts being a regression suite."
    )


if __name__ == "__main__":
    main()
