# `prompts/` — prompts as versioned artefacts

Same convention as Chapters 1-2: a prompt that lives inside a Python string
literal cannot be diffed in a review, cannot be pinned to a logged response,
and cannot be edited without a code deploy. Everything in this directory is a
prompt that got promoted out of source code and into a file.

## Naming

```
<task>.<role>.md
```

- `<task>` — the pipeline stage it belongs to.
- `<role>` — `system` for the system instruction. This chapter still has no
  `user` templates; every stage's variable content (the ticket, the
  question, the retrieved chunk) is passed as plain `input`, not
  substituted into a template.

## Frontmatter convention

Identical to Chapters 1-2 — a flat YAML block between `---` fences with
`name`, `version`, `model`, `updated`, `description`. See Chapter 1's
[`prompts/README.md`](../../01-smart-intern-prompt-engineering/prompts/README.md)
for the full field-by-field rationale and the semantic-versioning rule.

## What's in this directory

### Reused verbatim from Chapters 1-2

Three files copied byte-for-byte (frontmatter included) from
`02-fixed-assembly-line-sequential-pipelines/prompts/`, themselves reused
verbatim from Chapter 1, unedited, `version` unchanged:

| File | Reused for |
|---|---|
| `ticket_classifier.system.md` | Stage 1 (CLASSIFY) of the extended Incident Response Pipeline in `examples/03_grounded_incident_pipeline.py`. |
| `error_rewriter.system.md` | Stage 4 (REWRITE), now given the ticket, the classification, AND the retrieved refund-policy chunk as its input - the prompt text itself is unchanged, only what gets fed into it grew. |
| `summarizer.system.md` | Stage 5 (LOG SUMMARY), applied to the whole five-stage run. |

That they are byte-identical is the point, not an oversight — run `diff`
against Chapter 2's (and transitively Chapter 1's) originals any time you
want to confirm none of the three has drifted.

### Nothing new to this chapter

This chapter adds no new system-prompt file, because it adds no new stage
that talks to the model in natural language. The one new stage — GROUND,
in `examples/03_grounded_incident_pipeline.py` — calls
`client.models.embed_content`, which takes plain text and a `task_type`
enum value, not a system instruction. Chunking, embedding, and cosine
similarity search are a model CALL, but not a natural-language model
INSTRUCTION in the classic system-prompt sense, so there is no
`ground.system.md` to find here — its absence is expected, mirroring
Chapter 2's own missing `route.system.md` for a plain-code stage with no
prompt at all.

The `GroundedAnswer` verification prompt used in `examples/02_ops_library_qa.py`
and `examples/04_similarity_threshold_gate.py` is Chapter 1's exact §4.1
system instruction, inlined at the call site (as Chapter 1 itself did) —
it was never promoted to its own file there, and this chapter does not
promote it here either, to keep the reuse honestly traceable to its
origin rather than duplicating it under a new name.

## How the loader consumes these

`examples/03_grounded_incident_pipeline.py` reuses Chapter 2's frontmatter
parser unchanged: split the leading `---` fenced block from the body with a
deliberately minimal flat `key: value` parser, no PyYAML dependency.

## Changing a prompt safely

Same steps as Chapters 1-2:

```
1. Edit the .md body.
2. Bump `version` and `updated` in the frontmatter, same commit.
3. python3 examples/06_retrieval_eval.py   # retrieval precision did not regress?
   python3 examples/03_grounded_incident_pipeline.py  # pipeline still runs end to end?
4. Open the PR. The diff is readable, because it is a text file.
```
