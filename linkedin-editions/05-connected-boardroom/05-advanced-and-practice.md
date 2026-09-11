# Episode 5 — The Whole Series, Assembled

*Part 5 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part VII](../../05-connected-boardroom-specialist-networks/07-advanced.md) and
[Part VIII](../../05-connected-boardroom-specialist-networks/08-practice.md).*

## The honest limits of a boardroom

More agents means more places for a hand-off to lose fidelity, more cost, and a
Supervisor that itself needs a well-scoped, disciplined prompt — or it becomes
exactly the kind of unfocused agent this whole pattern exists to avoid. And past a
single Supervisor with a flat team of specialists, real systems sometimes need a
hierarchy of teams. That's a real pattern in the wild. This series doesn't build
it — it's genuinely past the edge of what five blueprints cover.

## The oldest lesson, still true at every new seam

Every blueprint in this series has re-taught the same discipline in a new shape:
untrusted input stays untrusted no matter how many hops it travels through. A
support ticket typed by a stranger was untrusted in Part 1. A retrieved document
was still untrusted in Part 3. A specialist's output, here, is no different —
if it ultimately traces back to something a user typed, every specialist that
touches it needs to treat it that way, not just the first one.

## Ten ways this quietly breaks

No clear division of labor between specialists. The Supervisor doing a
specialist's job itself. Paraphrasing between hops instead of passing output
verbatim. Reaching for a team when one call or one loop would've done. Giving one
specialist an overly broad, unfocused prompt — persona conflict, reintroduced one
level down. No team manifest, so nobody can tell which specialists a given task is
even allowed to use. Grading only the final report instead of whether the right
specialists were actually consulted. Forgetting that team cost stacks three ways.
Trusting a specialist's output without the same skepticism you'd apply anywhere
else. And, the one that applies to this entire series, not just this chapter:
reaching for any more complex pattern before a concrete, named limitation of the
simpler one actually forced the upgrade.

## The Golden Rule, assembled

Across all five parts, the same decision tree, fully built out: simple, one-turn
task — Part 1. Rigid, step-by-step flow — Part 2. Needs private or fresh data —
Part 3. Dynamic, unpredictable tools — Part 4. Genuinely conflicting expert
domains — Part 5. And at every branch, a demotion check worth asking honestly:
could a simpler pattern one step back have actually done this. The rule underneath
all five parts, unchanged since Part 1:

> Always start with the simplest pattern that works. Only upgrade your complexity
> tier when your requirements absolutely force you to.

## Hands-On Conceptual Exercise

1. Take a real task of your own and run the full five-part decision test against
   it, end to end — land on one blueprint, and write one sentence justifying why
   it's that one and not a simpler one.
2. Name, honestly, which of the ten ways-this-breaks you've personally shipped at
   some point.
3. Pick the blueprint you're most likely to reach for next, and write down the
   one concrete signal that would tell you it's time to upgrade to it.

💡 This is the last one: which of the five blueprints did you actually end up
building? There's no next episode to tease — reply and let us know.

That's the series. One call. A fixed chain. A chain grounded in a library. A loop
that decides its own steps. A team coordinated by a supervisor that does none of
their work itself. Five patterns, one rule underneath all of them: start simple,
and only add structure when the simpler thing actually, concretely, ran out of
road.

**Back to:** [Part 5 index](./00-index.md)
