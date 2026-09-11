"""Example — Part IV: handling a specialist call that raises.

A specialist call is still a network call to a model, and network calls
fail — timeouts, transient 5xxs, rate limits. This script SIMULATES that
locally (a stand-in `run` that raises on its first N calls) so the failure
handling can be demonstrated deterministically, without depending on a
real failure actually occurring against the live API.

The Supervisor's handling, demonstrated here:
  1. Retry that ONE specialist call a bounded number of times
     (MAX_SPECIALIST_RETRIES) — not the whole Supervisor loop, just the one
     failing dispatch.
  2. If it still fails after the retry budget, surface an honest gap in
     the final report — "policy_specialist could not answer" — rather than
     silently omitting the section or inventing a plausible-sounding
     answer in its place.

No client.interactions.create call is made in this script: the point is
the RETRY AND SURFACE discipline, not live model behavior, so a flaky
specialist stand-in is simulated with plain Python instead.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import Specialist, banner

MAX_SPECIALIST_RETRIES = 3


class SimulatedSpecialistError(RuntimeError):
    """Stands in for a real API error (timeout, 5xx, rate limit, etc.)."""


def call_specialist_with_retries(specialist: Specialist, specialist_input: str,
                                  max_retries: int = MAX_SPECIALIST_RETRIES) -> dict:
    """Call one specialist, retrying only that call up to max_retries times.

    Returns {"ok": True, "output": str} on success, or
    {"ok": False, "error": str} if every attempt raised. This bounded retry
    is scoped to the ONE specialist dispatch — it does not restart the
    Supervisor's whole run_agent_loop, and it does not retry forever.
    """
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            output = specialist.run(specialist_input)
            return {"ok": True, "output": output, "attempts": attempt}
        except SimulatedSpecialistError as exc:
            last_error = exc
            print(f"  attempt {attempt}/{max_retries} for "
                  f"{specialist.name} failed: {exc}")
    return {
        "ok": False,
        "error": str(last_error) if last_error else "unknown error",
        "attempts": max_retries,
    }


def make_always_failing_run(name: str):
    """A specialist stand-in that always raises — simulates a persistently
    unavailable specialist (e.g. its underlying model call keeps failing)."""
    def run(specialist_input: str) -> str:
        raise SimulatedSpecialistError(f"{name}: simulated persistent failure")
    return run


def assemble_final_report(data_result: dict, policy_result: dict) -> str:
    """Assemble a Supervisor's final report, honestly naming any gap.

    This mirrors the honest-gap rule from 03_supervisor_violation_demo.py:
    a missing specialist result is surfaced as a stated gap, never
    silently dropped and never papered over with an invented answer.
    """
    lines = ["Quarterly billing review — final report"]

    if data_result["ok"]:
        lines.append(f"Data analyst findings: {data_result['output']}")
    else:
        lines.append(
            "Data analyst findings: UNAVAILABLE — "
            f"data_analyst_specialist could not answer after "
            f"{data_result['attempts']} attempt(s) "
            f"({data_result['error']})."
        )

    if policy_result["ok"]:
        lines.append(f"Policy answer: {policy_result['output']}")
    else:
        lines.append(
            "Policy answer: UNAVAILABLE — "
            f"policy_specialist could not answer after "
            f"{policy_result['attempts']} attempt(s) "
            f"({policy_result['error']}). This is an honest gap, not a "
            "guess — no policy claim is made in its place."
        )

    return "\n".join(lines)


def main() -> None:
    """Simulate one specialist succeeding and one persistently failing."""
    banner("Simulated specialist calls")

    working_data_analyst = Specialist(
        name="data_analyst_specialist",
        system_instruction="(simulated for this demo)",
        run=lambda specialist_input: (
            "2026-10-03: 96/1842 (5.2%); 2026-10-04: 11/1790 (0.6%); "
            "2026-10-05: 2/1810 (0.1%)."
        ),
    )
    failing_policy_specialist = Specialist(
        name="policy_specialist",
        system_instruction="(simulated for this demo)",
        run=make_always_failing_run("policy_specialist"),
    )

    print(f"Calling {working_data_analyst.name} (will succeed)...")
    data_result = call_specialist_with_retries(working_data_analyst, "get the facts")

    print(f"Calling {failing_policy_specialist.name} "
          f"(will fail every attempt, up to {MAX_SPECIALIST_RETRIES})...")
    policy_result = call_specialist_with_retries(
        failing_policy_specialist, "does policy cover this?"
    )

    banner("Final report — honest about the gap")
    print(assemble_final_report(data_result, policy_result))

    banner("The rule this demonstrates")
    print(
        "Retry the ONE failing specialist call a bounded number of times. "
        "If it still fails, surface the gap by name in the final report — "
        "'policy_specialist could not answer' — rather than silently "
        "dropping that section or inventing a plausible-sounding policy "
        "answer to fill it."
    )


if __name__ == "__main__":
    main()
