"""01 — The Risk Report Pipeline: the article's own example, end to end.

Four fixed stages, one document, no branching:

    document_text -> translate -> summarize -> extract risks -> format bullets

Demonstrates:
  * a four-stage Pipeline built from _common.Stage / _common.Pipeline
  * each stage is its own single-shot client.interactions.create() call,
    store=False, exactly like a Blueprint-1 Smart Intern
  * the seam between stages is a plain Python string for the first two
    stages, and a validated Pydantic list for the last two - a seam does
    not have to be structured data to be a real contract
  * the model's own output feeding the NEXT PROMPT is fine; the model's
    output deciding WHICH STAGE RUNS NEXT would not be (see 02 and the
    chapter's own discussion of this line)

What to look for in the output:
  1. Each stage prints its own output as it completes, so you can see the
     seam: stage N's full output is exactly what stage N+1 receives.
  2. The final bulleted Markdown list is the only thing a stakeholder would
     actually read - everything before it is scaffolding to get there
     reliably.
  3. Token cost accumulates across four calls, not one. A pipeline's real
     cost is the sum of its stages, and it is easy to under-estimate until
     you print each one.

Run:  python3 examples/01_risk_report_pipeline.py
"""
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    MODEL,
    STORE_DEFAULT,
    Pipeline,
    Stage,
    banner,
    document_text,
    get_client,
    report_usage,
    rule,
)
from pydantic import BaseModel, Field, ValidationError  # noqa: E402

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_system_prompt(filename: str) -> str:
    """Read a prompt file and strip its YAML frontmatter, keeping the body.

    A minimal version of the parser in 06_pipeline_manifest.py - here we
    only need the body, not the metadata.
    """
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


TRANSLATE_PROMPT = load_system_prompt("translate.system.md")
SUMMARIZER_PROMPT = load_system_prompt("summarizer.system.md")
EXTRACT_RISKS_PROMPT = load_system_prompt("extract_risks.system.md")
FORMAT_BULLETS_PROMPT = load_system_prompt("format_bullets.system.md")

TARGET_LANGUAGE = "Spanish"


class Risk(BaseModel):
    """The contract between the extraction stage and the formatting stage."""

    description: str = Field(description="One sentence describing the risk.")
    severity: str = Field(description="One of: low, medium, high.")


class RiskList(BaseModel):
    """Structured output wrapper - a bare JSON list has no schema of its own."""

    risks: list[Risk] = Field(default_factory=list)


def make_translate_stage(client: Any) -> Stage:
    """Stage 1 — translate the source document to TARGET_LANGUAGE."""

    def run(text: str) -> str:
        interaction = client.interactions.create(
            model=MODEL,
            input=text,
            system_instruction=TRANSLATE_PROMPT.replace(
                "the target language", TARGET_LANGUAGE
            ),
            generation_config={"thinking_level": "low"},
            store=STORE_DEFAULT,
        )
        report_usage(interaction, label="translate")
        return interaction.output_text

    return Stage(name="translate", run=run)


def make_summarize_stage(client: Any) -> Stage:
    """Stage 2 — reduce the translation to an executive summary."""

    def run(translated_text: str) -> str:
        interaction = client.interactions.create(
            model=MODEL,
            input=translated_text,
            system_instruction=SUMMARIZER_PROMPT,
            generation_config={"thinking_level": "low"},
            store=STORE_DEFAULT,
        )
        report_usage(interaction, label="summarize")
        return interaction.output_text

    return Stage(name="summarize", run=run)


def make_extract_risks_stage(client: Any) -> Stage:
    """Stage 3 — pull every risk out of the summary as structured data."""

    def run(summary: str) -> RiskList:
        interaction = client.interactions.create(
            model=MODEL,
            input=summary,
            system_instruction=EXTRACT_RISKS_PROMPT,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": RiskList.model_json_schema(),
            },
            generation_config={"thinking_level": "low"},
            store=STORE_DEFAULT,
        )
        report_usage(interaction, label="extract_risks")
        try:
            return RiskList.model_validate_json(interaction.output_text)
        except ValidationError as exc:
            raise ValueError(
                f"extract_risks returned an off-contract payload: {exc}"
            ) from exc

    return Stage(name="extract_risks", run=run, output_schema=RiskList)


def make_format_bullets_stage(client: Any) -> Stage:
    """Stage 4 — render the structured risks as a bulleted Markdown list."""

    def run(risk_list: RiskList) -> str:
        # The model receives structured JSON as its input text - the seam
        # is still "a string over the wire", but the string is now a
        # validated, schema-shaped payload rather than free prose.
        payload = risk_list.model_dump_json(indent=2)
        interaction = client.interactions.create(
            model=MODEL,
            input=payload,
            system_instruction=FORMAT_BULLETS_PROMPT,
            generation_config={"thinking_level": "low"},
            store=STORE_DEFAULT,
        )
        report_usage(interaction, label="format_bullets")
        return interaction.output_text

    return Stage(name="format_bullets", run=run, input_schema=RiskList)


def build_pipeline(client: Any) -> Pipeline:
    """Assemble the four fixed stages in their one, unchanging order."""
    return Pipeline(
        stages=[
            make_translate_stage(client),
            make_summarize_stage(client),
            make_extract_risks_stage(client),
            make_format_bullets_stage(client),
        ]
    )


def main() -> None:
    client = get_client()
    pipeline = build_pipeline(client)

    banner("Risk Report Pipeline — running all four stages")
    print(f"target language: {TARGET_LANGUAGE}")

    value: Any = document_text
    for stage in pipeline.stages:
        rule()
        print(f"stage: {stage.name}")
        try:
            value = stage.run(value)
        except Exception as exc:  # noqa: BLE001 - demonstration, not a library
            print(f"HALTED at stage {stage.name!r}: {exc}")
            return
        print(value if isinstance(value, str) else value.model_dump_json(indent=2))

    banner("Final bulleted risk list")
    print(value)


if __name__ == "__main__":
    main()
