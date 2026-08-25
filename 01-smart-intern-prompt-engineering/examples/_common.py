"""Shared scaffolding for every example in Blueprint 1 — The Smart Intern.

Nothing in this module talks to the network at import time. It only:
  * loads a local .env so GEMINI_API_KEY is available,
  * pins the model in ONE place,
  * hands back a configured client with a human-readable error if the key
    is missing,
  * holds the three canonical fixtures used throughout the chapter -
    stack_trace, ticket_text, document_text - copied verbatim from the
    session preamble in 00-setup.md so the prose and the code cannot drift,
  * prints usage and section banners consistently.

Import it from any example:

    from _common import MODEL, get_client, stack_trace, banner, report_usage

Every example adds this directory to sys.path itself, so the scripts run
from the repository root (`python3 examples/01_hello_and_tokens.py`) as
well as from inside `examples/`.
"""

from __future__ import annotations

import os
import sys
from typing import Any, List, Tuple

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
# One constant, imported everywhere. When you want to try a different model
# you change this line and nothing else. Hard-coding the model string into
# twelve separate files is how you end up with a chapter that half-works.
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

# Single-shot work is stateless by definition: there is no next turn that
# needs the previous one. store=False opts out of server-side retention.
# It is incompatible with background=True and with previous_interaction_id,
# neither of which a Smart Intern uses.
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
# Canonical fixture 1 — the stack trace behind the error-message rewriter
# ---------------------------------------------------------------------------
# Verbatim from the session preamble in 00-setup.md §0.10. If you change one
# character here, change it there too.
stack_trace: str = """Traceback (most recent call last):
  File "/app/services/billing.py", line 214, in charge_customer
    response = gateway.submit(payload, timeout=self.timeout)
  File "/app/vendor/paygate/client.py", line 88, in submit
    raise GatewayTimeout(f"no response in {timeout}s")
paygate.errors.GatewayTimeout: no response in 30s"""

# A deliberately mangled version, used by 09_bad_input.py.
TRUNCATED_TRACE: str = 'Traceback (most recent call last):\n  File "/app/servi'


# ---------------------------------------------------------------------------
# Canonical fixture 2 — a support ticket for the classifier
# ---------------------------------------------------------------------------
# Verbatim from the session preamble in 00-setup.md §0.10. This is the single
# canonical ticket. SAMPLE_TICKETS below is a deliberately terser batch, used
# where an example needs several inputs rather than one realistic one.
ticket_text: str = """Hi, I was charged twice for my October subscription. I can see two
identical GBP 49.00 charges on the same card, both dated 3 October. I have already
tried logging in to check my invoices but the billing page just spins forever.
Could someone refund the duplicate? This is the second month it has happened."""

CATEGORIES: List[str] = [
    "billing",
    "technical",
    "account_access",
    "feature_request",
    "other",
]

SAMPLE_TICKETS: List[str] = [
    "I was charged twice for the September invoice. Please refund the duplicate.",
    "The export button spins forever and never downloads the CSV. Chrome 141, macOS.",
    "I can't log in - the password reset email never arrives. Checked spam.",
    "Any chance you could add a dark mode? My team works nights.",
    "Just wanted to say the new dashboard is lovely. No issue, no reply needed.",
]

# (ticket, expected_category) — the golden set used by 11_eval_harness.py.
GOLDEN_TICKETS: List[Tuple[str, str]] = [
    (SAMPLE_TICKETS[0], "billing"),
    (SAMPLE_TICKETS[1], "technical"),
    (SAMPLE_TICKETS[2], "account_access"),
    (SAMPLE_TICKETS[3], "feature_request"),
    (SAMPLE_TICKETS[4], "other"),
    ("My card was declined but the dashboard still says payment pending.", "billing"),
    ("SSO via Okta stopped working for the whole engineering group this morning.",
     "account_access"),
    ("API returns 500 on POST /v2/reports about one time in ten.", "technical"),
]


# ---------------------------------------------------------------------------
# Canonical fixture 3 — a short document for the summarizer
# ---------------------------------------------------------------------------
# Verbatim from the session preamble in 00-setup.md §0.10.
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
