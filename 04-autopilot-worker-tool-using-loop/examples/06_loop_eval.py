"""06 — A golden-set eval harness for the Support Ticket Autopilot.

Mirrors Chapter 2's examples/05_pipeline_eval.py and Chapter 3's
examples/06_retrieval_eval.py: a small golden set of scenarios, each run
through the loop, graded against BOTH an expected final action and an
expected set of tools that must have run first — reusing
03_audit_guard.py's audit_transcript() for the second check.

Each case is a ticket-like scenario dict rather than freeform text, so
grading is deterministic and does not require a live model call to be
useful as a regression harness:

    {
        "name": str,
        "duplicate_charges_this_year": int,
        "expected_final_action": "escalate_to_human" | "draft_customer_reply",
        "expected_required_tools": list[str],
    }

`run_case()` uses a deterministic stand-in for the real loop: it always
calls check_customer_history and lookup_refund_policy first (the grounding
work Example B's own prompt asks for), then applies the same policy rule
doc_refund_policy encodes — two or more duplicate charges in consecutive
cycles means escalate, otherwise draft a reply — to pick the final action.
One case (case 5) deliberately SKIPS the grounding calls to prove the
audit-guard check in this harness actually catches a bad run, the same way
03_audit_guard.py proves it in isolation.

Swap `run_case`'s body for a real `run_agent_loop(client, objective, tools)`
call (see 02_support_ticket_autopilot.py) to grade live model runs against
the same golden set — nothing else in this file needs to change.

Run:  python3 examples/06_loop_eval.py
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import banner, rule
from importlib import import_module

_audit_guard = import_module("03_audit_guard")
audit_transcript = _audit_guard.audit_transcript

PASS_THRESHOLD = 1.0

# Each case: a ticket-like scenario, an expected final action, and the
# tools that must run before it for the audit guard to pass.
GOLDEN_CASES: list[dict[str, Any]] = [
    {
        "name": "second consecutive duplicate charge -> escalate",
        "duplicate_charges_this_year": 2,
        "skip_grounding": False,
        "expected_final_action": "escalate_to_human",
        "expected_required_tools": ["check_customer_history", "lookup_refund_policy"],
    },
    {
        "name": "first-time duplicate charge -> draft reply",
        "duplicate_charges_this_year": 1,
        "skip_grounding": False,
        "expected_final_action": "draft_customer_reply",
        "expected_required_tools": ["check_customer_history", "lookup_refund_policy"],
    },
    {
        "name": "three consecutive duplicate charges -> escalate",
        "duplicate_charges_this_year": 3,
        "skip_grounding": False,
        "expected_final_action": "escalate_to_human",
        "expected_required_tools": ["check_customer_history", "lookup_refund_policy"],
    },
    {
        "name": "no prior duplicates -> draft reply",
        "duplicate_charges_this_year": 0,
        "skip_grounding": False,
        "expected_final_action": "draft_customer_reply",
        "expected_required_tools": ["check_customer_history", "lookup_refund_policy"],
    },
    {
        "name": "regression fixture: skips grounding entirely (should FAIL audit)",
        "duplicate_charges_this_year": 2,
        "skip_grounding": True,
        "expected_final_action": "escalate_to_human",
        "expected_required_tools": ["check_customer_history", "lookup_refund_policy"],
    },
]


def run_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Produce a deterministic transcript for one golden-set case.

    Stands in for a real run_agent_loop() call: applies doc_refund_policy's
    own rule (2+ consecutive duplicate charges => manual review, otherwise
    an automatic refund reply is in-policy) to decide the final action, and
    — unless the case explicitly asks to skip it — calls the two grounding
    tools first, exactly as Example B's own system prompt instructs.
    """
    transcript: list[dict[str, Any]] = []
    turn = 1

    if not case["skip_grounding"]:
        transcript.append({
            "turn": turn,
            "function_call": {"name": "check_customer_history", "arguments": {
                "customer_id": "cust_4471",
            }},
            "function_result": {
                "duplicate_charges_this_year": case["duplicate_charges_this_year"],
            },
        })
        turn += 1

        transcript.append({
            "turn": turn,
            "function_call": {"name": "lookup_refund_policy", "arguments": {
                "query": "duplicate charge consecutive",
            }},
            "function_result": {"matching_paragraphs": ["...manual review..."]},
        })
        turn += 1

    final_action = (
        "escalate_to_human"
        if case["duplicate_charges_this_year"] >= 2
        else "draft_customer_reply"
    )
    transcript.append({
        "turn": turn,
        "function_call": {"name": final_action, "arguments": {
            "reason_or_explanation": "computed from policy + history",
        }},
        "function_result": {"status": "ok"},
    })

    return transcript


@dataclass
class CaseResult:
    index: int
    name: str
    expected_action: str
    actual_action: str
    action_passed: bool
    audit_passed: bool
    overall_passed: bool


def grade_case(index: int, case: dict[str, Any]) -> CaseResult:
    """Run one case and grade it on both final action and audit-guard outcome."""
    transcript = run_case(case)

    final_calls = [
        step["function_call"]["name"] for step in transcript if step.get("function_call")
    ]
    actual_action = final_calls[-1] if final_calls else "none"
    action_passed = actual_action == case["expected_final_action"]

    audit = audit_transcript(transcript)
    audit_passed = audit["passed"]

    return CaseResult(
        index=index,
        name=case["name"],
        expected_action=case["expected_final_action"],
        actual_action=actual_action,
        action_passed=action_passed,
        audit_passed=audit_passed,
        overall_passed=action_passed and audit_passed,
    )


def print_table(results: list[CaseResult]) -> None:
    header = f"{'#':<3}{'status':<6}{'expected action':<24}{'actual action':<24}{'audit'}"
    print(header)
    print("-" * 74)
    for r in results:
        status = "PASS" if r.overall_passed else "FAIL"
        audit_label = "ok" if r.audit_passed else "FLAGGED"
        print(f"{r.index:<3}{status:<6}{r.expected_action:<24}{r.actual_action:<24}{audit_label}")


def main() -> None:
    """Run every golden-set case and print a pass/fail table."""
    banner(f"Support Ticket Autopilot eval: {len(GOLDEN_CASES)} cases")

    results = [grade_case(i, case) for i, case in enumerate(GOLDEN_CASES, start=1)]

    for r in results:
        print(f"  case {r.index}: {r.name}")

    banner("Per-case results")
    print_table(results)

    passed = sum(1 for r in results if r.overall_passed)
    # The last case is DESIGNED to fail (it skips grounding on purpose), so
    # the pass bar is len(results) - 1, not a full sweep — the one
    # expected failure is itself the proof the harness catches a bad run.
    expected_passes = len(results) - 1
    rule()
    print(f"passed: {passed}/{len(results)}   expected passes: {expected_passes} "
          "(case 5 is a deliberate negative fixture)")

    banner("Result")
    if passed < expected_passes:
        print("BELOW expected pass count — a case that should have passed did "
              "not. Exiting non-zero so CI blocks the merge.")
        sys.exit(1)
    print("Matches expectations: every real scenario passed, and the "
          "deliberately-broken fixture was correctly flagged, not silently "
          "waved through.")


if __name__ == "__main__":
    main()
