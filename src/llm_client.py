"""Shared OpenAI client helpers."""

import json
import os
import re
from typing import Any

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL

DEFAULT_LLM_MODEL = OPENAI_MODEL
MAX_TEXT_CHARS = 120_000
_MARKDOWN_FENCE = re.compile(r"^```(?:\w+)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL))


def truncate_text(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    return text[:max_chars]


def parse_llm_json(text: str) -> Any:
    """Parse JSON from an LLM response, tolerating optional markdown fences."""
    cleaned = text.strip()
    match = _MARKDOWN_FENCE.match(cleaned)
    if match:
        cleaned = match.group(1).strip()
    return json.loads(cleaned)


def call_llm_json(system_prompt: str, user_prompt: str) -> Any:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Configure .env before running the pipeline."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    model = get_openai_model()

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise RuntimeError(
            f"LLM request failed with model '{model}'. "
            f"You can change OPENAI_MODEL in .env. Error: {exc}"
        ) from exc

    return parse_llm_json(response.output_text)
