"""Example — the Part IV lesson: pass specialist output through VERBATIM.

Fully deterministic, no network call required. Shows one specialist
output (data_analyst_specialist's report) being handed to the next
specialist (communications_specialist) two ways:

  - VERBATIM: the exact text is passed through unchanged.
  - PARAPHRASED (bad): a "helpful" summary drops or distorts a number
    along the way.

The lesson: a Supervisor that paraphrases specialist output before handing
it to the next specialist introduces a silent, easy-to-miss failure mode —
a plausible-sounding but wrong number can propagate all the way to a
customer-facing draft. Passing outputs through verbatim is not extra
ceremony; it is the difference between a traceable pipeline and a
telephone game.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import banner


# What data_analyst_specialist actually returned (a fixed, illustrative
# stand-in for a real specialist call, so this script needs no network).
DATA_ANALYST_OUTPUT = (
    "2026-10-03: 96 of 1842 attempts (5.2%)\n"
    "2026-10-04: 11 of 1790 attempts (0.6%)\n"
    "2026-10-05: 2 of 1810 attempts (0.1%)\n"
    "Trend: fell sharply from 5.2% to 0.6% to 0.1% over three days."
)


def bad_paraphrase(verbatim: str) -> str:
    """A "helpful" paraphrase that drops a number and blurs the trend.

    This is deliberately what NOT to do: it reads fine on its own, but a
    customer-facing draft built from it would understate the peak by
    roughly half and lose the exact attempt counts entirely.
    """
    return "Duplicate charges spiked to about 3% before quickly returning to normal."


def draft_from(facts_text: str, source_label: str) -> str:
    """A tiny stand-in for communications_specialist's drafting step.

    Deterministic string-templating only — no model call — because the
    point here is about what INPUT reaches the drafting step, not about
    model behavior.
    """
    return (
        f"[Draft built from {source_label}]\n"
        "Dear customer, we identified duplicate charges affecting a small "
        f"number of accounts. Specifically: {facts_text}\n"
        "This is a DRAFT for human review — nothing here has been sent."
    )


def main() -> None:
    """Print the verbatim vs. paraphrased drafting comparison."""
    banner("data_analyst_specialist's actual output (verbatim)")
    print(DATA_ANALYST_OUTPUT)

    banner("Correct — communications_specialist drafts from the VERBATIM text")
    print(draft_from(DATA_ANALYST_OUTPUT, "verbatim data_analyst_specialist output"))

    paraphrased = bad_paraphrase(DATA_ANALYST_OUTPUT)
    banner("Anti-pattern — Supervisor paraphrases before handing off")
    print(f"Paraphrase actually passed along: {paraphrased!r}")
    print(draft_from(paraphrased, "a PARAPHRASE of data_analyst_specialist's output"))

    banner("Why this matters")
    print(
        "The paraphrase dropped the 5.2% peak (understated as 'about 3%'), "
        "dropped the exact attempt counts (1,842 / 1,790 / 1,810) entirely, "
        "and dropped the three-day trend down to '96, 11, then 2'. None of "
        "that is a hallucination in the usual sense — it is information "
        "loss introduced by an intermediate paraphrasing step that did not "
        "need to exist. Passing specialist output through VERBATIM to the "
        "next specialist removes this failure mode entirely: there is "
        "nothing for the paraphrase step to distort, because there is no "
        "paraphrase step."
    )


if __name__ == "__main__":
    main()
