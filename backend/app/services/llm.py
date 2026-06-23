"""LLM layer (PydanticAI).

The provider is swappable via the `LLM_MODEL` config (a PydanticAI model string
like `anthropic:claude-haiku-4-5`). Agents are defined here so tests can mock
the model with `agent.override(model=TestModel(...))` — no network, no API key.
"""

import os
from functools import lru_cache

from pydantic_ai import Agent

from app.config import settings
from app.schemas.profile import NonprofitProfile

EXTRACTION_SYSTEM_PROMPT = """\
You extract a structured nonprofit profile from a source document for funders.

For EVERY field:
- Set `value` only if the document supports it; otherwise leave it null.
- Set `status`:
  - "extracted" when the value is stated (near-verbatim) in the document,
  - "inferred" when you reasoned it from the document but it isn't stated outright,
  - leave the value null (status becomes "missing") when the document doesn't say.
- Set `confidence` in [0,1] — high for explicit statements, lower for inferences.
- Set `source_quote` to a short verbatim snippet from the document supporting the value.
- Do NOT set `source_chunk_id` (the system resolves it).

Do not invent facts. A missing field is expected and useful — it's better to leave
something null than to guess. Be conservative with confidence on inferred values.
"""


def _ensure_provider_env() -> None:
    """Bridge configured secrets into the env vars provider SDKs read.

    pydantic-settings loads keys from .env into `settings`; the Anthropic SDK
    reads `ANTHROPIC_API_KEY` from the process environment. Bridge them so the
    swappable model string keeps working without hardcoding the provider here.
    """
    if settings.anthropic_api_key and not os.getenv("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


@lru_cache
def extraction_agent() -> Agent[None, NonprofitProfile]:
    """Agent that turns source text into a validated NonprofitProfile."""
    _ensure_provider_env()
    return Agent(
        settings.llm_model,
        output_type=NonprofitProfile,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        model_settings={"max_tokens": settings.llm_max_tokens},
        retries=2,
    )
