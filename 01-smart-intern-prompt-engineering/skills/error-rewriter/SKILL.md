---
name: error-rewriter
description: Rewrites raw application stack traces and error logs into three plain-language lines a first-line support agent can use while talking to a customer. Use when handed a traceback, an exception dump, or a raw error log that needs to become customer-safe language.
---

<!--
  ILLUSTRATIVE EXAMPLE — MANAGED-AGENT FORMAT ONLY.

  This file demonstrates the Gemini API skill format used by managed agents
  (base_agent="antigravity-preview-05-2026", preview). It is mounted into an
  agent environment via client.agents.create(base_environment=...) at the path
  .agents/skills/error-rewriter/SKILL.md

  It is NOT read by client.interactions.create() and it is NOT part of
  Blueprint 1. A single-shot call has no loop and no filesystem access, so
  nothing here can be discovered or loaded at request time.

  The Blueprint 1 equivalent of this file is
  prompts/error_rewriter.system.md, passed explicitly as system_instruction=.
  See skills/README.md.
-->

# Error rewriter

Turn a raw error into something a non-technical support agent can act on
immediately, without misleading the customer.

## When to use this skill

Use it when the input is machine-generated failure output: a Python traceback,
a Java stack trace, a JSON error payload, a log excerpt containing an exception.

Do not use it for:

- Product questions or how-to requests — those are not errors.
- Errors that have already been rewritten. Rewriting a rewrite compounds drift
  away from the original evidence.
- Security-relevant failures (authentication, authorisation, key material).
  Escalate those to a human rather than paraphrasing them for a customer.

## Procedure

1. **Read the trace bottom-up.** The final line names the exception and carries
   the message. The frames above it show the call path. The topmost frame is
   usually the least interesting.
2. **Identify what actually failed** — the component and the operation. In
   `paygate.errors.GatewayTimeout` raised from a `submit` call, the component is
   the payment gateway client and the operation is submitting a charge.
3. **Extract only stated facts.** Timeouts, limits, counts and identifiers that
   appear literally in the text. A trace saying "no response in 30s" tells you
   the timeout was 30 seconds. It does not tell you why.
4. **Determine the customer-visible consequence.** Did the action succeed, fail,
   or is its state unknown? For payment timeouts the honest answer is usually
   "unknown, and it must be checked before retrying" — never assert that a
   customer was not charged unless the trace proves it.
5. **Write three lines** in the output format below.
6. **Re-read against the trace.** Delete any clause you cannot point to a line
   for.

## Output format

Exactly three labelled lines, nothing else:

```
What happened: <one sentence, plain language>
What it means: <one sentence, the customer-visible consequence>
What to say: <one sentence the agent can read aloud verbatim>
```

Maximum 30 words per line.

## Constraints

- No file paths, line numbers, function names, exception class names or vendor
  product names.
- No inferred root cause, blast radius, frequency or history. The trace is a few
  lines long; it does not know those things.
- Never blame the customer.
- "What to say" must be safe to read to a paying customer: no internal system
  names, no admission of liability.
- If the input is empty, unreadable, or not an error trace, output exactly:
  `Data unavailable`

## Worked example

Input:

```
Traceback (most recent call last):
  File "/app/services/billing.py", line 214, in charge_customer
    response = gateway.submit(payload, timeout=self.timeout)
  File "/app/vendor/paygate/client.py", line 88, in submit
    raise GatewayTimeout(f"no response in {timeout}s")
paygate.errors.GatewayTimeout: no response in 30s
```

Output:

```
What happened: The payment step did not get a reply within 30 seconds and stopped waiting.
What it means: We do not yet know whether the payment went through, so it must be checked before anyone tries again.
What to say: Your payment is still being confirmed - please do not retry yet, and I will check the status now.
```

Note what the example does **not** say: it does not claim the customer was not
charged, does not name the vendor, and does not guess why the gateway was slow.
None of that is in the trace.

## Failure modes to avoid

| Tempting output | Why it is wrong |
|---|---|
| "The payment provider was down." | The trace shows a timeout, not an outage. |
| "Your card was declined." | A timeout is not a decline. Opposite remediation. |
| "This is a known issue affecting some users." | Frequency is not in the trace. |
| "Error: GatewayTimeout after 30s in billing.py:214" | That is the input, reformatted. The agent still cannot read it. |
