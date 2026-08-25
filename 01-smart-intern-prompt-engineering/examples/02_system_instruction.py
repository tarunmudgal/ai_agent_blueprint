"""02 — What a system instruction actually buys you.

Demonstrates:
  * the identical user input sent twice: once bare, once with a
    system_instruction that fixes role, audience, format and boundaries
  * the token cost of that system instruction

What to look for in the output:
  1. The bare call answers, but it picks its own audience, its own length
     and its own format. Run it twice and the shape changes. That variance
     is the thing a system instruction removes.
  2. The instructed call is shorter, addressed to the right reader, and
     structurally predictable - which is what makes it parseable
     downstream.
  3. total_input_tokens goes UP by roughly the length of the instruction.
     System instructions count as input tokens on every single call. That
     is the price of consistency, and it is almost always worth paying.

Run:  python3 examples/02_system_instruction.py
"""
import sys

from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
    report_usage,
    stack_trace,
)

USER_INPUT = f"Rewrite this error message.\n\n{stack_trace}"

SYSTEM_INSTRUCTION = """You rewrite raw application errors for first-line support agents
who cannot read code.

Rules:
- Exactly three labelled lines: What happened / What it means / What to tell the customer.
- Plain language. No file paths, no line numbers, no exception class names.
- Never speculate about a cause the trace does not show.
- If the trace is unreadable or empty, reply exactly: Data unavailable."""


def run(client: Any, system_instruction: str | None, label: str) -> None:
    """Send USER_INPUT with or without a system instruction."""
    banner(label)

    kwargs = {
        "model": MODEL,
        "input": USER_INPUT,
        "store": STORE_DEFAULT,
    }
    # Omit the parameter entirely rather than passing None, so the
    # "without" case really is the bare request.
    if system_instruction is not None:
        kwargs["system_instruction"] = system_instruction

    interaction = client.interactions.create(**kwargs)

    print(interaction.output_text)
    print()
    report_usage(interaction, label=label)


def main() -> None:
    client = get_client()

    run(client, None, "WITHOUT system instruction")
    run(client, SYSTEM_INSTRUCTION, "WITH system instruction")

    banner("Takeaway")
    print(
        "The user content says WHAT to process. The system instruction says\n"
        "WHO you are, WHO you are writing for, and WHAT SHAPE the answer\n"
        "takes. Mixing the two into one blob is the single most common\n"
        "single-shot mistake - it makes the stable part of your prompt\n"
        "impossible to version separately from the variable part."
    )


if __name__ == "__main__":
    main()
