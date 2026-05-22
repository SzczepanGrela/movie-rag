from typing import Any

TOP_CAST_N = 15
CREW_JOBS = ("Director", "Writer", "Screenplay", "Story")


def top_cast(detail: dict[str, Any], n: int = TOP_CAST_N) -> list[dict[str, Any]]:
    cast = detail.get("credits", {}).get("cast", [])
    ordered = sorted(cast, key=lambda c: c.get("order", 9999))
    return ordered[:n]


def key_crew(detail: dict[str, Any]) -> list[dict[str, Any]]:
    crew = detail.get("credits", {}).get("crew", [])
    return [c for c in crew if c.get("job") in CREW_JOBS]


def person_rows(detail: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"tmdb_id": e["id"], "name": e["name"]} for e in [*top_cast(detail), *key_crew(detail)]]


def to_cast_row(entry: dict[str, Any], movie_id: int, person_id: int) -> dict[str, Any]:
    return {
        "movie_id": movie_id,
        "person_id": person_id,
        "character": entry.get("character") or None,
        "billing_order": entry.get("order"),
    }


def to_crew_row(entry: dict[str, Any], movie_id: int, person_id: int) -> dict[str, Any]:
    return {
        "movie_id": movie_id,
        "person_id": person_id,
        "job": entry["job"],
        "department": entry.get("department") or None,
    }
