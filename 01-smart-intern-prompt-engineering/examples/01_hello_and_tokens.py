"""01 — Your first call, and where the tokens go.

Demonstrates:
  * counting input tokens BEFORE sending (client.models.count_tokens)
  * asking the model registry for its own limits (client.models.get)
  * one Interactions API call (client.interactions.create)
  * the full usage breakdown afterwards - input, output, thinking, cached,
    tool use, total - and what each number actually means

What to look for in the output:
  1. The pre-flight count_tokens number is INPUT ONLY. Compare it with
     total_input_tokens in the usage line - they should be close, but the
     usage figure also includes the system instruction if you sent one.
  2. total_output_tokens and total_thought_tokens are separate numbers.
     Both are billed at the output rate. The thinking tokens are invisible
     in the text you get back.
  3. total_tokens is the whole request. It is the only number that maps
     directly onto your bill for this call.

Run:  python3 examples/01_hello_and_tokens.py
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
    rule,
    stack_trace,
)

PROMPT = (
    "Rewrite this error for a non-technical support agent in two sentences.\n\n"
    f"{stack_trace}"
)


def preflight(client: Any) -> None:
    """Price the request before spending anything on it."""
    banner("Pre-flight: what will this cost me?")

    counted = client.models.count_tokens(model=MODEL, contents=PROMPT)
    print(f"count_tokens says: {counted.total_tokens} input tokens")
    print(f"(rule of thumb check: {len(PROMPT)} chars / 4 "
          f"= ~{len(PROMPT) // 4} tokens)")

    # The model itself is the only trustworthy source for its limits.
    # Do not memorise a context-window number from a blog post.
    info = client.models.get(model=MODEL)
    print(f"model input_token_limit : {info.input_token_limit}")
    print(f"model output_token_limit: {info.output_token_limit}")


def first_call(client: Any) -> Any:
    """Make the call. This is the whole Interactions API surface you need."""
    banner("The call: client.interactions.create")

    interaction = client.interactions.create(
        model=MODEL,
        input=PROMPT,
        store=STORE_DEFAULT,
    )

    # output_text is the convenience accessor for the assembled answer.
    # Everything else - reasoning steps, tool calls - hangs off
    # interaction.steps, which later examples open up.
    print(interaction.output_text)
    return interaction


def explain_usage(interaction: Any) -> None:
    """Print every usage field, then say what each one is for.

    The optional fields go through getattr with a 0 default. Only
    total_input_tokens and total_output_tokens are reliably present on
    every response; reading `usage.total_thought_tokens` directly is a
    very common way to crash a script against a non-thinking response.
    """
    banner("Where the tokens went")

    usage = getattr(interaction, "usage", None)
    if usage is None:
        print("No usage object on this response - nothing to account for.")
        return

    inp = getattr(usage, "total_input_tokens", 0)
    out = getattr(usage, "total_output_tokens", 0)
    thought = getattr(usage, "total_thought_tokens", 0) or 0
    cached = getattr(usage, "total_cached_tokens", 0) or 0
    tools = getattr(usage, "total_tool_use_tokens", 0) or 0
    total = getattr(usage, "total_tokens", 0)

    print(f"  total_input_tokens     : {inp}")
    print(f"  total_output_tokens    : {out}")
    print(f"  total_thought_tokens   : {thought}")
    print(f"  total_cached_tokens    : {cached}")
    print(f"  total_tool_use_tokens  : {tools}")
    print(f"  total_tokens           : {total}")

    rule()
    print(
        "input   - everything you sent: prompt, system instruction, any\n"
        "          few-shot examples. The only number you can know in\n"
        "          advance, via count_tokens. Cheapest per token.\n"
        "output  - the visible answer, the text printed above.\n"
        "thinking- reasoning tokens the model generated and did not show\n"
        "          you. Billed at the OUTPUT rate. Controlled by\n"
        f"          thinking_level (see 06). Here: {thought}.\n"
        "cached   - input tokens served from a previous cache hit, billed\n"
        "          at a discount. Zero on a first single-shot call.\n"
        "tool use - tokens spent on tool calls and their results. Zero\n"
        "           until you give the model a tool (see 08).\n"
        "total    - the sum. This is the line that becomes your invoice."
    )

    if thought:
        rule()
        print(
            f"Billed as output: {out + thought} tokens "
            f"({out} you can read + {thought} you cannot).\n"
            "That gap is the single most commonly missed cost in a Gemini 3\n"
            "budget."
        )

    rule()
    # The same numbers via the shared helper, which is what every later
    # example uses so the accounting line looks identical everywhere.
    report_usage(interaction, label="report_usage")


def main() -> None:
    client = get_client()
    preflight(client)
    interaction = first_call(client)
    explain_usage(interaction)

    banner("Takeaway")
    print(
        "You can always know the input cost before you send. You can never\n"
        "know the output cost before you send - only cap it. That asymmetry\n"
        "drives most of the cost engineering in this chapter."
    )


if __name__ == "__main__":
    main()
