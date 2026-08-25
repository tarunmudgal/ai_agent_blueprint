"""06 — thinking_level: the knob with the steepest price curve.

Demonstrates:
  * the same classification at minimal / low / medium / high
  * total_thought_tokens and wall-clock latency for each

What to look for in the output:
  1. The ANSWER is very likely identical at all four levels. This task is
     fact extraction; there is nothing to reason about.
  2. total_thought_tokens is not identical. It can differ by an order of
     magnitude. You are billed for every one of those tokens at the output
     rate, and you never see them - only a summary, if you asked for one.
  3. Latency tracks thinking almost linearly. On a live support console
     that difference is the whole user experience.

The general shape of the lesson: thinking_level is not a quality dial you
turn up because higher is better. It is a budget you spend on tasks that
have something to think about. Google's own guidance: minimal/low for fact
retrieval and classification, the default for comparison and creative
reasoning, high for advanced coding, maths and multi-step planning.

Note on temperature: it is deliberately absent from this file. Google
strongly recommends leaving temperature at its default of 1.0 on Gemini 3
models - lowering it can cause looping or degraded reasoning. The classic
"set temperature=0 for determinism" advice applies to the 2.5 series, not
here.

The model pinned in _common.py supports all four levels and defaults to
medium. Other models differ - some Gemini 3 Pro previews have no "minimal",
and the 2.5 series has none either. Never hard-code a model string here;
MODEL is imported so there is exactly one place to change it.

Run:  python3 examples/06_thinking_levels.py
"""
import sys
import time

from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    CATEGORIES,
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
)

LEVELS: list[str] = ["minimal", "low", "medium", "high"]

SYSTEM_INSTRUCTION = (
    "Classify the support ticket into exactly one of: "
    + ", ".join(CATEGORIES)
    + ". Reply with the category name and an urgency 1-5, nothing else."
)

# A genuine boundary case, so that if extra thinking ever helps, it has
# something to help with.
TICKET = (
    "Our finance team was locked out of the billing portal after the admin "
    "who owned the account left. We also got an invoice we can't view. "
    "Renewal is in two days."
)


def timed_call(client: Any, level: str) -> dict[str, Any]:
    """Run one classification at a given thinking_level and time it."""
    started = time.perf_counter()

    interaction = client.interactions.create(
        model=MODEL,
        input=TICKET,
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={
            "thinking_level": level,
            # Ask for summaries so we can see whether the model actually
            # used the budget. Summaries may still come back empty.
            "thinking_summaries": "auto",
        },
        store=STORE_DEFAULT,
    )

    elapsed = time.perf_counter() - started
    usage = getattr(interaction, "usage", None)

    return {
        "level": level,
        "seconds": elapsed,
        "output": interaction.output_text.strip().replace("\n", " "),
        "thought_tokens": getattr(usage, "total_thought_tokens", 0) or 0,
        "output_tokens": getattr(usage, "total_output_tokens", 0) or 0,
        "input_tokens": getattr(usage, "total_input_tokens", 0) or 0,
        "interaction": interaction,
    }


def show_thought_summary(interaction: Any) -> None:
    """Print any thought summaries the model chose to return.

    Thought steps always carry a .signature; .summary may be empty or
    absent entirely. Never index into it blindly.
    """
    steps = getattr(interaction, "steps", None) or []
    summaries = [
        getattr(step, "summary", "")
        for step in steps
        if getattr(step, "type", None) == "thought"
    ]
    summaries = [s for s in summaries if s]
    if summaries:
        print("  thought summary: " + summaries[0].strip()[:200])
    else:
        print("  thought summary: (none returned)")


def main() -> None:
    client = get_client()

    banner("Same ticket, four thinking levels")
    print(f"ticket: {TICKET}\n")

    results = []
    for level in LEVELS:
        result = timed_call(client, level)
        results.append(result)
        print(f"[{level:<7}] {result['seconds']:.2f}s  "
              f"thinking={result['thought_tokens']:<6} "
              f"output={result['output_tokens']}")
        print(f"  answer: {result['output'][:120]}")
        show_thought_summary(result["interaction"])
        print()

    banner("Side by side")
    header = f"{'level':<9}{'latency':>9}{'thinking':>10}{'output':>8}{'billed*':>9}"
    print(header)
    print("-" * len(header))
    for r in results:
        billed = r["output_tokens"] + r["thought_tokens"]
        print(f"{r['level']:<9}{r['seconds']:>8.2f}s{r['thought_tokens']:>10}"
              f"{r['output_tokens']:>8}{billed:>9}")
    print("\n* billed = output + thinking tokens, both at the output rate.")

    identical = len({r["output"] for r in results}) == 1
    banner("Takeaway")
    if identical:
        print("All four answers were IDENTICAL.")
    else:
        print("The answers differed - inspect them above before concluding "
              "the extra thinking was wasted.")
    print(
        "\nIf the answer does not change, every thinking token above the\n"
        "cheapest level that works is money and latency you set on fire.\n"
        "Measure this on YOUR task with YOUR prompt. Do not inherit a\n"
        "thinking_level from a tutorial - including this one."
    )


if __name__ == "__main__":
    main()
