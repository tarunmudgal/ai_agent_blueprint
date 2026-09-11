# `prompts/` — prompts as versioned artefacts

Same convention as Chapters 1-4: a prompt that lives inside a Python string
literal cannot be diffed in a review, cannot be pinned to a logged
response, and cannot be edited without a code deploy. Everything in this
directory is a prompt that got promoted out of source code and into a
file.

## Naming

```
<agent>.<role>.md
```

- `<agent>` — the specialist or Supervisor it belongs to.
- `<role>` — `system` for the system instruction. This chapter still has
  no `user` templates; each call's variable content (a ticket, a policy
  question, another specialist's output) is passed as plain `input`, not
  substituted into a template.

## Frontmatter convention

Identical to Chapters 1-4 — a flat YAML block between `---` fences with
`name`, `version`, `model`, `updated`, `description`. See Chapter 1's
[`prompts/README.md`](../../01-smart-intern-prompt-engineering/prompts/README.md)
for the full field-by-field rationale and the semantic-versioning rule.

## Five agent prompts, not one

Every prior chapter in this series versioned a handful of prompts, usually
one per pipeline stage or per tool-using worker. This chapter has **five**
— four specialists plus one Supervisor — because that is the whole point
of the Connected Boardroom pattern: instead of one system prompt trying to
hold several conflicting personas at once, each persona gets its own file,
its own version history, and its own narrow job.

| File | Used by |
|---|---|
| `support_specialist.system.md` | Example A, `examples/01_ops_boardroom.py`. A simplified stand-in for Chapter 4's full Support Ticket Autopilot loop, invoked here as one specialist call. |
| `data_analyst_specialist.system.md` | Example B, `examples/02_quarterly_billing_review.py`. Strict, literal, numbers-only — the article's "isolated SQL analyst." |
| `policy_specialist.system.md` | Example B. Grounded-retrieval persona reusing Chapter 3's `GroundedAnswer` discipline — the article's "document researcher." |
| `communications_specialist.system.md` | Example B. Warm, empathetic, customer-facing — deliberately the opposite persona from the data analyst. |
| `supervisor.system.md` | Example B's Supervisor. Dispatch and assembly only, explicitly forbidden from doing any specialist's job itself. |

## The team manifest — which specialists a Supervisor may call

This chapter's other new idea (Part V) is the **team manifest**: the fixed,
known-in-advance list of specialists a given Supervisor is allowed to
dispatch to, expressed as nothing more exotic than the `tools=[...]` list
passed to `run_agent_loop` — each entry built by wrapping one `Specialist`
with `make_specialist_tool()` in `examples/_common.py`. Example A's
Supervisor has a team manifest of one (`support_specialist`); Example B's
has three. Adding a specialist to a Supervisor's reach means adding one
more wrapped `Tool` to that list — nothing about `run_agent_loop` itself
changes, exactly as Chapter 4's own tool allowlist worked.

## Changing a prompt safely

Same steps as Chapters 1-4:

```
1. Edit the .md body.
2. Bump `version` and `updated` in the frontmatter, same commit.
3. python3 examples/06_team_eval.py                     # golden-set still passes?
   python3 examples/02_quarterly_billing_review.py       # live run still assembles a sane report?
4. Open the PR. The diff is readable, because both are plain text.
```
