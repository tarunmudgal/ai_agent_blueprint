# Episode 4 — Packaging a Library

*Part 3 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part V](../../03-intelligent-library-grounded-context/05-reusable-artifacts.md) and
[Part VI](../../03-intelligent-library-grounded-context/06-production.md).*

Once your retrieval layer works, the same packaging instinct from Part 2 applies
again, one level further out: a corpus is a reusable artifact too, and it needs its
own discipline.

## A corpus is not static

If the refund policy document changes next quarter, every chunk that came from it
needs re-embedding, and the index needs updating. There's no error message when this
doesn't happen — the system just keeps confidently answering with outdated policy.
A corpus manifest that records which embedding model version built the index, and a
content hash per source document, is what lets you detect "this document changed
since it was last embedded" without re-embedding everything just to check.

## Retrieval as its own kind of stage

The lookup stage from Episode 3 isn't a new orchestration idea — it's Part 2's
existing `Stage`/`Pipeline` shape, wrapping a search call instead of a model call
or a plain rule. That's worth appreciating on its own: this series keeps adding new
*kinds* of stages without ever needing a new way to chain them together.

## Where the cost actually shows up — twice

Embedding cost happens at two different moments that are easy to conflate.
Embedding your corpus happens once, rarely, whenever documents change — call it
amortized. Embedding the user's question happens on every single request. At small
scale neither one matters much. At real scale, the second one is the one that adds
up, and a linear search over "just check everything" stops being fast enough long
before your embedding bill does — that's the point where a real vector database
earns its keep.

## Evaluating retrieval on its own terms

Here's a subtlety worth its own eval: your pipeline can retrieve the *right*
document and still answer badly, or retrieve the *wrong* document and still stumble
into a right-sounding answer. That means retrieval quality and final-answer quality
are two different things to measure. A small golden set of (question, expected
document) pairs — checked purely on whether the top retrieved result matches, no
generation involved — tells you something an end-to-end eval alone would miss.

## Hands-On Conceptual Exercise

1. For your own corpus idea, write a one-line manifest: which documents, which
   embedding model, when each was last updated.
2. Guess which moment — indexing or querying — would dominate your own system's
   embedding cost, and why.
3. Write three (question, expected document) pairs for your own corpus that you
   could use to check retrieval quality on its own, without generating an answer at
   all.

💡 Which of your documents is most likely to go stale without anyone noticing?

**Next:** [Episode 5 — Retrieve and Ground, Never Retrieve and Act](./05-advanced-and-practice.md)
