# Part VI — Production Discipline

Part V was what you save. This part is what you do with it once a pipeline is running
against real tickets and real documents — versioning a whole chain instead of one
prompt, reasoning about the cost and latency of four round trips instead of one, and
catching the failure mode that is unique to pipelines: every stage individually correct,
the composed answer wrong anyway.

---

## 6.1 Pipelines as code

Chapter 1 §6.1 gave four rules for one prompt: live in files, be versioned, be reviewed,
stay separate from application logic. All four still apply per stage. One rule is new,
and it is the rule this section is about:

> **A stage's prompt version is part of the pipeline's own identity.** The manifest
> (§5.3) is what makes a pipeline's behavior reconstructable — and a manifest that still
> says `1.0.0` while one of its stages quietly points at prompt `1.1.0` is a manifest that
> lies. Bumping any stage's prompt version bumps the pipeline version too.

```python
def bump_pipeline_version(manifest: dict, changed_stage: str, new_prompt_version: str) -> dict:
    """A stage's prompt version is part of the pipeline's own identity (§5.3) — changing
    it always bumps the pipeline version, never just the one stage entry."""
    for spec in manifest["stages"]:
        if spec["name"] == changed_stage:
            spec["prompt_version"] = new_prompt_version
    major, minor, patch = (int(part) for part in manifest["version"].split("."))
    manifest["version"] = f"{major}.{minor + 1}.0"
    return manifest


risk_report_manifest = bump_pipeline_version(risk_report_manifest, "summarize", "1.1.0")
print(risk_report_manifest["version"])
```

### Pipeline-level changelog

One `prompts/CHANGELOG.md` per prompt file was Chapter 1's convention (§6.1 there). A
pipeline needs one more changelog, at the manifest's own level, because "stage 2's
prompt got a MINOR bump" and "the pipeline's own behavior changed" are different claims —
the second one is what a downstream consumer of the pipeline's *final* output cares about.

```markdown
## risk_report 1.1.0 — 2026-08-14 — @tmudgal
**Type:** MINOR (pipeline-level — triggered by a stage bump, not a structural change)
**Change:** summarize stage prompt bumped 1.0.0 -> 1.1.0 (tighter number-preservation rule).
**Downstream:** none — output contract (ExecutiveSummary schema) unchanged.
**Eval:** evals/golden/risk_report_e2e.jsonl — 27/30 -> 29/30.

## incident_response 2.0.0 — 2026-07-30 — @tmudgal
**Type:** MAJOR — breaking
**Change:** ROUTE rule's urgency threshold raised from >=5 to >=4 (§2.5).
**Downstream:** on-call runbook's escalation volume assumptions must be updated first.
**Eval:** evals/golden/incident_response_e2e.jsonl — routing exact-match 0.88 -> 0.95.
```

### Code review for a stage change

The question from the task header — "does the whole pipeline need a version bump when
one stage's prompt changes?" — has one answer: **yes, always**, per the manifest rule
above. The review checklist Chapter 1 gave per-prompt (§6.1 there) still applies to the
one file that changed; add exactly one pipeline-level question on top of it:

- [ ] Does the manifest's own `version` reflect this stage change, not just the stage's
      own `prompt_version` field?
- [ ] Does the CHANGELOG entry name which stage changed and cite the end-to-end eval
      delta (§6.3), not just that stage's isolated eval delta?

---

## 6.2 Cost and latency of a whole pipeline

Chapter 1 §1.6 gave the sum-of-stages math: pipeline cost is the sum of every stage's
token cost, pipeline latency (absent concurrency) is the sum of every stage's latency.
`StageLog` (§5.2) already collects exactly the numbers that sum needs.

### Finding the dominant stage

```python
def cost_breakdown(logs: list[StageLog]) -> None:
    for entry in logs:
        total = entry.input_tokens + entry.output_tokens
        bar = "#" * max(1, total // 20)
        print(f"{entry.stage:16} {bar} {total:5} tok  ({entry.elapsed_ms:.0f} ms)")


cost_breakdown(run_logs)
```

```
PER-STAGE TOKENS — Risk Report Pipeline, one run against the incident memo

  translate       ############################################  ~610 tok   <- dominant
  summarize       ###############                                ~210 tok
  extract_risks   #######                                         ~95 tok
  format_bullets                                                    0 tok   (plain code)
```

`translate` dominates because it is the only stage that reads the *full* source document
— every later stage reads something a previous stage already compressed. That is the
general shape: **the stage closest to the raw input is usually the expensive one**, and
it is worth checking before assuming the "smartest-sounding" stage (extraction, in this
pipeline) is the costly one.

Three options, in the order §5.4 in Chapter 1 recommends trying them:

| Option | When it applies |
|---|---|
| **Trim the input** | The dominant stage reads more of the source than the task needs — pre-filter in Python before the call (Ch1 §6.2). |
| **Lower `thinking_level`** | The dominant stage is doing fact-transfer, not reasoning. Translation is a good candidate; extraction with a nuanced severity judgment may not be. |
| **Reconsider the stage boundary** | The stage exists mainly to shrink text for the next one. If two adjacent stages are both cheap "reformatting" steps with no independent value, ask whether they should be one call — but weigh that against losing an independently testable seam (§1.3). |

```python
def translate_step_low_thinking(source_text: str) -> tuple[TranslatedDoc, dict[str, int]]:
    """Same seam contract as translate_step (§5.2) — translation is fact-transfer,
    not reasoning, so a lower thinking_level is the first lever to try, not caching
    or trimming."""
    interaction = client.interactions.create(
        model=MODEL,
        system_instruction=TRANSLATE_SYSTEM,
        input=source_text,
        generation_config={"thinking_level": "low"},
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": TranslatedDoc.model_json_schema(),
        },
        store=False,
    )
    doc = TranslatedDoc.model_validate_json(interaction.output_text)
    usage = {
        "input_tokens": interaction.usage.total_input_tokens,
        "output_tokens": interaction.usage.total_output_tokens,
    }
    return doc, usage
```

### Total latency is a floor, not a target

Stages run sequentially by definition in this blueprint — that is the "fixed" in Fixed
Assembly Line. A 4-stage pipeline is **at minimum four round trips**, paid one after
another:

```
LATENCY, ONE PIPELINE RUN — four stages, strictly sequential

  classify   ████████████████████████                800 ms
  route      ▏                                           0.1 ms  (no call)
  rewrite    ████████████████████████████████████     1100 ms
  log_summary███████████████████████████████            950 ms
             └──────────────────────────────────────┘
                     total ≈ 2850 ms, floor

  Nothing here overlaps. Stage N+1 cannot start until Stage N's validated
  output exists — that dependency is the whole point of "fixed order."
```

Shortening any one stage (lower `thinking_level`, smaller input, Flash instead of Pro —
Ch1 §6.3's levers, applied per stage) lowers the floor. **Running independent stages
concurrently would lower it faster, and this chapter deliberately does not build that.**
The moment two stages no longer have a strict producer/consumer relationship, keeping
them in one fixed sequence is a choice, not a requirement — and once you want the runtime
to decide which stages can overlap or reorder based on what it sees, you are designing
Blueprint 4 (The Autopilot Worker), not extending this one. Name it, do not build it here.

---

## 6.3 Evaluating a whole pipeline

Chapter 1 §6.4 gave the golden-set-plus-scorer pattern for one call. Apply it per stage
first — a golden set for `classify_step` alone is Chapter 1's `ticket_classifier.jsonl`,
unchanged, run against `classify_step` directly. That catches most regressions cheaply.

It is not sufficient by itself. A pipeline can have every stage individually pass its own
golden set and still produce the wrong final answer, because stages **compose**. The
concrete failure mode in Pipeline B: `classify_step` correctly identifies urgency 5, and
`route_step`'s `if` correctly escalates — both pass their own evals — but `rewrite_step`'s
repurposed prompt (§5.2's honest callout: the body was written for a stack trace, not a
triage note) leaks the internal `category`/`reason` fields into `customer_message`
because the boundary rule about "untrusted data" was never tuned for this input shape.
No per-stage eval catches that; only running the whole chain does.

```
              per-stage golden sets                    end-to-end integration eval
        ┌───────────────────────────────┐        ┌───────────────────────────────┐
        │ evals/golden/classify.jsonl    │        │ INCIDENT_GOLDEN                │
        │ evals/golden/rewrite.jsonl      │──────▶│  ticket -> expected final route │
        │ evals/golden/log_summary.jsonl  │  each  │  runs classify->route->rewrite  │
        └───────────────────────────────┘  stage  │  ->log_summary end to end       │
                     │                     passes  └───────────────────────────────┘
                     ▼                    isolation              │
        cheap, fast, one call per case                           ▼
        catches most regressions early        catches composition bugs — every stage
                                               can be individually correct and still
                                               combine into the wrong final answer
```

A minimal, runnable end-to-end eval for Pipeline B, checking only the property that
matters most for an on-call runbook — did the right tickets get escalated:

```python
INCIDENT_GOLDEN = [
    {"id": "ir-001", "ticket": ticket_text, "expected_route": "escalate"},
    {
        "id": "ir-002",
        "ticket": "Any update on when dark mode is landing? Not urgent, just curious.",
        "expected_route": "auto",
    },
    {
        "id": "ir-003",
        "ticket": "I'm locked out of my account and need to run payroll in an hour.",
        "expected_route": "escalate",
    },
]


def run_incident_response_eval() -> float:
    passed = 0
    for case in INCIDENT_GOLDEN:
        state, _ = incident_response_pipeline.run(IncidentRunState(ticket=case["ticket"]))
        ok = state.route == case["expected_route"]
        passed += ok
        if not ok:
            print(f"FAIL {case['id']}: expected {case['expected_route']}, got {state.route}")
    print(f"incident_response end-to-end: {passed}/{len(INCIDENT_GOLDEN)}")
    return passed / len(INCIDENT_GOLDEN)


run_incident_response_eval()
```

`expected_route` is deterministic — exact match, free, trusted completely, exactly per
Chapter 1 §6.4's scoring-method hierarchy. The end-to-end eval does not need an
LLM-as-judge here because the property under test (did routing land correctly) is a
fixed label, not a subjective quality judgment. A pipeline whose *final* stage produces
free-form prose (the Risk Report Pipeline's bulleted list) would reuse Chapter 1's judge
pattern (§6.4 there) at the end-to-end level instead.

---

## 6.4 Observability

Chapter 1 §6.1 logged one call's `prompt_id`, `prompt_version`, tokens and latency. A
pipeline needs the same fields per stage, plus the one field that lets them be
reassembled afterward: `run_id` (§5.5).

```python
import logging
import json

log = logging.getLogger("pipeline")


def log_stage_entries(logs: list[StageLog], pipeline_name: str) -> None:
    for entry in logs:
        record = {
            "pipeline": pipeline_name,
            "run_id": entry.run_id,
            "stage": entry.stage,
            "prompt_version": entry.prompt_version,
            "elapsed_ms": round(entry.elapsed_ms, 1),
            "input_tokens": entry.input_tokens,
            "output_tokens": entry.output_tokens,
        }
        log.info("pipeline_stage", extra=record)
        print(json.dumps(record))  # illustrative here; production emits via `log` only


log_stage_entries(run_logs, "risk_report")
log_stage_entries(incident_logs, "incident_response")
```

One JSON object per stage, `run_id` as the correlation key. Redact ticket/document text
before logging, exactly as Chapter 1 §5.7 requires — the fields above are all metadata,
never the payload.

```
logs/pipeline.jsonl  — unordered, append-only, many runs interleaved

  {"run_id":"7e2f...","stage":"classify",   "elapsed_ms":812, "prompt_version":"1.0.0"}
  {"run_id":"a91c...","stage":"classify",   "elapsed_ms":790, "prompt_version":"1.0.0"}
  {"run_id":"7e2f...","stage":"route",      "elapsed_ms":0.1, "prompt_version":null}
  {"run_id":"a91c...","stage":"route",      "elapsed_ms":0.1, "prompt_version":null}
  {"run_id":"7e2f...","stage":"rewrite",    "elapsed_ms":1105,"prompt_version":"1.0.0"}
  {"run_id":"a91c...","stage":"rewrite",    "elapsed_ms":980, "prompt_version":"1.0.0"}
  {"run_id":"7e2f...","stage":"log_summary","elapsed_ms":940, "prompt_version":"1.0.0"}
        │
        ▼  filter run_id = "7e2f...", sort by arrival order
  classify(812ms) -> route(0.1ms) -> rewrite(1105ms) -> log_summary(940ms)
  one full, ordered trace of a single pipeline run — reconstructed entirely from
  logs written by four unrelated log.info() calls, hours or weeks after the fact
```

That reconstruction is the entire payoff of §5.5's `run_id`: nothing about the logging
call itself needs to know it is part of a pipeline. `Pipeline.run` generates the ID once;
every stage's log line inherits it; a query at incident-review time is a `WHERE run_id =
...` and a sort.

---

## Five things worth actually remembering

1. **A stage's prompt version is part of the pipeline's own version.** Bump the manifest
   whenever any stage's prompt bumps — a manifest that lags a stage change is a manifest
   that lies about what shipped.
2. **The stage closest to the raw input is usually the expensive one**, not the
   smartest-sounding stage. Measure with `StageLog` before optimising by intuition.
3. **Sequential order is a floor on latency, not a suggestion.** Four stages are at least
   four round trips; overlapping them means abandoning strict order, which is Blueprint 4
   territory, not this one.
4. **Per-stage evals catch regressions; only an end-to-end eval catches composition
   bugs.** Every stage can individually pass and the pipeline can still be wrong.
5. **`run_id` is the only correlation key a pipeline's logs need.** One line per stage,
   same key, reassembled into a timeline whenever someone has to ask "what happened on
   this one run."

---

**Next:** [Part VII — Advanced](./07-advanced.md)
