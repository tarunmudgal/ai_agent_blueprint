"""04 — Zero-shot vs one-shot vs three-shot, and what examples cost.

Demonstrates:
  * the ticket classifier at three levels of exemplification
  * the input-token price of every example you add

What to look for in the output:
  1. Zero-shot often gets the category right but the FORMAT wrong - extra
     prose, a code fence, a capitalised label. Examples teach format at
     least as much as they teach judgement.
  2. One-shot usually locks the format. The jump from zero to one is the
     biggest single improvement you will see here.
  3. Three-shot mainly helps with the boundary cases (is a complaint about
     a missing feature "feature_request" or "other"?).
  4. Watch total_input_tokens climb. Those tokens are paid on EVERY call
     forever. Few-shot examples are a permanent tax you levy on yourself,
     so make each one earn its place - and prefer examples that
     disambiguate boundaries over examples that restate the obvious.

Run:  python3 examples/04_few_shot.py
"""
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    CATEGORIES,
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
    report_usage,
)

# The ticket we are actually classifying: deliberately a boundary case.
# It mentions a charge (billing?) but the ask is for a capability that
# does not exist (feature_request?).
TARGET_TICKET = (
    "We keep getting charged for seats that left the company months ago. "
    "There's no way to bulk-remove users, so we do it one at a time. "
    "Can you sort this out?"
)

INSTRUCTION = (
    "Classify the support ticket into exactly one category from this list: "
    + ", ".join(CATEGORIES)
    + ".\nAlso assign urgency from 1 (no rush) to 5 (business stopped).\n"
    "Answer on one line as: category=<category> urgency=<n>"
)

# Chosen to teach the boundaries, not to pad the prompt.
EXAMPLES: list[tuple[str, str]] = [
    ("My invoice shows tax at 20% but we're VAT exempt.",
     "category=billing urgency=3"),
    ("SSO login loops back to the sign-in page for everyone since 9am.",
     "category=account_access urgency=5"),
    ("It would be nice if reports could be scheduled weekly.",
     "category=feature_request urgency=1"),
]


def build_prompt(n_examples: int) -> str:
    """Assemble the prompt with the first n_examples demonstrations."""
    parts = [INSTRUCTION]
    for ticket, answer in EXAMPLES[:n_examples]:
        parts.append(f"\nTicket: {ticket}\nAnswer: {answer}")
    parts.append(f"\nTicket: {TARGET_TICKET}\nAnswer:")
    return "\n".join(parts)


def run(client: Any, n_examples: int) -> None:
    label = f"{n_examples}-shot"
    banner(f"{label.upper()}")

    prompt = build_prompt(n_examples)

    # Price the prompt before sending, so the cost of examples is visible
    # even if the call later fails.
    counted = client.models.count_tokens(model=MODEL, contents=prompt)
    print(f"prompt size before sending: {counted.total_tokens} input tokens")

    interaction = client.interactions.create(
        model=MODEL,
        input=prompt,
        store=STORE_DEFAULT,
    )
    print(f"output: {interaction.output_text.strip()}")
    report_usage(interaction, label=label)


def main() -> None:
    client = get_client()

    for n in (0, 1, 3):
        run(client, n)

    banner("Takeaway")
    print(
        "Examples are the highest-leverage and most under-measured knob in\n"
        "single-shot prompting. They are also the only prompt technique with\n"
        "a per-call price tag you can read off a meter. Add them\n"
        "deliberately, one at a time, and re-run 11_eval_harness.py to check\n"
        "each one actually bought you accuracy."
    )


if __name__ == "__main__":
    main()
