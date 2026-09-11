# Episode 4 — Keeping a Team Honest

*Part 5 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part V](../../05-connected-boardroom-specialist-networks/05-reusable-artifacts.md) and
[Part VI](../../05-connected-boardroom-specialist-networks/06-production.md).*

## A specialist is a tool whose body is another agent

Nothing new needed to formalize this: a `Specialist` is the same reusable shape as
Part 4's `Tool`, except its function body makes a nested model call instead of
touching a plain function or a lookup. The Supervisor itself is Part 4's loop,
unmodified — this chapter adds a new kind of tool body, not a new kind of
orchestrator.

## A team manifest

Extend the pipeline manifest and prompt-versioning ideas from earlier parts one
level up: a small record of each specialist's name, its own prompt version, and
which specialists the Supervisor is allowed to call for a given kind of objective.
Change either a specialist's persona or the Supervisor's allowed roster, and you've
changed what the whole team can do — both deserve to be versioned together.

## The cost of a team, stacked three ways

This is the sharpest cost lesson in the series. A pipeline's cost was the sum of a
known number of stages. A loop's cost depended on how many turns it took. A team's
cost is the Supervisor's own turns *plus* every specialist call — and a specialist
that is itself a full tool-using loop (like the support specialist from Episode 1)
compounds further still. For the Quarterly Billing Review, the honest minimum is
the Supervisor's own dispatch-and-synthesis turns plus three separate specialist
calls — never fewer than that, and often more. This is exactly the overhead the
"avoid when" line from Episode 2 is warning about.

## Evaluating a team, properly

Grading only the final report misses the point. A real eval checks three things
separately: did the Supervisor call the right specialists, did it pass them the
right input verbatim, and does the final synthesis actually reflect what the
specialists said rather than something the Supervisor added on its own.

## Hands-On Conceptual Exercise

1. Write your own team manifest for a boardroom you've sketched earlier in this
   series — specialist names, versions, and who's allowed to call whom.
2. Work out the honest minimum call count for that same team, the way this
   episode did for the Quarterly Billing Review.
3. Design one eval check (not the final answer's quality) that would catch a
   Supervisor quietly skipping a specialist it should have called.

💡 Has a project you've worked on ever quietly ballooned in cost the same way —
each new layer of coordination adding calls nobody budgeted for?

**Next:** [Episode 5 — The Whole Series, Assembled](./05-advanced-and-practice.md)
