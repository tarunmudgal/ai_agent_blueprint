# Episode 1 — The Vocabulary of a Specialist Team

*Part 5 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part I](../../05-connected-boardroom-specialist-networks/01-vocabulary.md).*

Every pattern so far has been one model, doing one job, however that job was
shaped — a single call, a fixed chain, a chain with a lookup, a loop that decides
its own steps. This week the model count changes. Not because one model got more
powerful, but because one job turned out to need more than one voice.

## The example: a supervisor and one specialist

Take the whole Support Ticket Autopilot from Part 4 — the tool loop that checks
policy, checks history, decides to escalate or draft a reply — and wrap it as one
callable unit: a `support_specialist`. Give it to a new, thinner agent whose only
job is to decide when to call it and what to do with what comes back. That thinner
agent is the Supervisor.

## Specialist

A narrow, disciplined agent with its own system prompt, built to do one kind of
job well. A specialist doesn't need to know about any other specialist, and it
doesn't need to know it's part of a larger system at all.

## Supervisor

Built exactly like Part 4's tool-calling loop, except each "tool" is a dispatch to
a specialist instead of a plain function. Its own system prompt is explicit about
what it's *not* allowed to do: no policy lookups, no drafting customer replies, no
doing a specialist's job itself.

## No new API for this

Worth saying plainly, because it's easy to assume otherwise: there is no
"multi-agent" feature being unlocked here. A specialist is just another model call
with its own persona. A Supervisor coordinating several of them is recursion, not a
new primitive — the same `client.interactions.create` call this whole series has
used, called from inside a loop, calling itself again.

## Dispatch and synthesis

The Supervisor has exactly two jobs: deciding *who* to call (dispatch), and
combining what comes back into one coherent answer (synthesis). Neither job
involves doing the actual specialist work — the moment it does, something has gone
wrong.

## Persona conflict, made concrete

Picture a single system prompt trying to be both "a strict, literal data analyst"
and "warm and empathetic" in the same breath. It doesn't fail cleanly — it drifts,
leaning into whichever instruction it read most recently, and you can't predict
which one wins on any given call. That drift is the exact problem this pattern
exists to remove, by giving each persona its own agent instead of asking one agent
to hold both at once.

## Hands-On Conceptual Exercise

1. Think of a task you've already given one model that secretly asks it to be two
   different kinds of expert at once (precise and empathetic, technical and
   persuasive, cautious and decisive).
2. Write out, as two separate one-line system prompts, what each half of that job
   would look like on its own.
3. Decide: who calls each of your two experts, and in what order — does one need
   the other's answer first?

💡 What's the smallest number of specialists your idea could get away with?

**Next:** [Episode 2 — When You Actually Need a Boardroom](./02-foundations.md)
