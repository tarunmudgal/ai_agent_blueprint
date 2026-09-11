# Episode 5 — Retrieve and Ground, Never Retrieve and Act

*Part 3 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part VII](../../03-intelligent-library-grounded-context/07-advanced.md) and
[Part VIII](../../03-intelligent-library-grounded-context/08-practice.md).*

Time for this part's version of the test we've been sharpening all series.

## The line that must not move

Valid: the GROUND stage retrieves the refund policy and hands a *draft* reply to a
human, or to a fixed next stage, exactly like our pipeline already does. Invalid: a
stage retrieves the policy and *automatically issues the refund itself*, or emails
the customer with no review. The instant retrieval feeds an action instead of a
fixed next stage or a human, you've built Part 4's pattern wearing this one's
clothes.

There's a subtler version of the same trap: letting a stage decide, on its own,
whether to search again with a reformulated query if the first result looked weak.
That decision — "should I retrieve differently based on what I just retrieved" —
is exactly the kind of output-time decision Part 2 warned about. This part's
retrieval is one fixed lookup, not an adaptive search loop.

## A retrieved document is still untrusted input

If your corpus includes anything user-contributed or externally sourced, a
retrieved chunk deserves exactly the same suspicion as a support ticket typed
directly by a stranger. A document sitting in "your own" library that happens to
contain a hidden instruction is just as real a risk as one typed into a chat box —
the fact that it arrived via search doesn't make it trusted.

## When two retrieved chunks disagree

Sometimes the top two results both look relevant but say slightly different things —
an old policy and a newer one, say. The honest move at this scale is usually
surfacing both to a human rather than letting the model silently pick a winner.
Freshness problems and retrieval problems meet exactly here.

## Ten ways this quietly breaks

Pasting the whole corpus when it doesn't fit — or when it would have fit and you
didn't need retrieval at all. Mismatching document-mode and query-mode embeddings.
No confidence threshold, so every query gets a confident answer even from a weak
match. Trusting a retrieved chunk without Part 1's verification. Treating retrieval
as free when its cost is real and recurring. Never re-indexing, so the library goes
stale silently. Re-indexing everything on every tiny change instead of checking what
actually changed. Letting a stage decide on its own to search again differently.
Trusting a document just because it's "yours." And building a production vector
database for a corpus that would have fit in one prompt.

## Hands-On Conceptual Exercise

1. Run the retrieve-vs-act test against a system you've built or imagined. Did
   retrieval ever quietly feed an action instead of a fixed next step?
2. Add a fifth, deliberately conflicting document to this part's library on paper —
   say, a newer refund policy that shortens the refund window. What should the
   system do when both versions rank high for the same question?
3. Pick one of the ten failure modes above you've personally hit. What actually
   fixed it?

💡 Which of the ten broke a system you've actually shipped?

We've now built three of five patterns: one call, a fixed chain of calls, and calls
grounded in a searchable library. Next time: what happens when the software gets to
decide its own next step, instead of following a chain you wrote in advance.

**Back to:** [Part 3 index](./00-index.md)
