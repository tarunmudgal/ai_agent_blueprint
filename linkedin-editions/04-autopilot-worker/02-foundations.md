# Episode 2 — When a Loop Earns Its Keep

*Part 4 of The AI Agent Blueprint. Full runnable code lives in the
[GitHub edition, Part II](../../04-autopilot-worker-tool-using-loop/02-foundations.md).*

## Best used for / Avoid when

> **Best used for:** Dynamic workflows where the exact sequence or number of steps
> is unpredictable at the start, such as checking a fluctuating live weather status
> and automatically emailing an alert.
>
> **Avoid when:** The task can be perfectly handled by standard, predictable
> conditional code.

That second line deserves a concrete baseline. Part 2's routing stage — "if urgency
is 4 or higher, escalate" — is exactly the kind of decision that needs neither a
model nor a loop. One line of code, no ambiguity, no reason to spend a model call
on it. Contrast that with checking whether today's wind speed crosses a threshold:
you could hardcode which three cities to check, but not what the weather actually
is today. That's the real test — not "is this complicated," but "can I actually
write the whole decision tree down in advance."

## Three patterns, one crisp test each

- **Fixed pipeline (Part 2):** you know the exact steps and their order in advance.
- **Grounded lookup (Part 3):** one fixed retrieval step, not a search that decides
  on its own to try again differently.
- **This pattern:** the model itself decides the sequence and count of actions,
  turn by turn, based on what it learns along the way.

Getting this test right matters, because each of the first two is simpler, cheaper,
and easier to test than this one — reach for this pattern only when the honest
answer to "could I write the steps down in advance" is no.

## Anatomy of one turn

Every turn in the loop follows the same shape: history so far goes in, the model
either asks for a tool call or gives a final answer, if it's a tool call your code
validates the arguments before running anything, and the result feeds back in as
the next turn's history.

## Building it end to end

The full Weather Alert Worker: two tools registered, one plain-language objective,
a hard cap on turns. Run it, and watch it check each city, reason about whether the
threshold is crossed, and either stop quietly or send exactly one alert — all
without a single hardcoded "and then check city two" instruction anywhere in the
code.

## Hands-On Conceptual Exercise

1. Take a decision you currently automate with a plain `if` statement. Confirm
   honestly it doesn't need this pattern.
2. Take the "unpredictable steps" example from Episode 1. Run the three-pattern
   test against it explicitly: could you write the steps down in advance? Is it
   one lookup, or several adaptive ones?
3. Sketch the one turn your own system would need to validate most carefully
   before acting on it.

💡 Which of your own workflows keeps almost, but not quite, fitting into a fixed
`if`/`else`?

**Next:** [Episode 3 — Giving an Agent Real Tools](./03-core-and-reliability.md)
