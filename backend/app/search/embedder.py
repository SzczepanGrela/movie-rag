import asyncio
import hashlib
import math
from typing import Literal, Protocol, cast

from fastapi import Request
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "google/embeddinggemma-300m"
EMBEDDING_DIM = 768

EmbedKind = Literal["query", "document"]


class Embedder(Protocol):
    def embed(self, texts: list[str], *, kind: EmbedKind) -> list[list[float]]: ...


def get_embedder(request: Request) -> Embedder:
    embedder: Embedder = request.app.state.embedder
    return embedder


class GemmaEmbedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str], *, kind: EmbedKind) -> list[list[float]]:
        prompt_name = "query" if kind == "query" else None
        vectors = self._model.encode(
            texts,
            prompt_name=prompt_name,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return cast(list[list[float]], vectors.tolist())


class FakeEmbedder:
    def embed(self, texts: list[str], *, kind: EmbedKind) -> list[list[float]]:
        _ = kind
        return [_fake_vector(text) for text in texts]


def _fake_vector(text: str) -> list[float]:
    raw = hashlib.shake_128(text.encode("utf-8")).digest(EMBEDDING_DIM * 4)
    ints = [int.from_bytes(raw[i * 4 : (i + 1) * 4], "big") for i in range(EMBEDDING_DIM)]
    floats = [(x / 2**32) * 2 - 1 for x in ints]
    norm = math.sqrt(sum(f * f for f in floats))
    if norm == 0:
        return floats
    return [f / norm for f in floats]


async def embed_async(
    embedder: Embedder, texts: list[str], *, kind: EmbedKind
) -> list[list[float]]:
    return await asyncio.to_thread(embedder.embed, texts, kind=kind)
