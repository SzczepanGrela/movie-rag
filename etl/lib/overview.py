from typing import Any

OVERVIEW_SOURCE = "tmdb_overview"
OVERVIEW_LANG = "en"


def overview_row(movie_id: int, overview: str) -> dict[str, Any]:
    return {
        "movie_id": movie_id,
        "source": OVERVIEW_SOURCE,
        "lang": OVERVIEW_LANG,
        "content": overview,
        "source_url": None,
        "char_count": len(overview),
    }
