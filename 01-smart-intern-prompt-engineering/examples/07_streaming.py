"""07 — Streaming: the same total time, a tenth of the perceived wait.

Demonstrates:
  * a non-streaming call, measuring total latency
  * a streaming call, measuring TTFT (time to first token) and total
  * the Interactions API streaming event shape

What to look for in the output:
  1. Total wall-clock time is roughly the same either way. Streaming does
     not make the model faster.
  2. TTFT is dramatically lower. That is the entire point: the human stops
     staring at a spinner. Perceived latency, not actual latency.
  3. Thinking happens BEFORE the first text token. On a high thinking_level
     your TTFT includes the whole thinking phase, so streaming buys you
     much less. Streaming and heavy thinking pull in opposite directions.

Event shape (Interactions API):
    event.event_type in {interaction.created, step.start, step.delta,
                         step.stop, interaction.completed}
    event.delta.type in {text, thought_summary, thought_signature}
We read the delta payload defensively with getattr, because a stream that
crashes your renderer mid-sentence is worse than no stream at all.

Run:  python3 examples/07_streaming.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    banner,
    document_text,
    get_client,
    report_usage,
)

SYSTEM_INSTRUCTION = (
    "You summarise internal engineering memos for an executive reader. "
    "Lead with the decision or risk. Six sentences maximum."
)

PROMPT = f"Summarise this memo.\n\n{document_text}"


def non_streaming(client: Any) -> float:
    """Block until the whole answer is ready. Returns total seconds."""
    banner("NON-STREAMING")

    started = time.perf_counter()
    interaction = client.interactions.create(
        model=MODEL,
        input=PROMPT,
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
        stream=False,
    )
    total = time.perf_counter() - started

    print(interaction.output_text)
    print()
    report_usage(interaction, label="non-streaming")
    print(f"total latency: {total:.2f}s   (user saw nothing until {total:.2f}s)")
    return total


def streaming(client: Any) -> Tuple[Optional[float], float]:
    """Render tokens as they arrive. Returns (ttft, total) in seconds."""
    banner("STREAMING")

    started = time.perf_counter()
    ttft: Optional[float] = None
    final_event: Any = None

    stream = client.interactions.create(
        model=MODEL,
        input=PROMPT,
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
        stream=True,
    )

    for event in stream:
        event_type = getattr(event, "event_type", None)

        if event_type == "step.delta":
            delta = getattr(event, "delta", None)
            delta_type = getattr(delta, "type", None)

            if delta_type == "text":
                # The visible answer, one fragment at a time.
                chunk = getattr(delta, "text", "") or ""
                if chunk:
                    if ttft is None:
                        ttft = time.perf_counter() - started
                        print(f"[first token at {ttft:.2f}s]\n")
                    print(chunk, end="", flush=True)

            elif delta_type == "thought_summary":
                # Reasoning traffic, not the answer. Keep it out of the
                # user-facing pane; log it if you want it.
                pass

            elif delta_type == "thought_signature":
                # Opaque integrity token. Never render it.
                pass

        elif event_type == "interaction.completed":
            # The terminal event carries the finished interaction, which is
            # where usage lives. Streaming does not exempt you from
            # accounting.
            final_event = event

    total = time.perf_counter() - started
    print("\n")

    completed = getattr(final_event, "interaction", None) if final_event else None
    if completed is not None:
        report_usage(completed, label="streaming")

    if ttft is None:
        print("no text delta arrived - check the model and event names")
        ttft = total

    print(f"TTFT: {ttft:.2f}s    total: {total:.2f}s")
    return ttft, total


def main() -> None:
    client = get_client()

    total_blocking = non_streaming(client)
    ttft, total_stream = streaming(client)

    banner("Side by side")
    print(f"non-streaming : user waits {total_blocking:.2f}s for anything")
    print(f"streaming     : user waits {ttft:.2f}s for anything, "
          f"{total_stream:.2f}s for everything")
    if ttft > 0:
        print(f"perceived speedup: {total_blocking / ttft:.1f}x")

    banner("Takeaway")
    print(
        "Stream when a human is watching. Do not stream when a program is\n"
        "the consumer: you cannot validate a JSON schema against half an\n"
        "object, and reassembling the stream just to parse it buys you\n"
        "nothing but a more complicated failure mode."
    )


if __name__ == "__main__":
    main()
