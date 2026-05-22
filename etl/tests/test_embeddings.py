import math

from lib.embeddings import EMBEDDING_DIM, FakeEmbedder, embed_async


def test_fake_embedder_deterministic() -> None:
    embedder = FakeEmbedder()
    [v1] = embedder.embed(["the cat sat on the mat"])
    [v2] = embedder.embed(["the cat sat on the mat"])
    assert v1 == v2


def test_fake_embedder_correct_shape() -> None:
    embedder = FakeEmbedder()
    result = embedder.embed(["a", "b", "c"])
    assert len(result) == 3
    assert all(len(v) == EMBEDDING_DIM for v in result)


def test_fake_embedder_different_texts_differ() -> None:
    embedder = FakeEmbedder()
    [va, vb] = embedder.embed(["alpha", "beta"])
    assert va != vb


def test_fake_embedder_normalized() -> None:
    embedder = FakeEmbedder()
    [vec] = embedder.embed(["some text to embed"])
    norm = math.sqrt(sum(f * f for f in vec))
    assert math.isclose(norm, 1.0, abs_tol=1e-6)


async def test_embed_async_uses_thread() -> None:
    embedder = FakeEmbedder()
    result = await embed_async(embedder, ["x", "y"])
    assert len(result) == 2
    assert result == embedder.embed(["x", "y"])
