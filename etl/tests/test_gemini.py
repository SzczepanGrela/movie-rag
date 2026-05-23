import asyncio

from lib.gemini import FakeGeminiClient, generate_async
from lib.schema_c import SchemaCOut


def test_fake_generate_returns_schema_and_tokens() -> None:
    client = FakeGeminiClient()
    data, tokens = client.generate(title="Fight Club", year=1999, source_text="plot")
    assert isinstance(data, SchemaCOut)
    assert isinstance(tokens, int)
    assert tokens > 0


def test_fake_generate_deterministic() -> None:
    client = FakeGeminiClient()
    a, _ = client.generate(title="X", year=2000, source_text="plot")
    b, _ = client.generate(title="X", year=2000, source_text="plot")
    assert a == b


def test_fake_generate_uses_title() -> None:
    client = FakeGeminiClient()
    data, _ = client.generate(title="Inception", year=2010, source_text="plot")
    assert "Inception" in data.plot_variants.concise


async def test_generate_async_smoke() -> None:
    client = FakeGeminiClient()
    sem = asyncio.Semaphore(2)
    data, tokens = await generate_async(client, sem, title="Heat", year=1995, source_text="plot")
    assert isinstance(data, SchemaCOut)
    assert tokens == 100


async def test_generate_async_concurrent() -> None:
    client = FakeGeminiClient()
    sem = asyncio.Semaphore(2)
    results = await asyncio.gather(
        *(
            generate_async(client, sem, title=f"M{i}", year=2000, source_text="plot")
            for i in range(5)
        )
    )
    assert len(results) == 5
    assert all(isinstance(d, SchemaCOut) for d, _ in results)
