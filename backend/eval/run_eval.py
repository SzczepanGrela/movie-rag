import asyncio
from collections.abc import Callable
from functools import partial
from pathlib import Path

import yaml

from app.config import settings
from app.db import AsyncSessionLocal
from app.search.embedder import GemmaEmbedder
from app.search.service import search
from eval.metrics import recall_at_k, top1

# 0.0 = scenes excluded from ranking (baseline); the rest sweep the scene weight.
ALPHAS = [0.0, 0.8, 0.85, 0.9, 0.95, 1.0]
QUERIES_PATH = Path(__file__).parent / "queries.yaml"

Pairs = list[tuple[list[int], int]]
recall5 = partial(recall_at_k, k=5)


def rate(pairs: Pairs, fn: Callable[[list[int], int], bool]) -> float:
    return sum(fn(r, e) for r, e in pairs) / len(pairs) if pairs else 0.0


async def _ranked_ids(session, embedder, query: str) -> list[int]:  # noqa: ANN001
    response = await search(session, embedder, query=query, limit=10)
    return [r.movie_id for r in response.results]


async def main() -> None:
    cases = yaml.safe_load(QUERIES_PATH.read_text())
    embedder = GemmaEmbedder()

    print(f"{'alpha':>6} | {'plot top1':>9} {'plot r@5':>8} | {'scene top1':>10} {'scene r@5':>9}")
    print("-" * 56)
    async with AsyncSessionLocal() as session:
        for alpha in ALPHAS:
            settings.search_scene_weight = alpha
            buckets: dict[str, Pairs] = {"plot": [], "scene": []}
            for case in cases:
                ranked = await _ranked_ids(session, embedder, case["query"])
                buckets[case["type"]].append((ranked, case["expect"]))

            p, s = buckets["plot"], buckets["scene"]
            print(
                f"{alpha:>6.2f} | "
                f"{rate(p, top1):>9.2f} {rate(p, recall5):>8.2f} | "
                f"{rate(s, top1):>10.2f} {rate(s, recall5):>9.2f}"
            )


if __name__ == "__main__":
    asyncio.run(main())
