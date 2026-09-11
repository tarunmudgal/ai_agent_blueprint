# Episode 2 — When You Actually Need a Boardroom

*Part 5 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part II](../../05-connected-boardroom-specialist-networks/02-foundations.md).*

## Best used for

The article's own framing: conflicting expert domains, where a task genuinely
needs more than one kind of judgment applied to it, and asking one model to hold
all of them in a single prompt causes it to blur between them.

## Avoid when

This is the most expensive pattern in the series to reach for by accident. Every
prior chapter said some version of "you might not need this" — this one costs the
most extra calls of any of them, so the check has real teeth: if you can't name two
genuinely conflicting personas or skill sets your task needs, you don't need a
boardroom. You need Part 4's single loop, or even Part 1's single call.

## The five blueprints, in one line each

Since this is the last chapter, worth saying plainly what each one solved:

- **Part 1** — one call, one answer.
- **Part 2** — a fixed sequence of calls, each stage's output feeding the next.
- **Part 3** — calls grounded against a searchable library, so the model isn't
  answering from memory.
- **Part 4** — a bounded loop that decides its own steps, using tools you gave it.
- **Part 5** — specialists coordinated by a Supervisor that does none of their work
  itself.

Part 5 exists for the case none of the first four cover: not a *steps* problem, and
not a *tools* problem, but a *persona* problem.

## Anatomy of one dispatch

Objective comes in. The Supervisor decides which specialist to call. That
specialist runs its own complete, isolated turn. The result comes back to the
Supervisor, which either dispatches again or synthesizes a final answer. Nothing in
that chain skips a step, and nothing lets the Supervisor shortcut straight to an
answer without actually consulting the specialist whose judgment the task needed.

## Hands-On Conceptual Exercise

1. Take the "do you need this at all" test from earlier — apply it to three tasks
   you've built or considered building. How many actually pass?
2. For any task that fails the test, name which single earlier blueprint (1
   through 4) would have solved it more cheaply.
3. For the one task (if any) that does pass, sketch its dispatch order: which
   specialist runs first, and does a later one depend on an earlier one's output?

💡 Which of your last five projects secretly needed this, and which just needed a
better single prompt?

**Next:** [Episode 3 — Three Experts, One Report](./03-core-and-reliability.md)
