# Episode 2 — Building Your First Grounded Search

*Part 3 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part II](../../03-intelligent-library-grounded-context/02-foundations.md).*

## Best used for / Avoid when

The parent article's line for this pattern:

> **Best used for:** Reliable Q&A search engines built over internal corporate
> wikis, fresh product catalogs, or private PDF operational runbooks.
>
> **Avoid when:** The system needs to proactively complete external actions, like
> modifying databases or sending outbound emails.

That second line is a hard boundary we'll come back to later in this part: this
pattern retrieves and grounds an answer. It does not act on the world. The moment a
step in your pipeline starts writing to a database or sending an email on its own
initiative, you've quietly left this pattern behind.

## When you don't actually need this

Before building anything: if your whole corpus comfortably fits inside one prompt
and doesn't change often, you may not need retrieval at all — you need Part 1's
verification technique and a bigger paste. Our own four-document library is small
enough that pasting all of it would genuinely work. We build the retrieval layer
anyway in this series because most real corpora *don't* stay that small — but it's
worth asking the question honestly before you reach for this pattern in your own
work.

## The whole thing, end to end

Chunk all four documents. Embed every chunk once. Then answer three different kinds
of questions against the same small index:

1. A question clearly answered by one document (how many customers were charged
   twice in the October incident — answered by the postmortem).
2. A question that requires picking the *right* document among plausible-looking
   candidates (are duplicate charges automatically refunded — answered by the
   refund policy, not the postmortem, despite the overlapping wording).
3. A question the corpus simply cannot answer (a company phone number that's
   nowhere in any of the four documents) — which should come back as "not found,"
   using Part 1's exact `NONE` / "Data unavailable" path, not a confident guess.

That third case matters as much as the first two. A retrieval system that always
finds *something* to say is more dangerous than one that occasionally, correctly,
says nothing.

## Anatomy of one retrieval

Every retrieval, regardless of which question triggered it, follows the same shape:

```
[ question ] -> [ embed as a query ] -> [ search the index ] -> [ ranked chunks ] -> [ Part 1's grounded-answer check ]
```

Nothing about the "answer" half of that chain is new. Everything left of the arrow
into "ranked chunks" is what this part adds.

## Hands-On Conceptual Exercise

1. From Episode 1's document list, write one question per document type: one that's
   clearly answered, one that requires disambiguating between two plausible
   documents, and one your documents genuinely can't answer.
2. For the unanswerable one, write down what a bad system would probably do wrong
   (guess confidently) versus what you actually want it to do (say so plainly).
3. Rough out, in one sentence, whether your own documents would even need
   retrieval — or whether they'd fit in one prompt today.

💡 Did the "do I even need this" question change your answer?

**Next:** [Episode 3 — Giving a Pipeline a Memory](./03-core-and-reliability.md)
