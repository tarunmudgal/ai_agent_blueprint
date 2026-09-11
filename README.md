# The AI Agent Blueprint

Companion code and knowledge base for the LinkedIn newsletter **The AI Agent
Blueprint** by Tarun Mudgal.

The parent article, *Beyond the Chatbox: The 5 Architecture Blueprints of Modern AI*
(21 July 2026), defined five architectural patterns for building with LLMs, ranked
simplest to most complex. Each gets its own chapter here.

| # | Blueprint | Chapter | Status |
|---|---|---|---|
| 1 | **The Smart Intern** — Single-Shot Inquiries | [`01-smart-intern-prompt-engineering/`](./01-smart-intern-prompt-engineering/00-index.md) | Complete |
| 2 | **The Fixed Assembly Line** — Sequential Pipelines | [`02-fixed-assembly-line-sequential-pipelines/`](./02-fixed-assembly-line-sequential-pipelines/00-index.md) | Complete |
| 3 | **The Intelligent Library** — Grounded Context | [`03-intelligent-library-grounded-context/`](./03-intelligent-library-grounded-context/00-index.md) | Complete |
| 4 | **The Autopilot Worker** — The Tool-Using Loop | [`04-autopilot-worker-tool-using-loop/`](./04-autopilot-worker-tool-using-loop/00-index.md) | Complete |
| 5 | **The Connected Boardroom** — Specialist Networks | [`05-connected-boardroom-specialist-networks/`](./05-connected-boardroom-specialist-networks/00-index.md) | Complete |

## Getting started

New here? Follow **[SETUP.md](./SETUP.md)** — clone, virtual environment, install,
get an API key, verify it works. Covers macOS, Linux, and Windows, in that one file.

Already set up? Jump straight to a chapter's `00-index.md` — see "Reading a chapter"
below.

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

Python **3.10+** with the `google-genai` SDK against Gemini. Every chapter uses the
**Interactions API** (`client.interactions.create`) on `gemini-3.5-flash`.

The 3.10 floor isn't arbitrary: `google-genai` itself now requires it, and Python 3.9
reached end of life on 31 October 2025. The code also uses modern typing throughout —
`str | None` rather than `Optional[str]`, `list[str]` rather than `List[str]`, and no
`from __future__ import annotations` anywhere, since Python 3.14 makes that import's
one job (deferred annotation evaluation) the default behavior for everyone. See the
callout in [`01-smart-intern-prompt-engineering/00-setup.md`](./01-smart-intern-prompt-engineering/00-setup.md#01-prerequisites)
if any of that looks unfamiliar — it's a short, self-contained explanation.

## Reading a chapter

Start at that chapter's `00-index.md`. It has the full table of contents and three
suggested reading routes depending on whether you are new to this, sharpening the
craft, or shipping to production.

## Repository layout

```
ai_agent_blueprint/
├── SETUP.md                              <- start here if you're new
├── README.md                             <- this file
├── requirements.txt                      <- runtime deps, aggregated across chapters
├── requirements-dev.txt                  <- linting/formatting tools (contributors only)
├── pyproject.toml, .flake8               <- shared tool configuration
├── Makefile                              <- make install / format / lint / check
├── .pre-commit-config.yaml               <- optional automatic checks on git commit
├── 01-smart-intern-prompt-engineering/   <- Chapter 1 (see table above)
    ├── 00-index.md                       <- chapter table of contents, start here
    ├── 00-setup.md ... 08-practice.md    <- the chapter, section by section
    ├── The-Smart-Intern-Prompt-Engineering.md  <- the whole chapter, one file
    ├── examples/                         <- 13 runnable scripts
    ├── prompts/, skills/                 <- reusable artifacts the chapter teaches
    └── requirements.txt, .env.example    <- this chapter's own dependencies
├── 02-fixed-assembly-line-sequential-pipelines/  <- Chapter 2 (see table above)
│   ├── 00-index.md                       <- chapter table of contents, start here
│   ├── 01-vocabulary.md ... 08-practice.md     <- the chapter, section by section
│   ├── The-Fixed-Assembly-Line-Sequential-Pipelines.md  <- the whole chapter, one file
│   ├── examples/                         <- 6 runnable pipeline scripts
│   ├── prompts/                          <- new stage prompts + 3 reused verbatim from Ch1
│   └── requirements.txt, .env.example    <- this chapter's own dependencies (same 3 packages)
├── 03-intelligent-library-grounded-context/  <- Chapter 3 (see table above)
│   ├── 00-index.md                       <- chapter table of contents, start here
│   ├── 01-vocabulary.md ... 08-practice.md     <- the chapter, section by section
│   ├── The-Intelligent-Library-Grounded-Context.md  <- the whole chapter, one file
│   ├── examples/                         <- 6 runnable scripts (corpus, retrieval, pipeline, eval)
│   ├── prompts/                          <- 3 prompts reused verbatim from Ch1/Ch2
│   └── requirements.txt, .env.example    <- this chapter's own dependencies (same 3 packages)
├── 04-autopilot-worker-tool-using-loop/  <- Chapter 4 (see table above)
│   ├── 00-index.md                       <- chapter table of contents, start here
│   ├── 01-vocabulary.md ... 08-practice.md     <- the chapter, section by section
│   ├── The-Autopilot-Worker-Tool-Using-Loop.md  <- the whole chapter, one file
│   ├── examples/                         <- 6 runnable scripts (tool loop, audit guard, eval)
│   ├── prompts/                          <- system instructions + tool declarations
│   └── requirements.txt, .env.example    <- this chapter's own dependencies (same 3 packages)
├── 05-connected-boardroom-specialist-networks/  <- Chapter 5 (see table above, final chapter)
│   ├── 00-index.md                       <- chapter table of contents, start here
│   ├── 01-vocabulary.md ... 08-practice.md     <- the chapter, section by section
│   ├── The-Connected-Boardroom-Specialist-Networks.md  <- the whole chapter, one file
│   ├── examples/                         <- 6 runnable scripts (specialists, supervisor, eval)
│   ├── prompts/                          <- 4 specialist prompts + 1 supervisor prompt
│   └── requirements.txt, .env.example    <- this chapter's own dependencies (same 3 packages)
└── linkedin-editions/                    <- compact multi-episode LinkedIn versions, Parts 2-5
    ├── 02-fixed-assembly-line/, 03-intelligent-library/,
    └── 04-autopilot-worker/, 05-connected-boardroom/
```

## Development

This repo has two audiences: readers running the examples, and anyone (including
future me) editing the chapters or scripts. The commands below are for the second
group — reading a chapter only requires what its own `requirements.txt` lists, and
`SETUP.md` covers that path.

```bash
# one-time setup
python3 -m venv .venv && source .venv/bin/activate
make install    # runtime deps + black, isort, pylint, flake8, mypy, bandit, pytest

# before committing
make format     # auto-fix formatting and import order
make lint       # flake8 + pylint + mypy + bandit, read-only
make check      # both of the above — what CI should run

# optional: run the same checks automatically on every commit
make hooks
```

Tool configuration lives in `pyproject.toml` (black, isort, pylint, mypy, bandit) and
`.flake8` (flake8 doesn't read `pyproject.toml`). See `requirements-dev.txt` for what
each tool is for and why it's included.
