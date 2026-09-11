# Episode 5 — Bounded Autonomy

*Part 4 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part VII](../../04-autopilot-worker-tool-using-loop/07-advanced.md) and
[Part VIII](../../04-autopilot-worker-tool-using-loop/08-practice.md).*

Everything built this part still has a small, fixed, human-reviewed list of tools
and a hard cap on turns. That's the whole difference between "Blueprint 4 built
responsibly" and something genuinely riskier. Worth naming plainly what would tip
it past that line: a loop that can change its own tool list while running, or one
that hands off to other autonomous agents with no human checkpoint in between. This
series doesn't build that. It's a real, serious escalation, not a natural next
step to casually reach for.

## A tool's result is still someone else's data

If any tool touches the outside world — a real weather API, say, instead of our
simulated one — its response is exactly as untrusted as a support ticket typed by a
stranger. A tool result re-enters the model's context; it deserves the same
skepticism as anything else that came from outside your own code, not automatic
trust just because it arrived via a tool you built.

## Some actions shouldn't be tools at all

A human-approval gate is a real safeguard, but it's not an unbreakable one — a
sufficiently persuasive piece of text could in principle talk a model into calling
a gated tool it shouldn't. For anything genuinely irreversible, the safer design is
often simpler: don't make it callable at all. Less capability, more safety — a real
tradeoff, not a solved problem.

## When one agent's tools start fighting each other

If a single objective genuinely needs two conflicting styles of reasoning — a
strict, literal analyst voice and a warm, creative one, say — crammed into one
system prompt, they'll interfere with each other. That's the signal to split them
into separate specialists with a supervisor coordinating between them. That's next
part's entire subject.

## Ten ways this quietly breaks

No hard cap on turns. Trusting a tool's arguments without validating them. Letting
an action-shaped tool run for real with no human in the loop. Trusting a tool's
result just because it's "yours." Restarting a whole loop from turn one after a
network blip instead of retrying just the failed step. Giving the model a tool it
doesn't strictly need "just in case." Grading only the final answer instead of
whether the right tools were actually called. Reaching for a loop when a plain `if`
would do. Letting the tool list itself change at runtime. And forgetting that turn
count is a real, variable cost worth watching.

## Hands-On Conceptual Exercise

1. Run the "should this even be a tool" test against your own action-shaped tool
   ideas. Would any of them be safer simply not existing as a tool at all?
2. On paper only — never actually run this — imagine removing your turn cap
   entirely. Write down the worst plausible outcome, then pick a real cap and
   justify the number.
3. Describe, in one sentence, a task you've encountered where two genuinely
   conflicting reasoning styles would fight if crammed into one system prompt.

💡 Which of the ten broke a system you've actually seen in the wild?

We've now built four of five patterns: one call, a fixed chain, a chain with a
lookup, and a bounded loop that decides its own steps. Next time: what happens when
one agent's job genuinely needs a team.

**Back to:** [Part 4 index](./00-index.md)
