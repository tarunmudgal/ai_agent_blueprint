"""Example — a small golden-set eval harness for the Supervisor's team.

Mirrors the series' own eval-script convention (Chapter 1's
11_eval_harness.py, Chapter 4's 06_loop_eval.py): a handful of constructed
cases, a table of pass/fail, printed at the end.

Per Part VI §6.3, this checks three things per case, using SIMULATED
Supervisor transcripts rather than live API calls (deterministic and fast
to run repeatedly, exactly like Chapter 4's own loop eval):

  1. Did the Supervisor call the RIGHT specialists for the case?
  2. Are the specialists' REAL outputs (not paraphrases) traceable in the
     final report — i.e. does the final report contain the actual
     specialist output text, verbatim, rather than a reworded summary?
  3. Does the final report avoid inventing anything the specialists
     didn't say — i.e. does it introduce a number or claim absent from
     every specialist output it was given?

Each constructed case is a small dict standing in for what a real
run_agent_loop() transcript would look like: which specialists were
called, what they returned, and what the Supervisor's final report said.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import banner

# ---------------------------------------------------------------------------
# The golden set — five constructed cases, each a simulated Supervisor run.
# ---------------------------------------------------------------------------
CASES: list[dict] = [
    {
        "name": "billing_review_correct",
        "expected_specialists": {"data_analyst_specialist", "policy_specialist",
                                  "communications_specialist"},
        "called_specialists": {"data_analyst_specialist", "policy_specialist",
                                "communications_specialist"},
        "specialist_outputs": {
            "data_analyst_specialist": "96/1842 (5.2%) on 2026-10-03, falling to 0.1% by 2026-10-05.",
            "policy_specialist": "A single-period duplicate is eligible for automatic refund per Section 4.",
        },
        "final_report": (
            "data_analyst_specialist reported: 96/1842 (5.2%) on 2026-10-03, "
            "falling to 0.1% by 2026-10-05. policy_specialist reported: A "
            "single-period duplicate is eligible for automatic refund per "
            "Section 4. Draft customer explanation attached (not sent)."
        ),
    },
    {
        "name": "billing_review_missed_policy_specialist",
        "expected_specialists": {"data_analyst_specialist", "policy_specialist",
                                  "communications_specialist"},
        "called_specialists": {"data_analyst_specialist", "communications_specialist"},
        "specialist_outputs": {
            "data_analyst_specialist": "96/1842 (5.2%) on 2026-10-03.",
        },
        "final_report": (
            "data_analyst_specialist reported: 96/1842 (5.2%) on 2026-10-03. "
            "Refunds are generally available for duplicate charges."
        ),
    },
    {
        "name": "billing_review_paraphrased_facts",
        "expected_specialists": {"data_analyst_specialist", "policy_specialist",
                                  "communications_specialist"},
        "called_specialists": {"data_analyst_specialist", "policy_specialist",
                                "communications_specialist"},
        "specialist_outputs": {
            "data_analyst_specialist": "96/1842 (5.2%) on 2026-10-03, falling to 0.1% by 2026-10-05.",
            "policy_specialist": "A single-period duplicate is eligible for automatic refund per Section 4.",
        },
        "final_report": (
            "Duplicate charges spiked to roughly 3% before returning to "
            "normal. Refunds are generally available."
        ),
    },
    {
        "name": "billing_review_invented_number",
        "expected_specialists": {"data_analyst_specialist", "policy_specialist",
                                  "communications_specialist"},
        "called_specialists": {"data_analyst_specialist", "policy_specialist",
                                "communications_specialist"},
        "specialist_outputs": {
            "data_analyst_specialist": "96/1842 (5.2%) on 2026-10-03, falling to 0.1% by 2026-10-05.",
            "policy_specialist": "A single-period duplicate is eligible for automatic refund per Section 4.",
        },
        "final_report": (
            "data_analyst_specialist reported: 96/1842 (5.2%) on 2026-10-03, "
            "falling to 0.1% by 2026-10-05. policy_specialist reported: A "
            "single-period duplicate is eligible for automatic refund per "
            "Section 4. We estimate 340 customers were affected in total."
        ),
    },
    {
        "name": "ops_boardroom_minimal_case",
        "expected_specialists": {"support_specialist"},
        "called_specialists": {"support_specialist"},
        "specialist_outputs": {
            "support_specialist": "decision: escalate; reason: second consecutive month of duplicate charges.",
        },
        "final_report": (
            "support_specialist reported: decision: escalate; reason: "
            "second consecutive month of duplicate charges."
        ),
    },
]

# Numbers that would be an invented fact if present in a final report
# without appearing in any specialist output for that case (used only by
# the "invented_number" case's check below — a small, explicit trap).
_KNOWN_INVENTED_MARKERS = ["340 customers"]


def check_right_specialists_called(case: dict) -> bool:
    """Did the Supervisor call exactly the specialists this case needs?"""
    return case["called_specialists"] == case["expected_specialists"]


def check_outputs_traceable(case: dict) -> bool:
    """Is each specialist's REAL output verbatim-traceable in the final report?

    A crude but honest check: every specialist output string the case
    provides must appear, verbatim, as a substring of the final report. A
    paraphrase fails this check by design — that is the whole point.
    """
    report = case["final_report"]
    if not case["specialist_outputs"]:
        return True
    return all(output in report for output in case["specialist_outputs"].values())


def check_no_invented_claims(case: dict) -> bool:
    """Does the final report avoid introducing claims no specialist made?

    A crude but honest check for this small golden set: flag any of the
    known "invented fact" markers if it appears in the final report
    without appearing in any of the specialist outputs supplied for that
    case.
    """
    report = case["final_report"]
    specialist_text = " ".join(case["specialist_outputs"].values())
    for marker in _KNOWN_INVENTED_MARKERS:
        if marker in report and marker not in specialist_text:
            return False
    return True


def run_case(case: dict) -> dict:
    """Run all three checks for one case and return a result row."""
    right_specialists = check_right_specialists_called(case)
    traceable = check_outputs_traceable(case)
    no_invention = check_no_invented_claims(case)
    passed = right_specialists and traceable and no_invention
    return {
        "name": case["name"],
        "right_specialists": right_specialists,
        "traceable": traceable,
        "no_invention": no_invention,
        "passed": passed,
    }


def main() -> None:
    """Run the golden set and print a pass/fail table."""
    banner("Team eval — golden set")

    results = [run_case(case) for case in CASES]

    header = f"{'case':38} {'specialists':11} {'traceable':10} {'no_invention':12} {'result':6}"
    print(header)
    print("-" * len(header))
    for r in results:
        def mark(v: bool) -> str:
            return "PASS" if v else "FAIL"
        print(
            f"{r['name']:38} {mark(r['right_specialists']):11} "
            f"{mark(r['traceable']):10} {mark(r['no_invention']):12} "
            f"{('PASS' if r['passed'] else 'FAIL'):6}"
        )

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    banner("Summary")
    print(f"{passed}/{total} cases passed.")
    if passed < total:
        print(
            "Failing cases show the exact failure modes this chapter names: "
            "a missed specialist dispatch, a paraphrase that breaks "
            "traceability, or a final report inventing a fact no "
            "specialist provided."
        )


if __name__ == "__main__":
    main()
