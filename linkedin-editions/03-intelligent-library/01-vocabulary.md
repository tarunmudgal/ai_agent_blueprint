# Episode 1 — The Vocabulary of Retrieval

*Part 3 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part I](../../03-intelligent-library-grounded-context/01-vocabulary.md).*

Picture a librarian who, handed any question, confidently answers from whichever
book happens to be closest at hand — never checking whether it's actually the right
book. That's worse than a librarian who says "we don't have that." This week's whole
topic is making sure the "fetch the right book" step is trustworthy, because
everything downstream of it depends on getting that one step right.

## Four documents, not one

Take a small internal library: a payment-incident postmortem, a refund policy, an
onboarding FAQ, and an API rate-limits reference. A question like "if a customer's
charged twice, are they owed an automatic refund?" could plausibly be answered by
either the postmortem or the refund policy — both mention "charged twice." Only one
of them actually answers the question. That's the whole problem retrieval exists to
solve: picking the right source before you ever ask the model anything.

## Chunk

A document gets split into smaller retrievable pieces — chunks — usually along
natural boundaries like paragraphs. Each chunk keeps its own bearings on where it
came from, so a matched chunk always tells you which document it belongs to.

## Embedding

Each chunk becomes a vector of numbers via a dedicated embedding model — a
completely different model from the one that generates your answers. One detail
matters more than any other here: you embed the corpus's chunks with one mode
("this is a document to be searched") and you embed the user's question with a
different mode ("this is a search query"). Mixing these up quietly degrades search
quality, even though nothing throws an error to warn you.

## Index

The embedded chunks, stored somewhere searchable. At the scale of four short
documents, "somewhere searchable" is a plain list in memory — no database required.
At real scale, this becomes a proper vector database, or a managed search service.
Name the destination, but don't feel obligated to build the destination before you
need it.

## Similarity search

Given a question's own vector, rank every chunk in the index by how close its
vector is to the question's vector, and take the top few. This is what actually
answers "which document," and it's doing semantic matching, not keyword matching —
it can (and should) prefer the refund policy over the postmortem for a
policy question, even though the postmortem's text overlaps more on the surface.

## Retrieval and verification are two different jobs

This is the one distinction worth remembering above all the mechanics: retrieval
decides *which* chunk gets pasted into the prompt. Part 1's verification technique —
force a verbatim quote, then check it's an actual substring of the source — decides
whether the model's claim is *faithful to that chunk*. Getting the right chunk and
getting a faithful answer from that chunk are two separate failure points. A
pipeline that only gets one of them right is still broken.

## Hands-On Conceptual Exercise

1. List three to five real documents you or your team reference often (a policy
   doc, a runbook, a FAQ). For each, write one realistic question only that
   document answers.
2. For two of those documents, write one question where BOTH documents share
   surface-level wording, but only one is actually correct — like our "charged
   twice" example.
3. Guess, honestly: would a plain keyword search get your Exercise 2 answer right,
   or would it need real semantic matching?

💡 Which of your own documents would a keyword search get wrong?

**Next:** [Episode 2 — Building Your First Grounded Search](./02-foundations.md)
