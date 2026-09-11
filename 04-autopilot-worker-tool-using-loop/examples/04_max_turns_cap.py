"""Example — The MAX_TURNS safety net.

A tool-using loop's own output decides whether it keeps going. Without a
hard ceiling, a model that never stops calling tools (a bad prompt, a
confused model, a tool that keeps returning something that looks
actionable) becomes a literal runaway-cost and runaway-time failure mode,
not a metaphor.

This script proves run_agent_loop()'s max_turns cap actually works, using
a mocked client that never produces a turn without a function_call — i.e.
a model that (for the sake of this demonstration) never considers itself
done. No real network call is made; the mock is deterministic so the
cap-hit behavior is provable without depending on live model behavior.

With max_turns=2, the loop must return {"status": "max_turns_reached", ...}
instead of looping forever.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import banner, run_agent_loop, Tool

NEVER_DONE_DECLARATION: dict[str, Any] = {
    "type": "function",
    "name": "keep_going",
    "description": "A tool that always looks like there is more work to do.",
    "parameters": {
        "type": "object",
        "properties": {
            "note": {"type": "string", "description": "Free-text progress note."},
        },
        "required": ["note"],
    },
}


def keep_going(note: str) -> dict[str, Any]:
    """A trivial tool the mock model calls on every turn, forever."""
    return {"received_note": note, "still_going": True}


class _FakeFunctionCallStep:
    """Stands in for a real Interactions API function_call step."""

    type = "function_call"

    def __init__(self, call_id: str, name: str, arguments: dict[str, Any]) -> None:
        self.id = call_id
        self.name = name
        self.arguments = arguments


class _FakeInteraction:
    """Stands in for a real Interaction — always has exactly one function_call step."""

    def __init__(self, interaction_id: str, turn: int) -> None:
        self.id = interaction_id
        self.steps = [
            _FakeFunctionCallStep(
                call_id=f"call_{turn}",
                name="keep_going",
                arguments={"note": f"turn {turn}: still working on it"},
            )
        ]
        # A model that never stops also never produces a meaningful final
        # answer — output_text is left empty on purpose, since the happy
        # path (no function_call step) is never reached in this scenario.
        self.output_text = ""


class _NeverDoneClient:
    """A minimal mock of genai.Client that always returns a function_call.

    Simulates the worst case this chapter warns about: a model that keeps
    finding a reason to call a tool, turn after turn, and would loop
    forever without a hard cap enforced by our own code, not the model's
    good behavior.
    """

    def __init__(self) -> None:
        self._turn = 0

        class _Interactions:
            def create(inner_self, **kwargs: Any) -> _FakeInteraction:
                self._turn += 1
                return _FakeInteraction(interaction_id=f"fake-{self._turn}", turn=self._turn)

        self.interactions = _Interactions()


def main() -> None:
    """Run the mocked never-done loop with a small max_turns and show the cap firing."""
    banner("MAX_TURNS safety net — mocked never-done model")

    tools = [Tool(name="keep_going", declaration=NEVER_DONE_DECLARATION, fn=keep_going)]
    client = _NeverDoneClient()

    small_cap = 2
    print(f"Running with max_turns={small_cap} against a model that never stops "
          "calling tools...\n")

    result = run_agent_loop(client, "keep working forever", tools, max_turns=small_cap)

    for step in result["transcript"]:
        fc = step["function_call"]
        print(f"turn {step['turn']}: called {fc['name']}({fc['arguments']})")

    banner("Result")
    print(f"status: {result['status']}  (expected: 'max_turns_reached')")
    assert result["status"] == "max_turns_reached", "the cap should have fired"
    print(f"turns actually taken: {len(result['transcript'])}  "
          f"(expected: {small_cap})")
    assert len(result["transcript"]) == small_cap

    print("\nThe loop halted cleanly at the cap instead of calling keep_going "
          "forever. In a real system this is the point where the run gets "
          "logged and surfaced to a human, not silently retried.")


if __name__ == "__main__":
    main()
