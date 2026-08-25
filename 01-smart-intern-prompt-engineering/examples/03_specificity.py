"""03 — Vague prompt vs specific prompt, same input.

Demonstrates:
  * how much of "prompt engineering" is just saying what you actually want
  * that specificity constrains output length and therefore output cost

What to look for in the output:
  1. The vague prompt ("make this better") gets a competent answer to a
     question you did not ask. The model has to guess the audience, and
     with no signal it defaults to a developer audience.
  2. The specific prompt names the reader, the length, the format and the
     exclusions. Nothing is left to the model's taste.
  3. Compare total_output_tokens. Vague prompts are usually the more
     expensive ones, because an unconstrained model writes long.

Run:  python3 examples/03_specificity.py
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

VAGUE = f"Make this error message better:\n\n{stack_trace}"

SPECIFIC = f"""You are writing for a first-line support agent who cannot read code and is
on a live chat with the customer right now.

Rewrite the error below as exactly three lines, each prefixed with its label:

What happened: <one sentence, plain language>
What it means: <one sentence, the customer-visible consequence>
What to say: <one sentence the agent can read aloud verbatim>

Constraints:
- No file paths, line numbers, function names or exception class names.
- Do not guess at a root cause the trace does not show.
- Maximum 30 words per line.

Error:
{stack_trace}"""


def run(client: Any, prompt: str, label: str) -> None:
    banner(label)
    interaction = client.interactions.create(
        model=MODEL,
        input=prompt,
        store=STORE_DEFAULT,
    )
    print(interaction.output_text)
    print()
    report_usage(interaction, label=label)


def main() -> None:
    client = get_client()

    run(client, VAGUE, "VAGUE prompt")
    run(client, SPECIFIC, "SPECIFIC prompt")

    banner("Takeaway")
    print(
        "Every decision you do not make, the model makes for you - and it\n"
        "makes a different one each time. Specificity is not politeness to\n"
        "the model; it is the removal of degrees of freedom. In a system\n"
        "with no retry loop, an unspecified degree of freedom is a defect\n"
        "waiting for a Tuesday."
    )


if __name__ == "__main__":
    main()
