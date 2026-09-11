# Episode 2 — Building Your First Pipeline

*Part 2 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part II](../../02-fixed-assembly-line-sequential-pipelines/02-foundations.md).*

An assembly line is a strong metaphor, right up until you push on it. A real assembly
line can't skip a station because of what happened at the *previous* station and
still be called "fixed" — and neither can this pattern. The order of stages is
decided when you design the pipeline, not while it's running. That one sentence is
the entire architectural boundary of Blueprint 2, and we'll spend real time on it
later in the series because it's also the easiest boundary to accidentally cross.

## Best used for / Avoid when — made concrete

The parent article puts it in two lines:

> **Best used for:** Structured workflows with fixed steps, such as taking a
> technical text, translating it, summarizing it, and finally formatting its risks
> into a bulleted list.
>
> **Avoid when:** The software needs to dynamically evaluate intermediate outputs to
> decide its own next step.

Here's the test that makes that second line concrete: is the decision being made on
the *input* you already had before any model ran, or on something a *model just
produced*? "Skip translation because this document is already tagged English" is an
input-time decision — still perfectly Blueprint 2. "Ask the model to read the memo
and decide whether to run an extra escalation step" is an output-time decision — and
the moment you do that, you've quietly built Blueprint 4 (The Autopilot Worker)
without meaning to. We'll return to this exact test in Episode 5 because it's the
one people get wrong most often.

## When two stages are actually one

Not every step deserves its own stage. If "translate" and "summarize" are always
going to run together, on the same input, with no other stage between them and no
reason to inspect the intermediate translation — that might just be one well-written
Smart Intern prompt instead of two pipeline stages. Splitting a job into stages buys
you a validation gate at every seam; it also costs you a full extra round trip. Split
when you need that gate. Don't split just because it feels more "architectural."

## The anatomy of one stage

Every stage, regardless of what it does, has the same four parts:

```
[ input contract ] -> [ prompt ] -> [ output contract ] -> [ validation gate ]
```

The translate stage of our Risk Report Pipeline, for instance, takes the raw memo,
sends it through a translation-only system prompt (explicitly told: return *only*
the translated text, nothing else), and only lets its output pass the gate if it's
non-empty and doesn't contain the source language's original wording verbatim.

## The whole pipeline, end to end

By the end of this episode's full version, you have a real, runnable four-stage
pipeline: translate the memo to Spanish, summarize the translation, extract the
risks as a structured list (not prose — an actual typed object, the same
"schema first" habit from Part 1), and format that list as clean bulleted Markdown.
Four single-shot calls, four contracts, one fixed order.

```
memo -> [translate] -> [summarize] -> [extract risks: structured] -> [format bullets]
```

Nothing in that chain is new model behavior. Every box is exactly the kind of call
Part 1 already taught you to write well. What's new is the discipline connecting the
boxes.

## Hands-On Conceptual Exercise

1. Take the pipeline sketch you wrote in Episode 1's exercise.
2. For your least-defined seam, write the actual validation check you'd run before
   letting that stage's output continue — not "looks reasonable," but a concrete
   rule (length, required field, forbidden phrase, whatever fits).
3. Decide honestly: is there a pair of adjacent stages in your sketch that should
   really be merged into one prompt? Why or why not?

💡 Did merging two stages change your mind about how many stages you actually need?

**Next:** [Episode 3 — When Stages Aren't All Model Calls](./03-core-techniques.md)
