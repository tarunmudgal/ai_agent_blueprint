"""06 — A pipeline manifest: stage name -> prompt name/version/model.

Reuses Chapter 1's frontmatter parser (examples/10_prompt_files.py there)
unchanged, because the frontmatter convention here is the identical flat
`key: value` block - no reason to write a second parser.

Demonstrates:
  * loading the actual prompt files the Incident Response Pipeline uses
    from prompts/ on disk, not from a hardcoded string
  * building a small manifest that answers "which prompt version produced
    this pipeline run" for every stage in one place
  * Stage 2 (ROUTE) appearing in the manifest with no prompt file at all,
    because it is not a model call

What to look for in the output:
  1. Three of the four rows point at prompt files reused byte-for-byte
     from Chapter 1 - the manifest is what lets you say "we are running
     ticket_classifier v2.0.1" in an incident review six months from now.
  2. The ROUTE row has name/version/model all reported as "n/a (plain
     code, no prompt file)" - this is not a bug in the manifest, it is the
     manifest telling the truth about a stage that is not an LLM call.
  3. The final printed table is what you would log, or attach to a
     postmortem, alongside every pipeline run.

Run:  python3 examples/06_pipeline_manifest.py
"""
import re

from dataclasses import dataclass, field
from pathlib import Path

from _common import MODEL, banner

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Matches a single-brace {placeholder} token with a bare identifier inside.
# Unused by any prompt in this chapter (none of them use templates), kept
# only because it is part of the parser being reused verbatim from Ch1.
PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PromptError(RuntimeError):
    """Raised when a prompt file is malformed."""


@dataclass
class Prompt:
    """A prompt file, split into metadata and body. Mirrors Ch1's 10_prompt_files.py."""

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

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = parse_frontmatter(parts[1])
            body = parts[2]

    return Prompt(path=path, body=body.strip(), meta=meta)


@dataclass
class ManifestRow:
    """One line of the pipeline manifest: a stage, and what produced it."""

    stage: str
    prompt_name: str
    prompt_version: str
    prompt_model: str


def build_incident_response_manifest() -> list[ManifestRow]:
    """The manifest for the Incident Response Pipeline's four stages."""
    classify_prompt = load_prompt("ticket_classifier.system.md")
    rewrite_prompt = load_prompt("error_rewriter.system.md")
    log_prompt = load_prompt("summarizer.system.md")

    rows = [
        ManifestRow(
            stage="classify",
            prompt_name=classify_prompt.name,
            prompt_version=classify_prompt.version,
            prompt_model=classify_prompt.model,
        ),
        ManifestRow(
            stage="route",
            prompt_name="n/a (plain code, no prompt file)",
            prompt_version="n/a",
            prompt_model="n/a",
        ),
        ManifestRow(
            stage="rewrite",
            prompt_name=rewrite_prompt.name,
            prompt_version=rewrite_prompt.version,
            prompt_model=rewrite_prompt.model,
        ),
        ManifestRow(
            stage="log_summary",
            prompt_name=log_prompt.name,
            prompt_version=log_prompt.version,
            prompt_model=log_prompt.model,
        ),
    ]

    # Flag any prompt evaluated against a different model than the one
    # this chapter actually calls - same check Ch1's describe() makes.
    for prompt in (classify_prompt, rewrite_prompt, log_prompt):
        if prompt.model not in ("unspecified", MODEL):
            print(f"  NOTE: {prompt.name} was written for {prompt.model}, "
                  f"but we are calling {MODEL}. Re-run 05_pipeline_eval.py.")

    return rows


def print_manifest(rows: list[ManifestRow]) -> None:
    header = f"{'stage':<14}{'prompt_name':<20}{'version':<12}{'model'}"
    print(header)
    print("-" * 74)
    for row in rows:
        print(f"{row.stage:<14}{row.prompt_name:<20}{row.prompt_version:<12}"
              f"{row.prompt_model}")


def main() -> None:
    banner("Incident Response Pipeline manifest")
    rows = build_incident_response_manifest()
    print_manifest(rows)

    banner("Why this exists")
    print(
        "When a pipeline run goes wrong, the manifest is the difference\n"
        "between 'the classifier misbehaved' and 'ticket_classifier v2.0.1\n"
        f"misbehaved, calling {MODEL}, on 2026-08-30'. Log this table, or\n"
        "something like it, alongside every real pipeline run."
    )


if __name__ == "__main__":
    main()
