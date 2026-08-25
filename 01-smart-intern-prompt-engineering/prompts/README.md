# `prompts/` — prompts as versioned artefacts

A prompt that lives inside a Python string literal is not an artefact. You
cannot diff it in a review, you cannot tell which version produced last
Tuesday's bad output, and you cannot change it without a code deploy.

Everything in this directory is a prompt that got promoted out of source code
and into a file.

## Naming

```
<task>.<role>.md
```

- `<task>` — one of the three canonical tasks: `error_rewriter`,
  `ticket_classifier`, `summarizer`.
- `<role>` — `system` for the system instruction, `user` for the user-content
  template.

Keeping the two roles in separate files is deliberate. The system instruction
is the stable part; the user template is the variable part. They change on
completely different schedules and they belong in different review
conversations.

## Frontmatter convention

Every file opens with a YAML block between `---` fences:

```yaml
---
name: error_rewriter
version: 1.2.0
model: gemini-3.5-flash
updated: 2026-08-01
description: One sentence on what this prompt is for.
---
```

| Field | Why it exists |
|---|---|
| `name` | Stable identifier. The loader looks prompts up by filename, but logs and eval reports refer to `name`, so it survives a rename. |
| `version` | See the versioning rule below. Log this with every response you keep. |
| `model` | The model this prompt was written and evaluated against. A prompt is not model-portable — one tuned for `gemini-3.5-flash` may behave differently elsewhere. This field is documentation, not enforcement. |
| `updated` | ISO date of the last content change. Answers "is this stale?" at a glance. |
| `description` | One line, for humans skimming the directory. |

The frontmatter is metadata **about** the prompt. It is never sent to the
model — the loader strips it and returns only the body.

## The versioning rule

Semantic versioning, applied to behaviour rather than to an API surface:

- **PATCH** (`1.2.0` → `1.2.1`) — wording changes that do not alter the output
  contract. Typo fixes, clearer phrasing, a reordered sentence.
- **MINOR** (`1.2.0` → `1.3.0`) — new capability or new rule that existing
  consumers can ignore. An added boundary case, an extra content rule.
- **MAJOR** (`1.2.0` → `2.0.0`) — the output contract changed. A new field, a
  renamed category, a different format. **Anything downstream that parses this
  output must be checked.**

Two non-negotiable habits:

1. **Bump the version in the same commit as the content change.** A version
   that lags the content is worse than no version, because it lies.
2. **Re-run `examples/11_eval_harness.py` before merging any MINOR or MAJOR
   bump.** A prompt change with no eval run is a guess.

Log the `version` alongside every response you store. When someone asks why
the classifier suddenly started returning `other` for everything, the version
is how you find out in five minutes instead of five hours.

## How the loader consumes these

`examples/10_prompt_files.py` implements the loader. It:

1. Reads the `.md` file from this directory.
2. Splits the leading `---` fenced block from the body.
3. Parses that block into a `dict` — with a deliberately minimal parser that
   handles `key: value` lines only. There is no PyYAML dependency in
   `requirements.txt`, and the frontmatter here is flat by design. Add nested
   YAML and you must add the dependency too.
4. Returns a `Prompt` object with `.name`, `.version`, `.model`, `.updated`,
   `.description` and `.body`.
5. For user templates, `.render(**variables)` substitutes `{placeholder}`
   tokens and **raises** on any placeholder left unfilled.

That last point matters. Silent substitution failure is how you end up
shipping a prompt containing the literal text `{stack_trace}` to production
and wondering why the model is confused.

## Placeholders

User templates use single-brace `{name}` tokens. The current templates use:

| Template | Placeholders |
|---|---|
| `error_rewriter.user.md` | `{stack_trace}` |

System instructions contain no placeholders. If you find yourself wanting one,
that variable probably belongs in the user content instead — otherwise you are
changing the stable half of the prompt on every request, and you have lost the
reason for splitting them.

## Changing a prompt safely

```
1. Edit the .md body.
2. Bump `version` and `updated` in the frontmatter, same commit.
3. python3 examples/11_eval_harness.py     # accuracy did not regress?
4. python3 examples/12_llm_as_judge.py     # quality did not regress?
5. Open the PR. The diff is readable, because it is a text file.
```

Step 5 is the whole point.
