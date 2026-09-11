# Episode 5 — The Line Between "Fixed" and "You Built an Agent by Accident"

*Part 2 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part VII](../../02-fixed-assembly-line-sequential-pipelines/07-advanced.md) and
[Part VIII](../../02-fixed-assembly-line-sequential-pipelines/08-practice.md).*

We've been circling this test all series. Here's the final, explicit version of it,
because it's the one thing worth remembering after everything else in this part
fades: **is the decision being made on the input, or on a model's output?**

## The test, worked both ways

*Valid, still Blueprint 2:* your translate stage checks a `language` field on the
incoming document — set before the pipeline ever runs — and skips translation if it's
already English. The set of stages that *could* run was fully decided at design time;
this run just took one of the pre-defined paths.

*Invalid, secretly Blueprint 4:* you ask the classifier to also decide whether an
extra "draft an escalation email" stage should run this time. The moment a model's
output determines which stages exist for this run — not just which pre-defined branch
gets taken — you've built something that adapts its own shape at runtime. That's
Blueprint 4 (The Autopilot Worker), and it's a fine thing to build, but it's not this
pattern, and pretending otherwise is how "fixed" pipelines quietly turn into
unmaintainable ones.

Our own Incident Response Pipeline's routing stage is fine specifically *because*
both outcomes — escalate, or continue — are fixed and known in advance. The pipeline
never grows or shrinks a stage based on what the classifier says; it just takes one
of two paths that were always there.

## Trust doesn't transfer between stages

One more sharp edge: if an untrusted ticket contains a prompt-injection attempt and
your classifier resists it, that does *not* mean the rewrite stage downstream can
relax. Each stage has to independently treat untrusted input as untrusted — an
earlier stage not falling for something is not a credential that travels forward.

## A short pattern library

A few shapes worth having ready: translate→summarize→extract→format (our Risk Report
Pipeline); classify→route→respond→log (our Incident Response Pipeline);
draft→critique→revise, where revise always runs once — the critique stage doesn't
get to decide whether revision happens, or you've crossed the line above; and
fetch-context→ground→answer, which sits right at the edge of this pattern and is
actually why Blueprint 3 (The Intelligent Library) exists as its own topic next.

## Ten ways this quietly breaks

No contract at a seam. Retrying the whole pipeline instead of just the failed stage.
Worrying a fixed routing rule is secretly dynamic when it isn't. The opposite mistake
— calling something "fixed" when a stage's output actually determines what runs
next. No run ID, so a failed run can't be reconstructed. Bumping one stage's prompt
without bumping the pipeline's own version. Merging stages that serve different
audiences just to save a round trip. Adding stages before asking if one well-written
single-shot prompt would do. Forgetting that cost is additive until the bill shows up.
And re-trusting input at a later stage just because an earlier one wasn't fooled.

## Hands-On Conceptual Exercise

1. Run the input-vs-output test against your own pipeline sketch, stage by stage.
   Did you find a decision you'd assumed was "fixed" that's actually being made on a
   model's output?
2. If you found one, redesign it as an explicit, fixed two-branch decision instead —
   or admit honestly that what you're building now belongs to Blueprint 4.
3. Pick one of the ten failure modes above that you've personally hit in real code
   (yours or someone else's), and write one sentence on what actually fixed it.

💡 Which of the ten broke a pipeline you've actually shipped? I want to hear the real
stories in the comments.

See you next time for Blueprint 3 — The Intelligent Library, where we finally give
the model access to something it wasn't trained on.

**Back to:** [Part 2 index](./00-index.md)
