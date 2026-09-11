# Episode 3 — Three Experts, One Report

*Part 5 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part III](../../05-connected-boardroom-specialist-networks/03-core-techniques.md) and
[Part IV](../../05-connected-boardroom-specialist-networks/04-reliability.md).*

## The Quarterly Billing Review

Three specialists, three deliberately conflicting personas. A `data_analyst`,
strict and literal, given a small table of billing anomalies and forbidden from
speculating about cause. A `policy_specialist`, grounded against the refund
policy document — the same discipline Part 3 taught, simplified. A
`communications_specialist`, warm and empathetic, drafting a customer-facing
explanation — never sending it, only drafting.

## Order matters

The communications specialist needs the other two's facts before it can write
anything honest. The Supervisor calls the data analyst and the policy specialist
first, and only then hands their real output forward to the communications
specialist. Sequencing this correctly is the Supervisor's actual job — not
producing any of the three answers itself.

## The Supervisor's own restriction, taken seriously

Its system prompt explicitly forbids it from computing statistics, reciting policy
from memory, or drafting customer language on its own. A Supervisor that invents a
number instead of citing what the data analyst actually said has broken its one
job — this is worth watching for, because it's the natural failure mode of giving
a coordinating agent just enough context to sound confident.

## When specialists disagree, or a hand-off gets garbled

Specialists don't share context except what the Supervisor explicitly passes
between them — which means a paraphrasing error between two hops is a new failure
mode this pattern introduces that a single model doesn't have. The fix is
mechanical: pass each specialist's actual output forward verbatim, never the
Supervisor's own summary of it.

## A specialist that fails

If one specialist's call fails outright, that's worth retrying once or twice. If
it genuinely can't answer — no policy actually covers this case — that's not a
bug to hide. It's a real gap that belongs in the final report, stated honestly,
rather than papered over with an invented answer.

## Hands-On Conceptual Exercise

1. Sketch your own three-specialist task. Name each persona in one line, and note
   which one needs another's output before it can start.
2. Write the Supervisor's one-line restriction — the thing it's explicitly not
   allowed to do itself.
3. Pick one specialist and describe what "genuinely can't answer this" looks like
   for it, versus a transient failure worth just retrying.

💡 Where has a paraphrased hand-off between two people (not even models) caused a
real mix-up you've seen at work?

**Next:** [Episode 4 — Keeping a Team Honest](./04-artifacts-and-production.md)
