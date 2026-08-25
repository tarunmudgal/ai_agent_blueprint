"""10 — Prompts as files, not string literals.

Loads a prompt from prompts/ on disk, parses its YAML frontmatter, injects
variables into the user template, and calls the API.

Demonstrates:
  * externalising prompts so they can be diffed, reviewed and versioned
  * a frontmatter parser with no extra dependency
  * template rendering that FAILS LOUDLY on an unfilled placeholder

What to look for in the output:
  1. The metadata block. Every response you keep should be logged with the
     prompt version that produced it. Without that, "the classifier got
     worse last week" is unanswerable.
  2. The rendered user content, with {stack_trace} replaced.
  3. The deliberate failure at the end: rendering with a missing variable
     raises instead of quietly shipping the literal token "{stack_trace}"
     to the model. Silent substitution failure is a genuinely common
     production bug and it is embarrassing to debug.

Why no PyYAML: the frontmatter here is flat key/value by design, so a
20-line parser covers it and requirements.txt stays at three packages. If
you ever need nested YAML, add the dependency - do not extend this parser.

Run:  python3 examples/10_prompt_files.py
"""


import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    banner,
    get_client,
    report_usage,
    stack_trace,
)

# prompts/ sits next to examples/, one level up from this file.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Matches a single-brace {placeholder} token with a bare identifier inside.
PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PromptError(RuntimeError):
    """Raised when a prompt file is malformed or a variable is missing."""


@dataclass
class Prompt:
    """A prompt file, split into metadata and body."""

    path: Path
    body: str
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.meta.get("name", self.path.name)

    @property
    def version(self) -> str:
        return self.meta.get("version", "unversioned")

    @property
    def model(self) -> str:
        return self.meta.get("model", "unspecified")

    @property
    def updated(self) -> str:
        return self.meta.get("updated", "unknown")

    @property
    def description(self) -> str:
        return self.meta.get("description", "")

    def placeholders(self) -> list[str]:
        """Every {token} in the body, in order of first appearance."""
        seen: list[str] = []
        for match in PLACEHOLDER_RE.finditer(self.body):
            if match.group(1) not in seen:
                seen.append(match.group(1))
        return seen

    def render(self, **variables: str) -> str:
        """Substitute {placeholders}. Raise if any is left unfilled.

        Deliberately not str.format(): prompt bodies routinely contain
        braces in code samples and JSON examples, and format() would choke
        on them or, worse, silently eat them.
        """
        required = self.placeholders()
        missing = [key for key in required if key not in variables]
        if missing:
            raise PromptError(
                f"{self.name} v{self.version}: missing variable(s) "
                f"{missing}. Required: {required}"
            )

        unused = [key for key in variables if key not in required]
        if unused:
            # Not fatal, but it means the caller and the template disagree,
            # which is usually a rename that half-landed.
            print(f"  warning: variable(s) {unused} passed but not used by "
                  f"{self.name}")

        rendered = self.body
        for key in required:
            rendered = rendered.replace("{" + key + "}", str(variables[key]))
        return rendered


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a flat `key: value` YAML block. No nesting, no lists."""
    meta: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip("'\"")
    return meta


def load_prompt(filename: str) -> Prompt:
    """Read prompts/<filename>, split frontmatter from body."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise PromptError(f"no such prompt file: {path}")

    text = path.read_text(encoding="utf-8")

    meta: dict[str, str] = {}
    body = text

    # Frontmatter is the block between the first two --- fences, and only
    # counts if the file opens with one.
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = parse_frontmatter(parts[1])
            body = parts[2]

    return Prompt(path=path, body=body.strip(), meta=meta)


def describe(prompt: Prompt) -> None:
    """Print the metadata you should be logging with every response."""
    print(f"  name       : {prompt.name}")
    print(f"  version    : {prompt.version}")
    print(f"  model      : {prompt.model}")
    print(f"  updated    : {prompt.updated}")
    print(f"  description: {prompt.description}")
    print(f"  body chars : {len(prompt.body)}")
    placeholders = prompt.placeholders()
    print(f"  placeholders: {placeholders if placeholders else 'none'}")

    # A prompt evaluated against one model and run against another is a
    # silent risk, so say so out loud.
    if prompt.model not in ("unspecified", MODEL):
        print(f"  NOTE: this prompt was written for {prompt.model}, "
              f"but we are calling {MODEL}. Re-run the evals.")


def main() -> None:
    banner("Loading prompts from disk")

    system_prompt = load_prompt("error_rewriter.system.md")
    user_prompt = load_prompt("error_rewriter.user.md")

    print("SYSTEM:")
    describe(system_prompt)
    print("\nUSER TEMPLATE:")
    describe(user_prompt)

    banner("Rendered user content")
    rendered = user_prompt.render(stack_trace=stack_trace)
    print(rendered)

    banner("Calling the model")
    client = get_client()
    interaction = client.interactions.create(
        model=MODEL,
        input=rendered,
        system_instruction=system_prompt.body,
        generation_config={"thinking_level": "low"},
        store=STORE_DEFAULT,
    )
    print(interaction.output_text)
    print()
    report_usage(interaction, label="prompt-file")

    # This is the line you would write to your log store, and it is the
    # entire reason for the frontmatter.
    print(
        f"\nlog record -> system={system_prompt.name}@{system_prompt.version} "
        f"user={user_prompt.name}@{user_prompt.version} model={MODEL}"
    )

    banner("Failing loudly on a missing variable")
    try:
        user_prompt.render()  # no stack_trace supplied
    except PromptError as exc:
        print(f"  PromptError raised, as it should be:\n    {exc}")
    else:
        print("  no error raised - the loader is broken")

    banner("Takeaway")
    print(
        "Once prompts are files, three things become possible that were not\n"
        "before: a code review that shows the actual wording change, a log\n"
        "line that pins an output to a prompt version, and a non-engineer\n"
        "editing the prompt without touching Python."
    )


if __name__ == "__main__":
    main()
