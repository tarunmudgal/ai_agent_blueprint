# Episode 4 — Packaging a Pipeline

*Part 2 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part V](../../02-fixed-assembly-line-sequential-pipelines/05-reusable-artifacts.md) and
[Part VI](../../02-fixed-assembly-line-sequential-pipelines/06-production.md).*

Once you've built two or three pipelines, a pattern falls out on its own: every one
of them is really just an ordered list of stages, each with a name, a prompt version,
and a validation rule. Once you notice that, you stop writing pipelines from scratch
and start assembling them from two small, boring building blocks.

## Stage and Pipeline

A `Stage` is a small package: a name, a `run()` function, and (optionally) the input
and output schema it enforces. A `Pipeline` is just an ordered list of `Stage`s, with
one `run()` method that threads each stage's validated output into the next stage's
input, collects the token/latency cost of each step along the way, and stops cleanly
at the first stage that can't be made to produce valid output. Neither of these is a
framework — together they're maybe forty lines of Python. That's deliberate: the
value here is discipline, not machinery.

## The pipeline manifest

Chapter 1 taught you to version a single prompt with a small frontmatter block —
name, version, model, description. A pipeline needs the same idea one level up: a
manifest that records which prompt (and which *version* of that prompt) each stage
uses. Change one stage's prompt, and the pipeline's own version has to bump too —
because the pipeline's behavior is the sum of every stage's behavior, not just the
one you touched.

## One run ID to tie it all together

Give every pipeline run a single ID the moment it starts, and stamp every stage's log
line with it. Six months from now, when someone asks "why did this specific ticket
get routed wrong," that one ID is what lets you reconstruct the entire run — every
stage's input, output, and cost — from your logs, in order, without guessing.

## Where the cost actually goes

A four-stage pipeline doesn't cost the same at every stage. In practice, one stage
almost always dominates — usually whichever one processes the longest piece of text
(a full memo, not a three-line ticket). Once you can see that in your own usage logs,
you have real options: trim what that stage receives, lower its reasoning effort if
it doesn't need deep thinking, or ask whether it needs to be its own stage at all.
None of that is guesswork once you're logging per-stage cost with a shared run ID.

## Evaluating a whole pipeline, not just each stage

Here's a trap: every stage can individually pass its own test set and the pipeline
can still get the final answer wrong, because the stages compose badly together —
stage 2's mildly-off output becomes stage 3's confidently-wrong input. The fix is two
tiers of evaluation: a small golden set *per stage* (does this one function do its
one job correctly), plus one end-to-end test that runs the whole pipeline and checks
only the final output. Passing both is what "this pipeline works" actually means.

## Hands-On Conceptual Exercise

1. Sketch a one-page manifest for your own pipeline idea: stage name, one-line
   purpose, and which of your existing prompts (if any) it reuses.
2. Guess which single stage would dominate your pipeline's cost, and why — then
   write down what you'd try first to bring that down.
3. Write one end-to-end test case for your whole pipeline (input in, expected final
   output) that could still fail even if every individual stage "looks right."

💡 Which stage in your own idea do you think will turn out to be the expensive one?

**Next:** [Episode 5 — The Line Between "Fixed" and "You Built an Agent by Accident"](./05-advanced-and-practice.md)
