from typing import Any


def to_movie_row(api_dict: dict[str, Any]) -> dict[str, Any]:
    release_date = api_dict.get("release_date") or None
    year: int | None = None
    if release_date:
        try:
            year = int(str(release_date).split("-", 1)[0])
        except ValueError:
            year = None
    return {
        "tmdb_id": api_dict["id"],
        "title": api_dict["title"],
        "original_title": api_dict.get("original_title"),
        "year": year,
    }


def dedupe_by_tmdb_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        tmdb_id = row["tmdb_id"]
        if tmdb_id in seen:
            continue
        seen.add(tmdb_id)
        out.append(row)
    return out
