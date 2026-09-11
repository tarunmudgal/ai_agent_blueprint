# Episode 4 — Packaging an Agent

*Part 4 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part V](../../04-autopilot-worker-tool-using-loop/05-reusable-artifacts.md) and
[Part VI](../../04-autopilot-worker-tool-using-loop/06-production.md).*

Once a tool loop works, the same packaging instinct from Parts 2 and 3 applies
again: a small `Tool` wrapper (name, description, the actual function, whether it
needs human review) and a loop runner that threads objective in, transcript and
final answer out. Neither is a framework — it's the same restraint this whole
series has kept: enough structure to reuse, not enough to hide what's happening.

## The transcript is the artifact now

A fixed pipeline could get away with one log line per stage, because the stages
were always the same. A loop can't — since the sequence itself is what's
unpredictable, the only way to reconstruct "what actually happened" after the fact
is the full turn-by-turn transcript: every tool call, every argument, every result,
tied to one run ID.

## Tool descriptions are prompts too

A tool's name, description, and parameter shape steer the model's behavior just
like a system prompt does. A vaguely-worded description is a real way this pattern
misbehaves — version and review tool declarations with the same care you'd give a
prompt file.

## The cost question is different here too

A fixed pipeline's cost is the sum of a known number of stages. A loop's cost
depends on how many turns it actually takes — and a run that takes six turns
instead of two, for the exact same outcome, costs three times as much for nothing.
Watching average turns-per-run in production, and treating a rising average as a
signal to tighten tool descriptions or the objective, is a real, ongoing job this
pattern creates that fixed pipelines don't.

## A third kind of eval

Chapter 2 taught per-stage and end-to-end evals. Chapter 3 added a retrieval
precision eval. This pattern needs a third: did the loop use the *right tools, in a
sensible order*, to reach the *right final outcome* — checked separately, because a
loop can land on the correct final action by luck without actually checking what it
should have checked first.

## Hands-On Conceptual Exercise

1. Sketch a one-line "tool manifest" for your own idea: each tool's name, purpose,
   and whether it needs human review.
2. Guess whether your own system's cost would be dominated by turn count or by any
   single expensive tool call.
3. Write one (scenario, expected final action, tools that should have been called)
   triple you could use to eval your own loop's judgment, not just its final answer.

💡 Which of your tools would you most want a plain-English description review on
before anyone trusts it in production?

**Next:** [Episode 5 — Bounded Autonomy](./05-advanced-and-practice.md)
