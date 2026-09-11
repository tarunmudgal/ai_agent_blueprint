# Episode 3 — When Stages Aren't All Model Calls

*Part 2 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part III](../../02-fixed-assembly-line-sequential-pipelines/03-core-techniques.md) and
[Part IV](../../02-fixed-assembly-line-sequential-pipelines/04-reliability.md).*

This is where Part 1 stops being background reading and starts being load-bearing.
Remember the ticket classifier, the error rewriter, and the summarizer we built back
then? We're reusing all three, unmodified, as stages in a real pipeline — plus one
new stage that never calls a model at all.

## The Incident Response Pipeline

A support ticket comes in. Four things need to happen, in this exact order:

```
ticket -> classify (Part 1's prompt) -> route (plain code, no model) -> rewrite (Part 1's prompt) -> log summary (Part 1's prompt)
```

**Stage 2 is not a model call.** It's a deterministic rule: if urgency is 4 or higher,
or the category is `account_access`, escalate to a human; otherwise continue. That's
it — an `if` statement, sitting in the middle of an AI pipeline, doing real work. This
is worth sitting with: a pipeline stage is a unit in *your* flow, not necessarily an
LLM call, and the moment a routing decision needs to be fast, cheap, and fully
auditable, plain code usually beats asking a model to make the same call every time.

## Reuse, not rewrite

Stage 1 (classify) is Part 1's exact classifier prompt. Stage 3 (rewrite) is Part 1's
exact error-rewriter prompt, repurposed onto a ticket instead of a stack trace. Stage
4 (log summary) is Part 1's exact summarizer prompt, applied to the whole run. None
of these needed to be rewritten to work as pipeline stages. If you wrote a good
single-shot prompt once, it doesn't stop being good just because it now runs as part
of something bigger — the only new work is the orchestration and the contracts
between stages, not the prompts themselves.

## The validation gate: halt or repair?

When stage 1 comes back with a category that isn't one of the ones you expected, you
have two honest options: retry once with the validation error appended to the
prompt ("repair"), or stop the pipeline and quarantine the ticket for a human to
look at ("halt"). Retrying forever is not a third option — it just delays the same
failure. A good rule of thumb: one bounded repair attempt, then halt. Never let a
stage guess its way past a validation failure just to keep the pipeline moving.

## Partial failure, for real this time

Here's a harder problem than a malformed response: what if the classifier returns a
perfectly *valid-shaped* answer that's simply wrong? Say it tags an angry billing
ticket as low-urgency. The schema is fine. Routing dutifully follows it. Nothing in
the pipeline itself notices anything went wrong — because nothing did, from the
pipeline's point of view. This is an honest limitation of the Fixed Assembly Line: it
can catch a malformed answer, but it has no built-in way to catch a *confidently
wrong* one. That's a real gap, not something this pattern quietly solves.

## Retrying safely — and the postmortem that's been hiding in plain sight

Remember our memo fixture from Part 1 — the one about a payment gateway retrying a
timeout without an idempotency key, and charging customers twice? That's not a random
example. It's exactly the lesson for retrying pipeline stages: retrying a stage that
only *reads* is always safe. Retrying a stage that has a side effect (sent an email,
charged a card, escalated to a human) without an idempotency key is precisely the bug
our own fixture describes. If you remember nothing else from this episode: read the
document again with that in mind.

## Hands-On Conceptual Exercise

1. Pick one stage in your own sketch and ask honestly: does it need to be a model
   call, or is it actually a deterministic rule wearing an AI costume?
2. For a stage that does need the model, decide: on a validation failure, should it
   repair once and then halt, or halt immediately? Justify it in one sentence.
3. Identify any stage in your pipeline that has a real side effect (sends something,
   charges something, writes something). Would retrying it safely need an
   idempotency key?

💡 Found a stage in your own workflow that's secretly just an `if` statement?

**Next:** [Episode 4 — Packaging a Pipeline](./04-reusable-artifacts.md)
