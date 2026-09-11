"""Example — the Part III anti-pattern: a Supervisor doing a specialist's job.

Fully deterministic, no network calls required. This is a before/after text
comparison illustrating the single most important discipline rule this
chapter names: the Supervisor's only job is dispatch and assembly, never
computing a statistic, reciting policy, or drafting language itself.

"Before" (the anti-pattern): a "Supervisor" invents a duplicate-charge
percentage without ever citing BILLING_ANOMALY_ROWS — it sounds confident,
but the number is not traceable to any specialist output, because no
specialist was consulted.

"After" (the correct behavior): the Supervisor's report explicitly quotes
what data_analyst_specialist actually returned, so every number in the
final report is traceable to a real specialist call.

No client.interactions.create call is made in this script — the point is
illustrated with plain, deterministic Python and printed text, since the
anti-pattern is about DISCIPLINE (what the Supervisor is and isn't allowed
to invent), not about model behavior on a given day.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import BILLING_ANOMALY_ROWS, banner


def violating_supervisor_report() -> str:
    """What it looks like when a "Supervisor" does the analyst's job, badly.

    This text is written to look plausible — that is exactly the danger.
    It never touches BILLING_ANOMALY_ROWS. The "roughly 5%" figure below is
    invented, not computed, and does not match the real data (see
    correct_supervisor_report below).
    """
    return (
        "Duplicate charges spiked this quarter, running at roughly 5% of "
        "attempts on the worst day before settling down. Customers "
        "affected by a one-off duplicate are eligible for a refund under "
        "our standard policy.\n"
        "[ANTI-PATTERN: this '5%' figure and the exact policy condition "
        "were never computed or looked up — they were generated from the "
        "Supervisor's own general impression, not from a specialist call. "
        "BILLING_ANOMALY_ROWS was never consulted.]"
    )


def correct_supervisor_report() -> str:
    """What the same report looks like when it is traceable to a specialist.

    This mirrors what data_analyst_specialist would return in
    02_quarterly_billing_review.py: a literal report computed straight from
    BILLING_ANOMALY_ROWS, which the Supervisor then quotes rather than
    reinvents.
    """
    lines = []
    for row in BILLING_ANOMALY_ROWS:
        rate = row["duplicate_charges"] / row["total_charge_attempts"] * 100
        lines.append(
            f"  {row['date']}: {row['duplicate_charges']} of "
            f"{row['total_charge_attempts']} attempts ({rate:.1f}%)"
        )
    computed = "\n".join(lines)
    return (
        "Per data_analyst_specialist's report (quoted, not reinvented):\n"
        f"{computed}\n"
        "Per policy_specialist's grounded answer (quoted, not recited from "
        "memory): a confirmed single-period duplicate is eligible for an "
        "automatic refund; two or more consecutive cycles of duplication "
        "requires manual review instead.\n"
        "[CORRECT: every number and every policy clause above is traceable "
        "to an actual specialist call, not invented by the Supervisor.]"
    )


def main() -> None:
    """Print the before/after comparison."""
    banner("Anti-pattern — Supervisor does the analyst's job itself")
    print(violating_supervisor_report())

    banner("Correct — Supervisor cites actual specialist output")
    print(correct_supervisor_report())

    banner("The rule this demonstrates")
    print(
        "A Supervisor's final report must be traceable back to specialist "
        "outputs, not independently invented facts. If you cannot point to "
        "which specialist call produced a number or a policy claim in the "
        "final report, treat that as a bug in the Supervisor's behavior, "
        "not a stylistic choice."
    )


if __name__ == "__main__":
    main()
