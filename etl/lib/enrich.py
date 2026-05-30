from datetime import date
from typing import Any

from lib.build_list import to_movie_row


def parse_release_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def to_enrichment_row(detail: dict[str, Any]) -> dict[str, Any]:
    return {
        **to_movie_row(detail),
        "runtime": detail.get("runtime") or None,
        "imdb_id": detail.get("imdb_id") or None,
        "overview": detail.get("overview") or None,
        "tagline": detail.get("tagline") or None,
        "release_date": parse_release_date(detail.get("release_date")),
        "vote_average": detail.get("vote_average"),
        "vote_count": detail.get("vote_count"),
        "original_language": detail.get("original_language") or None,
        "poster_path": detail.get("poster_path") or None,
        "etl_status": "enriched",
    }


def genre_tmdb_ids(detail: dict[str, Any]) -> list[int]:
    return [g["id"] for g in detail.get("genres", [])]


def to_genre_row(genre: dict[str, Any]) -> dict[str, Any]:
    return {"tmdb_id": genre["id"], "name": genre["name"]}
