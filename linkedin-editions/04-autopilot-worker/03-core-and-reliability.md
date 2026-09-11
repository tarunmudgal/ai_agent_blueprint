# Episode 3 — Giving an Agent Real Tools

*Part 4 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part III](../../04-autopilot-worker-tool-using-loop/03-core-techniques.md) and
[Part IV](../../04-autopilot-worker-tool-using-loop/04-reliability.md).*

Remember our support ticket — classified in Part 1, routed in Part 2, grounded in
Part 3? This week it finally meets a real decision-maker.

## Four tools, one objective

Instead of a fixed sequence, the model gets four tools: look up the refund policy,
check the customer's account history, escalate to a human, or draft a customer
reply. The instruction is simple: handle the ticket, look up whatever you need, and
land on an outcome. Which tools it uses, and in what order, is entirely up to it.

Because this specific customer has been charged twice for a second month running —
and the policy says repeat duplication needs manual review — a good run checks the
account history, checks the policy, and escalates rather than confidently drafting
an auto-refund reply.

## The two tools that don't get to act unsupervised

Two of the four tools are read-only lookups. The other two — escalate, and draft a
reply — are simulated in every example in this series: they print what they would
do and hand back a fake confirmation. Nothing here ever sends a real email or
issues a real refund. That's a deliberate design choice, not a limitation: an
action with real consequences gets a human between the decision and the effect,
full stop.

## What if the loop skips a step it shouldn't have?

Here's the honest part: this is a genuine test of judgment, not a scripted demo,
so it can go wrong. If the model reaches for "draft a reply" without first checking
history or policy, that's a real failure mode worth catching — not by trusting the
model's own sense that it's done, but by checking, in your own code, whether the
tools that *should* have been called actually were, before accepting the final
action.

## The loop that never stops is a real bug, not a metaphor

A model can, in principle, keep calling tools without ever quite deciding it's
finished. A hard cap on the number of turns isn't a nice-to-have — without one, this
is a literal runaway cost and latency problem. Hitting that cap is a real outcome to
handle (log it, stop, hand the partial trail to a human), not something to quietly
retry forever.

## Hands-On Conceptual Exercise

1. For your own tool-list sketch from Episode 1, mark which tools are read-only and
   which have a real-world consequence.
2. Write one audit rule: which tools must have been called before your system
   accepts a consequential action as final?
3. Pick a reasonable turn cap for your own idea, and write down what should happen
   when it's hit.

💡 Which of your own tools would you never let run unsupervised, no matter how
confident the system sounded?

**Next:** [Episode 4 — Packaging an Agent](./04-artifacts-and-production.md)
