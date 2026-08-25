# `skills/` — read this before you copy anything out of here

## The short version

**`SKILL.md` is not a Smart Intern feature.**

Skills and `AGENTS.md` are a **managed-agent** capability in the Gemini API —
the Antigravity agent surface. They are mounted into an agent's environment and
consumed by a long-running agent that has tools, files and a loop.

A Blueprint 1 system has none of those things. One prompt in, one response out.
There is nothing running that could discover a skill file, decide it is
relevant, and load it.

So this directory is **illustrative**. It shows you the real format, correctly,
so that when you reach Blueprint 4 (Autopilot Worker) or Blueprint 5 (Connected
Boardroom) you recognise it. Nothing in `examples/` imports it, and nothing in
`examples/` could.

## Why the confusion is worth clearing up

"Skills" has become a fashionable word, and it is easy to read a tutorial,
create a `SKILL.md`, point a `client.interactions.create()` call at your project
directory and expect something to happen. Nothing will. The single-shot API does
not read your filesystem. There is no mechanism by which a plain
`interactions.create()` call becomes aware that this file exists.

If you have written a `SKILL.md` and your single-shot calls seem to be obeying
it, what is actually happening is that you pasted its content into a system
instruction at some point, or your IDE agent is injecting it. The API is not
reading the file.

## What the real thing looks like

Per the Gemini API custom-agents documentation, for **managed agents only**:

```
.agents/
├── AGENTS.md                      # always-on project context for the agent
└── skills/
    └── <skill-name>/
        └── SKILL.md               # a capability the agent can load on demand
```

`SKILL.md` is markdown with YAML frontmatter carrying `name` and `description`:

```markdown
---
name: slide-maker
description: Builds presentation decks from an outline.
---

<markdown body: the procedure the agent should follow>
```

Skills are mounted into an agent's environment when the agent is created:

```python
client.agents.create(
    id="...",
    base_agent="antigravity-preview-05-2026",
    system_instruction="...",
    base_environment={
        "type": "remote",
        "sources": [
            {
                "type": "inline",
                "target": ".agents/skills/error-rewriter/SKILL.md",
                "content": "<file contents>",
            }
        ],
    },
)
```

Source types are `inline`, `repository` (git) and GCS.

Facts worth knowing before you plan around this:

- `antigravity-preview-05-2026` is the only supported `base_agent`.
- It is **preview** status. Preview APIs change.
- Maximum 1000 agents.
- `system_instruction` and `AGENTS.md` are **additive** — both apply. Neither
  overrides the other, so contradictions between them are your problem.

Reference: https://ai.google.dev/gemini-api/docs/custom-agents

## The Blueprint 1 equivalent

For a genuine single-shot task, the client-side equivalent of a skill is
mundane and it already exists in this repository:

| Managed agent | Smart Intern |
|---|---|
| `SKILL.md` loaded by the agent at runtime | A **system instruction** you pass on every call |
| `AGENTS.md` always-on project context | The same system instruction, or a prompt file |
| Agent decides which skill applies | **You** decide, in your own code, before the call |
| Skill discovery | `prompts/<task>.system.md` + a loader |

That is what `prompts/error_rewriter.system.md` and
`examples/10_prompt_files.py` are. A file on disk, versioned, loaded by your
code, passed as `system_instruction=`. Same benefit — reviewable, diffable,
versioned prompt content — without pretending the model is doing something it
is not.

The routing decision is the real difference. A managed agent picks its own
skill. In Blueprint 1 you write:

```python
system_instruction = load_prompt("error_rewriter.system.md").body
```

You made the choice. That is not a limitation to work around; it is the entire
definition of the blueprint. The moment you want the model to choose which
instruction set applies, you have left Blueprint 1.

## What is in here

- `error-rewriter/SKILL.md` — a correctly formatted example skill, in the real
  managed-agent format, carrying a header note repeating this warning.

Read it for the format. Do not wire it into a single-shot call.
