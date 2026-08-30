# `prompts/` — prompts as versioned artefacts

Same convention as Blueprint 1: a prompt that lives inside a Python string
literal cannot be diffed in a review, cannot be pinned to a logged response,
and cannot be edited without a code deploy. Everything in this directory is a
prompt that got promoted out of source code and into a file.

## Naming

```
<task>.<role>.md
```

- `<task>` — the pipeline stage it belongs to.
- `<role>` — `system` for the system instruction. This chapter has no `user`
  templates; every stage's variable content (the ticket, the document, the
  previous stage's output) is passed as plain `input`, not substituted into a
  template.

## Frontmatter convention

Identical to Chapter 1 — a flat YAML block between `---` fences with `name`,
`version`, `model`, `updated`, `description`. See Chapter 1's
[`prompts/README.md`](../../01-smart-intern-prompt-engineering/prompts/README.md)
for the full field-by-field rationale and the semantic-versioning rule
(PATCH / MINOR / MAJOR). It applies here unchanged.

## What's in this directory

### New to this chapter

Three prompts written for the Risk Report Pipeline, none of which existed in
Chapter 1:

| File | Stage |
|---|---|
| `translate.system.md` | Stage 1 — translate the source document into the target language. |
| `extract_risks.system.md` | Stage 3 — pull every risk out of the summary as structured JSON. |
| `format_bullets.system.md` | Stage 4 — render the structured risks as a final bulleted Markdown list. |

### Reused verbatim from Chapter 1

Three files copied byte-for-byte (frontmatter included) from
`01-smart-intern-prompt-engineering/prompts/`, unedited, `version` unchanged:

| File | Reused for |
|---|---|
| `ticket_classifier.system.md` | Stage 1 of the Incident Response Pipeline. |
| `error_rewriter.system.md` | Stage 3 of the Incident Response Pipeline, repurposed to turn the ticket + classification into a customer-safe explanation. |
| `summarizer.system.md` | Stage 4 of the Incident Response Pipeline, applied to the whole pipeline run instead of a single document. |

That they are byte-identical is the point, not an oversight — see
`examples/01_risk_report_pipeline.py`'s and
`examples/02_incident_response_pipeline.py`'s docstrings for why reusing a
prompt unmodified across blueprints is the normal way this gets built, not a
special case. Run `diff` against Chapter 1's originals any time you want to
confirm none of the three has drifted.

### No file for Stage 2 of the Incident Response Pipeline

The pipeline's ROUTE stage (`urgency >= 4 or category == "account_access"` →
escalate) has no prompt file, because it is not a model call. It is a plain
Python function in `examples/02_incident_response_pipeline.py`. A "stage" in
this blueprint is a unit of the pipeline, not necessarily an LLM call —
looking for a `route.system.md` here and not finding one is expected, not a
missing file.

## How the loader consumes these

`examples/06_pipeline_manifest.py` reuses Chapter 1's frontmatter parser
(`examples/10_prompt_files.py` there) unchanged: split the leading `---`
fenced block from the body with a deliberately minimal flat `key: value`
parser, no PyYAML dependency. See Chapter 1's README for why that stays a
20-line parser rather than growing a dependency.

## Changing a prompt safely

Same five steps as Chapter 1:

```
1. Edit the .md body.
2. Bump `version` and `updated` in the frontmatter, same commit.
3. python3 examples/05_pipeline_eval.py   # accuracy did not regress?
4. Open the PR. The diff is readable, because it is a text file.
```
