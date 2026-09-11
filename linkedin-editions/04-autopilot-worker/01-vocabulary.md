# Episode 1 — The Vocabulary of the Loop

*Part 4 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part I](../../04-autopilot-worker-tool-using-loop/01-vocabulary.md).*

Every pattern so far has had a shape you could draw in advance: one call, a fixed
chain of calls, a chain with a lookup inserted. This week, for the first time, the
shape of what happens is decided while it's happening.

## The example: checking the weather, properly this time

Give the model two tools — check the weather for a city, and send an alert email —
and one instruction: check three specific cities, and email an alert if any of them
crosses a wind or storm threshold. Nobody tells the model how many times to check
the weather, or whether to send the email. It decides, based on what it actually
finds.

## Tool

A described capability the model *may* choose to use — not something that runs
automatically just because it exists. You describe what it does and what
arguments it takes; the model decides, per situation, whether and when to reach for
it.

## Think, act, observe, repeat

Underneath, every turn of this loop is the same three-part rhythm: the model
reasons about what to do next, calls a tool, and gets back the real result of that
call — then does it again, using what it just learned, until it decides it's done.

## No autopilot inside the autopilot

Here's a detail worth knowing before you build one: nothing runs your functions for
you automatically. The model tells you *which* function it wants and with *what
arguments* — your own code is what actually executes it and hands the result back.
This isn't a limitation to work around; it's exactly the seam where you get to
inspect, validate, and refuse before anything actually happens.

## How the loop ends — both ways

A loop should end one of two ways: the model decides it has enough information and
stops asking for tools, or your own code cuts it off after a fixed number of turns.
Only the first one is the happy path. The second one is not optional to build —
a loop that can, in principle, keep calling tools forever is a real cost and time
problem, not a hypothetical one.

## The tool list is still fixed, even though the order isn't

Here's the nuance worth sitting with: the model can only ever call tools you
explicitly gave it. The *set* of possible actions is decided by you, in advance,
same as ever. What's new is that the *sequence* through them — how many calls, in
what order — is no longer yours to script.

## Hands-On Conceptual Exercise

1. Think of a real task where the number of steps genuinely depends on what you
   find along the way (not a task you could just hardcode as "always three
   steps").
2. List the tools such a system would need. Keep the list as short as it can
   honestly be.
3. Decide: for each tool on your list, what should happen if the model tries to
   call it with a value that doesn't make sense?

💡 What's the shortest tool list your idea could get away with?

**Next:** [Episode 2 — When a Loop Earns Its Keep](./02-foundations.md)
