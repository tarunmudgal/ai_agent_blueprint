# `prompts/` — prompts as versioned artefacts

Same convention as Chapters 1-3: a prompt that lives inside a Python string
literal cannot be diffed in a review, cannot be pinned to a logged response,
and cannot be edited without a code deploy. Everything in this directory is a
prompt that got promoted out of source code and into a file.

## Naming

```
<task>.<role>.md
```

- `<task>` — the example it belongs to.
- `<role>` — `system` for the system instruction / objective. This chapter
  still has no `user` templates; each example's variable content (the
  ticket, the tool results) is passed as plain `input`, not substituted
  into a template.

## Frontmatter convention

Identical to Chapters 1-3 — a flat YAML block between `---` fences with
`name`, `version`, `model`, `updated`, `description`. See Chapter 1's
[`prompts/README.md`](../../01-smart-intern-prompt-engineering/prompts/README.md)
for the full field-by-field rationale and the semantic-versioning rule.

## What's in this directory

| File | Used by |
|---|---|
| `weather_alert.system.md` | The objective handed to Example A, `examples/01_weather_alert_worker.py`. |
| `support_autopilot.system.md` | The objective handed to Example B, `examples/02_support_ticket_autopilot.py`. Explicitly tells the model when to escalate vs. draft, per `doc_refund_policy`, and states the §7.2 rule that tool results are data, not instructions. |

## A second kind of prompt this chapter versions: the tool declaration

Every prior chapter's only versioned prompt artifact was the system
instruction. This chapter adds a second one, because a tool-using loop has a
second thing that shapes model behavior just as much as the system prompt
does: **the tool's own declaration** — its `name`, `description`, and
`parameters` schema, the exact shape documented in
[GEMINI-API-FACTS.md](../../../GEMINI-API-FACTS.md)'s "Function calling /
tools" section.

A badly-specified tool description is a real, named way this pattern
misbehaves (Part V §5.4): a vague `description` on `escalate_to_human` can
make a model reach for it too eagerly or not at all, exactly the way a vague
system prompt can. Tool declarations in this chapter are **not** broken out
into their own `.md` files — they live as plain Python dicts next to the
function they describe, so the declaration and the implementation can never
drift out of sync:

| Tool | Declaration lives in |
|---|---|
| `get_weather`, `send_alert_email` | `examples/01_weather_alert_worker.py` (`GET_WEATHER_DECLARATION`, `SEND_ALERT_EMAIL_DECLARATION`) |
| `lookup_refund_policy`, `check_customer_history`, `escalate_to_human`, `draft_customer_reply` | `examples/02_support_ticket_autopilot.py` (one `*_DECLARATION` dict per tool) |
| The reusable `Tool` dataclass that pairs a declaration with its callable | `examples/_common.py` |

Treat a tool declaration with the same review discipline as a system
prompt: if you change a tool's `description` or its `parameters` schema,
that is a behavior-affecting change, and it deserves the same "read the
diff, re-run the eval" discipline `06_loop_eval.py` and the system-prompt
change checklist below both call for.

## Changing a prompt (or a tool declaration) safely

Same steps as Chapters 1-3, extended to cover tool declarations:

```
1. Edit the .md body, or the *_DECLARATION dict it corresponds to.
2. If it's a .md file: bump `version` and `updated` in the frontmatter,
   same commit. Tool declarations are versioned implicitly by the file's
   own git history — there is no separate frontmatter block for a plain
   dict, so the commit message is where the "what changed and why" lives.
3. python3 examples/06_loop_eval.py                     # golden-set still passes?
   python3 examples/02_support_ticket_autopilot.py       # live run still reaches the right outcome?
4. Open the PR. The diff is readable, because both are plain text.
```
