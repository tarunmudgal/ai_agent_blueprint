"""08 — Grounding: forbidding the model to fill in the blanks.

This is grounding in the sense that matters for a Smart Intern: confining
the answer to the text you supplied. No tools, no retrieval, no search -
that is Blueprint 2. Here the only source of truth is the input, and the
only defence is the instruction.

Demonstrates:
  * an ungrounded prompt that actively invites invention
  * a grounded prompt that supplies an explicit escape hatch
  * both run against the SAME truncated evidence

What to look for in the output:
  1. The ungrounded answer will most likely name a cause - a network blip,
     an overloaded payment provider, a retry storm. None of that is in the
     trace. It is plausible, fluent, and unsupported.
  2. The grounded answer sticks to what the five lines actually prove, and
     says "Data unavailable" for the rest.
  3. This is the difference between a support note a customer can rely on
     and one that starts an outage postmortem down the wrong path.

The three ingredients of a grounding instruction:
  a) name the ONLY permitted source,
  b) forbid inference beyond it,
  c) give an explicit, exact string to emit when the answer is not there.
Leave out (c) and the model will still guess, because you have given it no
legal way to say nothing.

Run:  python3 examples/08_grounding.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
    report_usage,
    stack_trace,
)

# Questions the trace genuinely cannot answer. That is the test.
QUESTIONS = """1. What component failed?
2. What was the configured timeout?
3. What caused the gateway to time out?
4. How many customers were affected?
5. Has this happened before?"""

UNGROUNDED_SYSTEM = (
    "You are a senior engineer. Explain production errors clearly and "
    "helpfully to your team."
)

GROUNDED_SYSTEM = """You are a senior engineer writing an incident note.

Source of truth: the stack trace supplied in the user message. Nothing else.

Rules:
- Answer ONLY from evidence present in the trace.
- Do not infer causes, blast radius, frequency or history. The trace is five
  lines long; it does not know those things and neither do you.
- For any question the trace does not answer, reply with exactly:
  Data unavailable
- Quote the specific line of the trace that supports each answer you do give.

Answering "Data unavailable" is a correct and expected outcome, not a
failure. A confident wrong answer is the failure."""

USER_INPUT = f"""Answer these questions about the error below.

{QUESTIONS}

Trace:
{stack_trace}"""


def run(client: Any, system_instruction: Optional[str], label: str) -> None:
    banner(label)
    interaction = client.interactions.create(
        model=MODEL,
        input=USER_INPUT,
        system_instruction=system_instruction,
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
    )
    print(interaction.output_text)
    print()
    report_usage(interaction, label=label)


def main() -> None:
    client = get_client()

    run(client, UNGROUNDED_SYSTEM, "UNGROUNDED - 'be helpful'")
    run(client, GROUNDED_SYSTEM, "GROUNDED - 'answer only from the trace'")

    banner("Scoring it yourself")
    print(
        "Questions 1 and 2 ARE answerable from the trace:\n"
        "  1. the payment gateway client, via paygate.errors.GatewayTimeout\n"
        "  2. 30 seconds, from 'no response in 30s'\n"
        "Questions 3, 4 and 5 are NOT. The only correct answer to each is\n"
        "'Data unavailable'.\n"
        "\n"
        "Count how many of 3/4/5 each run invented an answer for. That count\n"
        "is your hallucination rate on this prompt, and it is the number to\n"
        "put in your eval harness."
    )


if __name__ == "__main__":
    main()
