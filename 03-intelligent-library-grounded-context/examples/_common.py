"""Shared scaffolding for every example in Blueprint 3 — The Intelligent Library.

Nothing in this module talks to the network at import time. It only:
  * loads a local .env so GEMINI_API_KEY is available,
  * pins TWO models in ONE place — MODEL for generation, EMBED_MODEL for
    embeddings — because embedding text and generating text are different
    jobs done by different models, and conflating the two is an easy,
    avoidable mistake,
  * hands back a configured client with a human-readable error if the key
    is missing,
  * holds the two canonical fixtures carried over from Chapters 1-2 -
    document_text and ticket_text - byte-identical to Chapter 2's own
    _common.py, plus this chapter's three new "library" fixtures,
  * prints usage and section banners consistently,
  * defines Stage and Pipeline, reusing Chapter 2's exact shape unchanged,
  * defines the new mechanics this chapter teaches: a Chunk dataclass, a
    blank-line chunker, a plain-Python cosine similarity function, and a
    Corpus class that ties chunking + embedding + retrieval together.

Import it from any example:

    from _common import (
        MODEL, EMBED_MODEL, get_client, ticket_text, document_text,
        doc_refund_policy, doc_onboarding_faq, doc_api_rate_limits,
        Stage, Pipeline, Chunk, Corpus, chunk_text, cosine_similarity,
    )

Every example adds this directory to sys.path itself, so the scripts run
from the repository root (`python3 examples/01_build_corpus.py`) as well as
from inside `examples/`.
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
# Model pins
# ---------------------------------------------------------------------------
# Two constants, imported everywhere. Generation and embedding are different
# jobs done by different models — pinning them as two separate names, rather
# than one, is deliberate: it makes it structurally impossible to
# accidentally pass the embedding model string to a generation call or vice
# versa without a visibly wrong variable name at the call site.
#
# MODEL is a Gemini 3 stable model. Its default thinking_level is "medium"
# and it supports minimal | low | medium | high.
#
# Honest caveat: the Interactions API "supported models" table on
# ai.google.dev does not list it, yet Google's own quickstart and thinking
# guides use exactly this pairing. The table looks stale. If you hit a
# model-not-supported error, Gemini 2.5 Flash is the documented fallback -
# change the one line below and note that the 2.5 series does NOT support
# thinking_level="minimal".
#
# These two assignments are the ONLY model strings in the whole examples/
# folder.
MODEL: str = "gemini-3.5-flash"
EMBED_MODEL: str = "gemini-embedding-001"

# Every generation call in this chapter is still a single-shot call: there
# is no "next turn" that needs keeping server-side. store=False opts out of
# server-side retention.
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
# Canonical fixture 1 — the support ticket driving Example B, the extended
# Incident Response Pipeline. Byte-identical to Chapter 2's own _common.py:
# Example B depends on it being the exact same ticket Chapter 2's pipeline
# classified and routed.
# ---------------------------------------------------------------------------
ticket_text: str = """Hi, I was charged twice for my October subscription. I can see two
identical GBP 49.00 charges on the same card, both dated 3 October. I have already
tried logging in to check my invoices but the billing page just spins forever.
Could someone refund the duplicate? This is the second month it has happened."""


# ---------------------------------------------------------------------------
# Canonical fixture 2 — the incident postmortem. Byte-identical to Chapter
# 2's own _common.py. Also the first document in this chapter's corpus.
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
# New fixtures — the other three documents in this chapter's small library.
# doc_refund_policy and document_text are the only two that can genuinely
# answer a billing/duplicate-charge question; doc_onboarding_faq and
# doc_api_rate_limits are deliberate distractors so retrieval has real work
# to do.
# ---------------------------------------------------------------------------
doc_refund_policy: str = """Refund and Duplicate Charge Policy (Billing Handbook, Section 4)

Customers charged more than once for the same billing period due to a system error
are eligible for an automatic refund of the duplicate charge, no support ticket
required, once the duplicate is confirmed in the payment ledger. Confirmed duplicate
charges are refunded within 5-7 business days to the original payment method.

If a customer reports being charged twice in two or more consecutive billing cycles,
the account must be flagged for manual review by the billing operations team before
any further automatic refund is issued, since repeat duplication usually indicates a
deeper account or integration problem rather than a one-off system error.

Refunds for any other reason (dissatisfaction, accidental purchase, downgrade
requests) fall outside this section and are handled under the standard cancellation
policy instead."""

doc_onboarding_faq: str = """New Account Onboarding — Frequently Asked Questions

Q: How do I reset my password?
A: Use the "Forgot password" link on the sign-in page. Reset emails expire after 30
minutes.

Q: Can I change my billing email address without changing my login email?
A: Yes. Billing email and login email are separate fields, set independently from
Account Settings > Billing.

Q: How long does account verification take after signup?
A: Most accounts verify within a few minutes. If verification is still pending after
24 hours, contact support with your signup email address.

Q: Can I use the same account for multiple team workspaces?
A: Yes, one login can belong to multiple workspaces, and you can switch between them
from the workspace picker in the top navigation bar."""

doc_api_rate_limits: str = """Developer Reference — API Rate Limits

All API requests are counted per project, not per individual API key. Limits are
enforced across three dimensions: requests per minute, input tokens per minute, and
requests per day. Exceeding any one of the three dimensions returns an HTTP 429 with
a Retry-After header.

Rate limit tier is determined by billing status: free-tier projects share the lowest
limits; projects with billing enabled and a verified payment method move to a higher
tier automatically within a few minutes of enabling billing.

Rate limit errors are not billed. A request that fails with a 429 before the model
processes it does not count toward token usage for that billing period."""


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
# Pipeline orchestration — reused unchanged from Chapter 2. Same shape: a
# Stage is a named unit of work (model call or plain code, either is fine),
# and a Pipeline threads stage N's output into stage N+1's input, in a fixed
# order decided before the pipeline ever runs.
# ---------------------------------------------------------------------------
@dataclass
class Stage:
    """One stage of a fixed pipeline.

    `run` is any callable that takes the previous stage's output (or the
    pipeline's initial input, for stage one) and returns this stage's
    output. It may or may not call the model - this chapter's own ROUTE
    stage (reused from Chapter 2) is the running example of one that never
    does, and the new GROUND stage is the running example of one that calls
    embed_content instead of interactions.create.

    `input_schema` / `output_schema` are optional Pydantic model classes,
    recorded for documentation purposes only. Pipeline itself does not
    enforce them; each stage's own `run` is responsible for validating its
    own output.
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
    the "strict, pre-determined order" Chapter 2 described: the sequence of
    stages never changes based on what a stage produces mid-run.
    """

    stages: list[Stage] = field(default_factory=list)

    def run(self, initial_input: Any) -> Any:
        """Run every stage in order, returning the final stage's output.

        Raises RuntimeError, chained from the original exception, naming
        the stage that failed. There is no retry loop here.
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


# ---------------------------------------------------------------------------
# Chunking — the new mechanics this chapter teaches. Deliberately simple:
# split on blank-line paragraph breaks. Real corpora need smarter chunking
# (semantic chunking, overlap, size limits) - that is a named production
# concern, not something this chapter builds. The point here is to teach
# the mechanics, not to ship a production chunker.
# ---------------------------------------------------------------------------
@dataclass
class Chunk:
    """One retrievable unit of the corpus.

    `doc_name` + `chunk_id` together form a stable identifier (e.g.
    "doc_refund_policy#1") used for citing a source and for grading a
    retrieval eval against a golden set. `vector` is None until
    Corpus.build() embeds it.
    """

    doc_name: str
    chunk_id: int
    text: str
    vector: list[float] | None = None

    @property
    def label(self) -> str:
        """A short, stable identifier for logging and eval grading."""
        return f"{self.doc_name}#{self.chunk_id}"


def chunk_text(text: str, doc_name: str) -> list[Chunk]:
    """Split `text` on blank-line paragraph breaks into a list of Chunks.

    A document with three paragraphs becomes three chunks, numbered from 0
    in document order. Blank lines and surrounding whitespace are stripped
    from each chunk; empty paragraphs (e.g. from doubled blank lines) are
    dropped.
    """
    paragraphs = [p.strip() for p in text.split("\n\n")]
    paragraphs = [p for p in paragraphs if p]
    return [
        Chunk(doc_name=doc_name, chunk_id=i, text=p)
        for i, p in enumerate(paragraphs)
    ]


# ---------------------------------------------------------------------------
# Similarity — plain Python, no third-party numeric library. This corpus is small enough that a
# nested loop over a list of floats is genuinely fine; a real vector store
# (or Google's own managed File Search API) is the production answer once
# the corpus stops fitting comfortably in memory.
# ---------------------------------------------------------------------------
def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors: dot(a,b) / (|a||b|).

    Returns 0.0 if either vector has zero magnitude, to avoid a
    ZeroDivisionError on a degenerate (all-zero) embedding.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Corpus — the entire "search engine" at this chapter's teaching scale: a
# plain in-memory list of Chunks, each holding its own embedding vector.
# Explicitly a stand-in for a real vector database (Pinecone, pgvector,
# Chroma, etc.) or Google's own managed File Search API
# (https://ai.google.dev/api/file-search/file-search-stores) - name the
# production alternative, do not build it.
# ---------------------------------------------------------------------------
class Corpus:
    """An in-memory, embedded collection of Chunks, searchable by cosine similarity.

    Usage:
        corpus = Corpus([*chunk_text(doc_a, "doc_a"), *chunk_text(doc_b, "doc_b")])
        corpus.build(client)                       # embeds every chunk once
        results = corpus.search(client, "a question", k=3)
    """

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks

    def build(self, client: Any) -> None:
        """Embed every chunk once with task_type=RETRIEVAL_DOCUMENT.

        Each chunk's own doc_name is passed as `title`, since Google's docs
        say this "provides better quality embeddings for retrieval." Chunks
        are batched into one embed_content call per document so that a
        four-document, dozen-chunk corpus costs a handful of API calls
        rather than one per chunk.
        """
        from google.genai import types

        by_doc: dict[str, list[Chunk]] = {}
        for chunk in self.chunks:
            by_doc.setdefault(chunk.doc_name, []).append(chunk)

        for doc_name, doc_chunks in by_doc.items():
            result = client.models.embed_content(
                model=EMBED_MODEL,
                contents=[c.text for c in doc_chunks],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    title=doc_name,
                ),
            )
            for chunk, embedding in zip(doc_chunks, result.embeddings):
                chunk.vector = embedding.values

    def search(self, client: Any, query: str, k: int = 3) -> list[tuple[Chunk, float]]:
        """Embed `query` as a RETRIEVAL_QUERY and return the top-k (chunk, score) pairs.

        Mismatching task_type between corpus and query embeddings
        measurably hurts retrieval quality per Google's own docs - this is
        the one place in the whole chapter where getting RETRIEVAL_QUERY vs.
        RETRIEVAL_DOCUMENT backwards would silently degrade every result.
        """
        from google.genai import types

        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        query_vector = result.embeddings[0].values

        scored = [
            (chunk, cosine_similarity(query_vector, chunk.vector))
            for chunk in self.chunks
            if chunk.vector is not None
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]
