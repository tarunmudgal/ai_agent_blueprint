# Blueprint 2 — The Fixed Assembly Line

## A Working Knowledge Base for Sequential Pipelines

*Companion chapter to "Beyond the Chatbox: The 5 Architecture Blueprints of Modern AI"
from the newsletter **The AI Agent Blueprint**, and the direct sequel to
[Blueprint 1 — The Smart Intern](../01-smart-intern-prompt-engineering/00-index.md).*

---

## Why this chapter exists

The parent article defined the Fixed Assembly Line in one sentence:

> When one prompt cannot handle the depth of a multi-stage task, you build a rigid
> assembly line. This pattern chains distinct steps together in a strict,
> pre-determined order where the output of Step A feeds directly into Step B.

Chapter 1 ended on a promise: *"A pipeline is four Smart Interns in a trench coat, and
every one of them still needs a schema, a delimiter, and an eval set."* This chapter
cashes that in literally. Nothing here is a new kind of model call — every stage is
still a single-shot call, exactly like Blueprint 1. What's new is everything *around*
the calls: the contract at the seam between two stages, what happens when a stage
produces garbage that the next stage receives as gospel, and how you reason about the
cost and latency of a whole chain instead of one call.

**The order is fixed, and that is the entire point.** The article is explicit about
where this pattern ends:

> **Avoid when:** The software needs to dynamically evaluate intermediate outputs to
> decide its own next step.

The moment a stage's *output* decides which stage runs next, you have quietly built
Blueprint 4 (The Autopilot Worker) without meaning to. This chapter treats that
boundary as a running theme, not a footnote — see §7.1 for the honest version of this
distinction.

---

## The two pipelines we keep coming back to

### Pipeline A — The Risk Report Pipeline

Directly from the article's own example: *"taking a technical text, translating it,
summarizing it, and finally formatting its risks into a bulleted list."* Four stages,
one document — the same post-incident review memo from Chapter 1.

```
technical text  →  translate  →  summarize  →  extract risks  →  bulleted list
```

### Pipeline B — The Incident Response Pipeline

This is where Chapter 1 stops being background reading and starts being load-bearing.
Every stage below is a prompt you already have — unmodified, chained.

```
support ticket  →  classify (Ch1)  →  route (plain code, no model)  →  rewrite (Ch1)  →  log summary (Ch1)
```

Three of these four stages are Chapter 1's exact prompts. The second stage is not a
model call at all — a deterministic Python rule. Both facts matter: a pipeline is
built from whatever stages the job needs, model calls and plain code alike, and reuse
across blueprints is not a nice-to-have, it's the normal way this actually gets built.

| # | Task | Why it earns its place |
|---|---|---|
| A | **Risk Report Pipeline** | The article's own example. Tests contracts across four LLM stages. |
| B | **Incident Response Pipeline** | Reuses Ch1's three prompts. Tests mixing code stages with model stages. |

---

## How to read this

```
┌─────────────────────────────────────────────────────────────────┐
│  New to this blueprint?                                         │
│  → Part I → Part II → Part III → stop.                          │
│    That's the working core: vocabulary, what a pipeline is,     │
│    and how to build one with a real contract at every seam.     │
├─────────────────────────────────────────────────────────────────┤
│  Already comfortable, want the craft?                           │
│  → Part III → Part IV → Part VIII.                               │
│    Skim Part I's glossary card to align on vocabulary first.    │
├─────────────────────────────────────────────────────────────────┤
│  Shipping something to production?                               │
│  → Part V → Part VI → Part VII.                                  │
│    Packaging a pipeline, its cost/latency math, and the honest   │
│    line between "fixed" and "you built an agent by accident."    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Contents

- [Part I — Vocabulary of a Pipeline](./01-vocabulary.md)
- [Part II — Foundations](./02-foundations.md)
- [Part III — Core Techniques](./03-core-techniques.md)
- [Part IV — Reliability](./04-reliability.md)
- [Part V — Reusable Artifacts](./05-reusable-artifacts.md)
- [Part VI — Production Discipline](./06-production.md)
- [Part VII — Advanced](./07-advanced.md)
- [Part VIII — Practice](./08-practice.md)

---

## Before you start

This chapter assumes you already completed
[Blueprint 1's setup](../SETUP.md) — same Python
3.10+, same virtual environment, same `GEMINI_API_KEY`. **No new dependencies.** This
chapter's own [`requirements.txt`](./requirements.txt) lists the identical three
packages Chapter 1 uses, because pipelines here are plain Python functions calling the
same API — nothing about "sequencing calls" requires a new library.

If you're starting fresh at Chapter 2 without having done Chapter 1: go do
[the repo's `SETUP.md`](../SETUP.md) first. It's
five minutes, and this chapter's examples assume `GEMINI_API_KEY` is already set.

---

## The session preamble

Every code block in every file below assumes this has already run. Copy it once,
keep it at the top of whatever file or notebook you're working in. The three
fixtures are **byte-identical to Chapter 1's** — same names, same text — because
Pipeline B depends on it being the exact same ticket Chapter 1 classified.

```python
"""Session preamble — every example in this chapter assumes these names exist."""

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()
MODEL = "gemini-3.5-flash"

# ---------------------------------------------------------------------------
# Fixture 1 — the support ticket driving Pipeline B (identical to Chapter 1)
# ---------------------------------------------------------------------------
ticket_text = """Hi, I was charged twice for my October subscription. I can see two
identical GBP 49.00 charges on the same card, both dated 3 October. I have already
tried logging in to check my invoices but the billing page just spins forever.
Could someone refund the duplicate? This is the second month it has happened."""

# ---------------------------------------------------------------------------
# Fixture 2 — the technical document driving Pipeline A (identical to Chapter 1)
# ---------------------------------------------------------------------------
document_text = """Post-incident review: payment gateway degradation, 3 October.

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
```

> **Sanity check.** Run this before continuing:
>
> ```python
> print(MODEL, "|", client.models.count_tokens(model=MODEL, contents=document_text).total_tokens, "tokens in the incident memo")
> ```
>
> If that prints a model name and a number, you're ready.

---

## A note on the code

Same convention as Chapter 1: the **Interactions API** only
(`client.interactions.create`), model pinned once as `MODEL`, Python 3.10+ style
throughout (`str | None`, `list[str]`, `pathlib.Path`, no `from __future__ import
annotations` — see [Chapter 1's note on why](../01-smart-intern-prompt-engineering/00-setup.md#01-prerequisites)
if any of that looks unfamiliar). Every code block in this chapter is cumulatively
runnable: paste them in order after the preamble above, and nothing breaks.

The one addition this chapter makes: a **pipeline stage never talks to another stage
through the model.** Chaining happens in your own Python — you validate stage N's
output, then pass it as stage N+1's input. The Interactions API's own conversation
state (`previous_interaction_id`) is for continuing one conversation, not for wiring
independent stages together, and this chapter deliberately does not use it for that
purpose. §1.6 explains why this distinction matters.

---

## Supporting files

| Path | What's in it |
|---|---|
| `examples/` | Runnable `.py` for both pipelines and every technique |
| `prompts/` | Every stage's prompt as a versioned file, including Chapter 1's three reused verbatim |
| `requirements.txt` | Same three packages as Chapter 1 — nothing new |

---

## Verification status

Every API claim in this chapter follows Chapter 1's conventions, re-verified against
Google's live documentation. Nothing here introduces a new API surface — pipelines are
built from the same `client.interactions.create` calls Chapter 1 already established,
composed in plain Python.

---

*Next in the series: Blueprint 3 — The Intelligent Library (Grounded Context).*
