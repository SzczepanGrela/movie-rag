import asyncio
from typing import Protocol

from google import genai
from google.genai import errors, types
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from lib.config import EtlSettings
from lib.schema_c import (
    CharacterOut,
    PlotVariantsOut,
    QuoteOut,
    SceneOut,
    SchemaCOut,
    build_prompt,
)

GEMINI_MAX_ATTEMPTS = 3


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, errors.APIError):
        code = exc.code
        return code == 429 or (code is not None and code >= 500)
    return False


class GeminiClient(Protocol):
    def generate(
        self, *, title: str, year: int | None, source_text: str
    ) -> tuple[SchemaCOut, int]: ...


class VertexGeminiClient:
    def __init__(self, settings: EtlSettings) -> None:
        self._client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        self._model = settings.gemini_model
        self._config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SchemaCOut,
        )

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(GEMINI_MAX_ATTEMPTS),
        reraise=True,
    )
    def _generate_content(self, prompt: str) -> types.GenerateContentResponse:
        return self._client.models.generate_content(
            model=self._model, contents=prompt, config=self._config
        )

    def generate(self, *, title: str, year: int | None, source_text: str) -> tuple[SchemaCOut, int]:
        response = self._generate_content(build_prompt(title, year, source_text))
        data = response.parsed
        if not isinstance(data, SchemaCOut):
            block = response.prompt_feedback.block_reason if response.prompt_feedback else None
            suffix = f" (blocked: {block})" if block else ""
            raise ValueError(f"Gemini returned no parsed output for '{title}'{suffix}")
        tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
        return data, tokens or 0


class FakeGeminiClient:
    def generate(self, *, title: str, year: int | None, source_text: str) -> tuple[SchemaCOut, int]:
        data = SchemaCOut(
            plot_variants=PlotVariantsOut(
                concise=f"Concise plot of {title}.",
                chronological=f"Chronological plot of {title}.",
                thematic=f"Thematic reading of {title}.",
            ),
            scenes=[
                SceneOut(
                    title=f"Scene {i}",
                    description=f"Scene {i} of {title}.",
                    characters=["Hero", "Villain"],
                    mood=["tense"],
                )
                for i in range(3)
            ],
            themes=["love", "loss"],
            atmosphere=f"The atmosphere of {title} is reflective.",
            quotes=[QuoteOut(quote_text="A line.", attributed_to="Hero")],
            characters=[CharacterOut(character_name="Hero", description="The protagonist.")],
        )
        return data, 100


async def generate_async(
    client: GeminiClient,
    sem: asyncio.Semaphore,
    *,
    title: str,
    year: int | None,
    source_text: str,
) -> tuple[SchemaCOut, int]:
    async with sem:
        return await asyncio.to_thread(
            client.generate, title=title, year=year, source_text=source_text
        )
