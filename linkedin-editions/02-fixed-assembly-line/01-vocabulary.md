# Episode 1 — The Vocabulary of a Pipeline

*Part 2 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part I](../../02-fixed-assembly-line-sequential-pipelines/01-vocabulary.md).*

Last time, we drew the line at one turn: one instruction set in, one answer out. This
week we cross it — but not by making one call smarter. We make several small, boring
calls and chain them together in an order that never changes.

## The example we'll use all series

Take a post-incident review memo — the kind an on-call engineer writes after an
outage. We want to turn it into a bulleted risk report for a non-technical
stakeholder. That's four distinct jobs:

```
technical memo -> translate -> summarize -> extract risks -> bulleted list
```

Each arrow is a seam. Each box is a stage. Get comfortable with those two words —
they're the entire vocabulary of this pattern.

## Stage

A stage is one unit of work with exactly one input and one output. Here's the
detail that trips people up: **a stage doesn't have to call a model.** "Translate the
memo" is a stage. So is "check whether this ticket's urgency crossed a threshold" —
and that one might just be an `if` statement. A pipeline is built from whatever the
job needs, and reusing plain code where a model call would be overkill isn't cutting
corners, it's the normal, correct way to build one.

## Seam and contract

The seam is the join between stage N's output and stage N+1's input. The contract is
the shape both sides agree to. In practice, that means: stage 1 promises to hand back
*only* the translated text, nothing else, and stage 2 is written assuming exactly
that. The moment stage 1 gets chatty — adds a preamble, a disclaimer, a "Here's your
translation:" — stage 2 either breaks or, worse, silently processes garbage as if it
were legitimate input.

This is the single most common way a homemade pipeline fails in practice: not the
model being wrong, but two honest, individually-correct stages disagreeing about
what's supposed to cross the seam between them.

## The step function

Under the hood, every stage in this series follows the same three-part shape:

1. Validate the input you were handed.
2. Call the model (or don't).
3. Validate what comes back before it's allowed to leave this stage.

That third step is not optional. A pipeline with no validation at any seam is really
just four prompts glued together with hope.

## Not a conversation

One easy mistake: assuming that because you're calling the same API four times in a
row, you should use its multi-turn conversation feature to "remember" what happened
in the earlier stages. Don't. A pipeline's stages are independent calls; *your own
code* holds the state between them — you read stage N's validated output and pass it
in as stage N+1's input, explicitly, in your own Python. The API's own conversation
memory is for one ongoing back-and-forth, not for wiring together stages that have
nothing to do with a "conversation" in the user-facing sense.

## Cost and latency don't disappear, they add up

If one Smart Intern call costs X and takes T seconds, four of them chained together
cost roughly 4X and take roughly 4T — because each stage has to finish before the
next one can start; that's what "fixed order" means. This is the real, honest
trade-off of this pattern: more control per step, in exchange for paying for every
step in full. We'll come back to this math with real numbers later in the series.

## Partial failure — the new failure mode

In Part 1, a call either worked or it didn't. Now there's a third option: stage 1
succeeds, stage 2 fails. What do you do with the fact that stage 1 already ran? This
is where a pipeline starts needing its own discipline around retries and
idempotency — more on that in Episode 3.

## Hands-On Conceptual Exercise

1. Pick a multi-step task you currently do by hand or with one giant prompt (a
   report, a triage process, an onboarding checklist).
2. Break it into stages on paper. For each stage, write down exactly what comes in
   and exactly what must come out — nothing vague like "a summary," but the actual
   shape (a string? a list? a specific JSON field?).
3. Find the one seam in your sketch that's the least well-defined. That's the one
   that will break first in real usage.

💡 Which of your own workflows just revealed a fuzzy seam when you tried this? Tell me
in the comments.

See you next episode, where we build the Risk Report Pipeline for real, end to end.

**Next:** [Episode 2 — Building Your First Pipeline](./02-foundations.md)
