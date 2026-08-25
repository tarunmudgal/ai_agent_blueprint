# Learning — Knowledge Base

Companion knowledge bases for the LinkedIn newsletter **The AI Agent Blueprint**
by Tarun Mudgal.

The parent article, *Beyond the Chatbox: The 5 Architecture Blueprints of Modern AI*
(21 July 2026), defined five architectural patterns for building with LLMs, ranked
simplest to most complex. Each gets its own chapter here.

| # | Blueprint | Chapter | Status |
|---|---|---|---|
| 1 | **The Smart Intern** — Single-Shot Inquiries | [`01-smart-intern-prompt-engineering/`](./01-smart-intern-prompt-engineering/00-index.md) | Complete |
| 2 | The Fixed Assembly Line — Sequential Pipelines | — | Planned |
| 3 | The Intelligent Library — Grounded Context | — | Planned |
| 4 | The Autopilot Worker — The Tool-Using Loop | — | Planned |
| 5 | The Connected Boardroom — Specialist Networks | — | Planned |

## The Golden Rule

From the parent article, and the organising principle for all of these:

> Always start with the simplest pattern that works. Only upgrade your complexity tier
> when your requirements absolutely force you to.

```
 [ How complex is the task? ]
 │
 ├── Simple / One-turn text? ──────> [ 1. The Smart Intern ]
 ├── Rigid Step-by-Step flow? ─────> [ 2. The Fixed Assembly Line ]
 ├── Needs private / fresh data? ──> [ 3. The Intelligent Library ]
 ├── Dynamic / Unpredictable tools? > [ 4. The Autopilot Worker ]
 └── Conflicting expert domains? ──> [ 5. The Connected Boardroom ]
```

## Stack

Python with the `google-genai` SDK against Gemini. Chapter 1 uses the
**Interactions API** on `gemini-3.5-flash` as the primary path, with legacy
`generate_content` variants alongside for continuity with earlier episodes.

## Reading a chapter

Start at that chapter's `00-index.md`. It has the full table of contents and three
suggested reading routes depending on whether you are new to this, sharpening the
craft, or shipping to production.
