# Episode 3 — Giving a Pipeline a Memory

*Part 3 of The AI Agent Blueprint. Full runnable code lives in the GitHub edition,
[Part III](../../03-intelligent-library-grounded-context/03-core-techniques.md) and
[Part IV](../../03-intelligent-library-grounded-context/04-reliability.md).*

This is where the series properly connects. Remember Part 2's Incident Response
Pipeline — classify, route, rewrite, log — built entirely from Part 1's prompts?
It gets exactly one new stage this week, and nothing else about it changes.

## One new stage, inserted in the middle

```
ticket -> classify (Part 1) -> route (plain code) -> ground (new) -> rewrite (Part 1) -> log summary (Part 1)
```

The new GROUND stage takes the ticket, searches the same small library from
Episodes 1-2, and hands the most relevant chunk to the rewrite stage. Now the
customer-facing explanation can cite the actual refund policy instead of the model
inventing plausible-sounding policy language from its own training data. Part 1 gave
this pipeline its prompts. Part 2 gave it structure and reuse discipline. Part 3
gives it a memory it can look things up in.

## Verifying the grounded claim, unchanged

Whatever policy claim ends up in the rewritten customer message still has to pass
Part 1's exact test: is the supporting quote an actual, verbatim substring of the
retrieved chunk? If not, the whole claim is untrusted, no matter how confident it
sounds. Retrieval decides *which* chunk. This check decides whether the answer is
*faithful* to that chunk. Both have to pass.

## The harder problem: right shape, wrong document

Here's an honest limit worth sitting with. Part 1's substring check catches a
*hallucinated* quote — the model made something up that isn't anywhere in the
source. It does *not* catch a confidently-answered question grounded in the
*wrong but real* chunk. If retrieval hands back the onboarding FAQ instead of the
refund policy for a borderline question, and the model faithfully quotes the FAQ,
you get a well-supported, perfectly verified, completely irrelevant answer. Nothing
in the verification step alone catches that.

## A similarity threshold as a safety net

One real mitigation: refuse to answer at all if the top retrieved chunk's
similarity score falls below a threshold, rather than grounding an answer in a weak
match just because it was the best one available. This is a blunt tool, but an
honest one — better to say "I'm not confident enough" than to sound certain about
the wrong document.

## Hands-On Conceptual Exercise

1. Sketch one pipeline of your own that could benefit from a "look something up in
   the middle" stage, the way our Incident Response Pipeline just did.
2. For that stage, decide: what should happen if the lookup returns something with
   low confidence? Refuse, ask a human, or proceed with a caveat?
3. Write down one question you could ask your own corpus where the "right shape,
   wrong document" trap could plausibly happen. What would tip you off that it did?

💡 Where in your own systems does a "confidently wrong but technically supported"
answer already worry you?

**Next:** [Episode 4 — Packaging a Library](./04-artifacts-and-production.md)
