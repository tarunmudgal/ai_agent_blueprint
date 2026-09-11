"""Example — The Audit Guard (Part III/IV pattern).

A tool-using loop can reach a confident-sounding final answer while having
skipped the grounding work that answer should have depended on. The model
believing it is done (no more function_call steps) is not the same claim as
"this run did the required checks first."

This script implements a deterministic auditor: given a completed
transcript (the list of {"turn", "function_call", "function_result"} dicts
run_agent_loop() returns), check whether BOTH check_customer_history and
lookup_refund_policy appear as function_call steps strictly earlier than
the final escalate_to_human/draft_customer_reply call. If either is
missing, flag the run for human review even though the model itself
considered the run finished.

Two transcripts are audited here:
  1. A hand-built transcript that SKIPS both grounding calls and jumps
     straight to draft_customer_reply — this MUST fail the guard, proving
     it actually catches something.
  2. A hand-built transcript that does the grounding work first — this
     MUST pass, proving the guard doesn't just reject everything.

Optionally, if REPLAY_LIVE_RUN is set to True, the real Example B loop
runs on the network and audits whatever the model actually did — but the
deterministic pair above is what makes this script runnable and provable
without a live API key.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import banner

REQUIRED_GROUNDING_TOOLS: list[str] = ["check_customer_history", "lookup_refund_policy"]
GATED_FINAL_TOOLS: list[str] = ["escalate_to_human", "draft_customer_reply"]


def audit_transcript(transcript: list[dict[str, Any]]) -> dict[str, Any]:
    """Check whether required grounding tools ran before the final gated action.

    Returns a dict:
      {
        "passed": bool,
        "final_action": str | None,     # name of the last gated tool called, if any
        "missing_before_final": list[str],
        "reason": str,
      }

    "Before" means at an earlier turn index than the final gated call. If no
    gated tool was ever called, there is nothing to audit against — the
    guard passes vacuously (the run never took an irreversible-shaped
    action, so there is no missing-grounding risk to flag).
    """
    calls_by_turn = [
        (step["turn"], step["function_call"]["name"])
        for step in transcript
        if step.get("function_call") is not None
    ]

    gated_calls = [
        (turn, name) for turn, name in calls_by_turn if name in GATED_FINAL_TOOLS
    ]

    if not gated_calls:
        return {
            "passed": True,
            "final_action": None,
            "missing_before_final": [],
            "reason": "no gated action (escalate/draft) was called — nothing to audit.",
        }

    final_turn, final_action = gated_calls[-1]

    seen_before_final = {
        name for turn, name in calls_by_turn if turn < final_turn
    }

    missing = [t for t in REQUIRED_GROUNDING_TOOLS if t not in seen_before_final]

    if missing:
        return {
            "passed": False,
            "final_action": final_action,
            "missing_before_final": missing,
            "reason": (
                f"{final_action!r} was called at turn {final_turn}, but "
                f"{missing} never ran first — flagging for human review "
                "even though the model considered the run finished."
            ),
        }

    return {
        "passed": True,
        "final_action": final_action,
        "missing_before_final": [],
        "reason": (
            f"{final_action!r} was called at turn {final_turn}, after both "
            "required grounding tools already ran."
        ),
    }


def build_transcript_missing_grounding() -> list[dict[str, Any]]:
    """A hand-built transcript that jumps straight to a gated action.

    Skips both check_customer_history and lookup_refund_policy entirely.
    This MUST fail audit_transcript() — that failure is the proof the
    guard works, not a bug in the fixture.
    """
    return [
        {
            "turn": 1,
            "function_call": {"name": "draft_customer_reply", "arguments": {
                "explanation": "Your duplicate charge has been refunded.",
            }},
            "function_result": {"status": "draft_created"},
        },
    ]


def build_transcript_with_grounding() -> list[dict[str, Any]]:
    """A hand-built transcript that does the grounding work before escalating."""
    return [
        {
            "turn": 1,
            "function_call": {"name": "check_customer_history", "arguments": {
                "customer_id": "cust_4471",
            }},
            "function_result": {"duplicate_charges_this_year": 2, "account_standing": "good"},
        },
        {
            "turn": 2,
            "function_call": {"name": "lookup_refund_policy", "arguments": {
                "query": "duplicate charge consecutive",
            }},
            "function_result": {"matching_paragraphs": ["...manual review..."]},
        },
        {
            "turn": 3,
            "function_call": {"name": "escalate_to_human", "arguments": {
                "reason": "Second consecutive month of duplicate charges — policy requires manual review.",
            }},
            "function_result": {"status": "simulated_escalation_ok"},
        },
    ]


def main() -> None:
    """Audit both hand-built transcripts and print pass/fail for each."""
    banner("Audit Guard — transcript WITHOUT required grounding")
    bad = audit_transcript(build_transcript_missing_grounding())
    print(bad["reason"])
    print(f"passed: {bad['passed']}  (expected: False)")
    assert bad["passed"] is False, "guard should have flagged the ungrounded run"

    banner("Audit Guard — transcript WITH required grounding")
    good = audit_transcript(build_transcript_with_grounding())
    print(good["reason"])
    print(f"passed: {good['passed']}  (expected: True)")
    assert good["passed"] is True, "guard should have passed the grounded run"

    banner("Summary")
    print("Both fixtures behaved as expected: the guard catches a run that "
          "skipped its required grounding, and does not falsely flag a run "
          "that did the work first.")


if __name__ == "__main__":
    main()
