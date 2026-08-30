"""Shared scaffolding for every example in Blueprint 2 — The Fixed Assembly Line.

Nothing in this module talks to the network at import time. It only:
  * loads a local .env so GEMINI_API_KEY is available,
  * pins the model in ONE place,
  * hands back a configured client with a human-readable error if the key
    is missing,
  * holds the two canonical fixtures that drive this chapter's two running
    pipelines - ticket_text and document_text - byte-identical to Chapter
    1's own _common.py so the prose and the code cannot drift,
  * prints usage and section banners consistently,
  * defines Stage and Pipeline, the minimal orchestration shape every
    example pipeline in this chapter is built from.

Import it from any example:

    from _common import MODEL, get_client, ticket_text, document_text, Stage, Pipeline

Every example adds this directory to sys.path itself, so the scripts run
from the repository root (`python3 examples/01_risk_report_pipeline.py`) as
well as from inside `examples/`.
"""


import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency guidance, not logic
    print(
        "Missing dependency: python-dotenv\n"
        "Run: python3 -m pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise

# Look for a .env in the current directory and every parent, so it works
# whether you launch from the repo root or from examples/.
load_dotenv()

# ---------------------------------------------------------------------------
# Model pin
# ---------------------------------------------------------------------------
# One constant, imported everywhere, exactly as in Chapter 1. A pipeline
# does not change this story - every stage still calls the same one model.
#
# The pinned model below is a Gemini 3 stable model. Its default
# thinking_level is "medium" and it supports minimal | low | medium | high.
#
# Honest caveat: the Interactions API "supported models" table on
# ai.google.dev does not list it, yet Google's own quickstart and thinking
# guides use exactly this pairing. The table looks stale. If you hit a
# model-not-supported error, Gemini 2.5 Flash is the documented fallback -
# change the one line below and note that the 2.5 series does NOT support
# thinking_level="minimal".
#
# This assignment is the ONLY model string in the whole examples/ folder.
MODEL: str = "gemini-3.5-flash"

# Every stage in every pipeline in this chapter is still a single-shot call:
# there is no "next turn" a stage needs kept server-side, because chaining
# happens in your own Python, not via previous_interaction_id. store=False
# opts out of server-side retention for all of them.
STORE_DEFAULT: bool = False


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
def get_client() -> Any:
    """Return a configured genai Client, or exit with an actionable message.

    The SDK reads GEMINI_API_KEY from the environment on its own. We check
    first only so the failure is a sentence a human can act on rather than
    an authentication stack trace 40 lines deep.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your-key-here":
        raise SystemExit(
            "\n"
            "GEMINI_API_KEY is not set (or is still the placeholder).\n"
            "\n"
            "Fix it in one of two ways:\n"
            "  1. cp .env.example .env  and paste your key into .env\n"
            "  2. export GEMINI_API_KEY='...'   (this shell only)\n"
            "\n"
            "Get a key at https://aistudio.google.com/apikey\n"
        )

    try:
        from google import genai
    except ImportError:
        raise SystemExit(
            "\n"
            "Missing dependency: google-genai\n"
            "Run: python3 -m pip install -r requirements.txt\n"
            "The Interactions API needs google-genai >= 1.55.0.\n"
        )

    # No argument needed: Client() picks up GEMINI_API_KEY itself.
    return genai.Client()


# ---------------------------------------------------------------------------
# Canonical fixture 1 — the support ticket driving the Incident Response
# Pipeline. Byte-identical to Chapter 1's own _common.py: Pipeline B depends
# on it being the exact same ticket Chapter 1 classified.
# ---------------------------------------------------------------------------
ticket_text: str = """Hi, I was charged twice for my October subscription. I can see two
identical GBP 49.00 charges on the same card, both dated 3 October. I have already
tried logging in to check my invoices but the billing page just spins forever.
Could someone refund the duplicate? This is the second month it has happened."""


# ---------------------------------------------------------------------------
# Canonical fixture 2 — the technical document driving the Risk Report
# Pipeline. Byte-identical to Chapter 1's own _common.py.
# ---------------------------------------------------------------------------
document_text: str = """Post-incident review: payment gateway degradation, 3 October.

Between 02:11 and 03:47 UTC, the billing service returned elevated errors on card
charge attempts. The upstream payment provider acknowledged a partial outage in their
authorisation tier during the same window.

Impact: 1,842 charge attempts failed. 96 customers were charged twice because our
retry logic did not check for an existing authorisation before resubmitting. No card
data was exposed.

Root cause: the retry wrapper treated a gateway timeout as a definitive failure. A
timeout is ambiguous — the charge may or may not have completed. The wrapper had no
idempotency key, so the retry created a second authorisation.

Remediation: idempotency keys on all charge submissions, shipped 9 October. Timeout
handling now reconciles against the provider before retrying. Duplicate charges were
refunded within 48 hours. Outstanding: we still have no alert on duplicate-charge rate,
tracked as BILL-2291."""


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------
def banner(title: str, width: int = 74) -> None:
    """Print a section header so long console output stays readable."""
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def rule(width: int = 74) -> None:
    """A lighter separator for sub-sections."""
    print("-" * width)


def report_usage(interaction: Any, label: str = "usage") -> None:
    """Print the token breakdown for a completed interaction.

    Field names come straight from the Interactions API usage object:
      total_input_tokens, total_output_tokens, total_thought_tokens,
      total_cached_tokens, total_tool_use_tokens, total_tokens

    Only the first two are reliably present on every response, so the
    optional ones go through getattr with a 0 default. Reading
    `usage.total_thought_tokens` directly is a very common way to crash a
    script the first time you run it against a non-thinking response.
    """
    usage = getattr(interaction, "usage", None)
    if usage is None:
        print(f"[{label}] no usage object on this response")
        return

    inp = getattr(usage, "total_input_tokens", 0)
    out = getattr(usage, "total_output_tokens", 0)
    thought = getattr(usage, "total_thought_tokens", 0) or 0
    cached = getattr(usage, "total_cached_tokens", 0) or 0
    tools = getattr(usage, "total_tool_use_tokens", 0) or 0
    total = getattr(usage, "total_tokens", 0)

    print(
        f"[{label}] input={inp}  output={out}  thinking={thought}  "
        f"cached={cached}  tools={tools}  total={total}"
    )
    # Billing reality check: you pay for thinking tokens at the output rate
    # even though you only ever see the summary.
    if thought:
        print(f"[{label}] billed as output: {out + thought} tokens "
              f"({out} visible + {thought} hidden thinking)")


def truncate(text: str, limit: int = 400) -> str:
    """Shorten text for console display without hiding that it was cut."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n... [{len(text) - limit} more characters]"


# ---------------------------------------------------------------------------
# Pipeline orchestration — the one new piece of infrastructure this chapter
# adds. Deliberately minimal: a Stage is a named unit of work (model call or
# plain code, either is fine), and a Pipeline threads stage N's output into
# stage N+1's input, in a fixed order decided before the pipeline ever runs.
# ---------------------------------------------------------------------------
@dataclass
class Stage:
    """One stage of a fixed pipeline.

    `run` is any callable that takes the previous stage's output (or the
    pipeline's initial input, for stage one) and returns this stage's
    output. It may or may not call the model - Stage 2 of the Incident
    Response Pipeline is the running example of one that never does.

    `input_schema` / `output_schema` are optional Pydantic model classes,
    recorded for documentation and manifest purposes (see
    06_pipeline_manifest.py). Pipeline itself does not enforce them; each
    stage's own `run` is responsible for validating its own output, exactly
    as Chapter 1 taught for a single call.
    """

    name: str
    run: Callable[[Any], Any]
    input_schema: type | None = None
    output_schema: type | None = None


@dataclass
class Pipeline:
    """An ordered, fixed sequence of Stages.

    `run` threads the initial input through every stage in order, stops at
    the first stage that raises, and reports which stage failed. This is
    the "strict, pre-determined order" the article describes: the sequence
    of stages never changes based on what a stage produces mid-run.
    """

    stages: list[Stage] = field(default_factory=list)

    def run(self, initial_input: Any) -> Any:
        """Run every stage in order, returning the final stage's output.

        Raises RuntimeError, chained from the original exception, naming
        the stage that failed. There is no retry loop here - see
        03_validation_gate.py for what a bounded retry on top of this
        looks like.
        """
        value = initial_input
        for stage in self.stages:
            try:
                value = stage.run(value)
            except Exception as exc:
                raise RuntimeError(
                    f"pipeline halted at stage {stage.name!r}: {exc}"
                ) from exc
        return value
