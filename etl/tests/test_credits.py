from lib.credits import (
    key_crew,
    person_rows,
    to_cast_row,
    to_crew_row,
    top_cast,
)

_DETAIL = {
    "id": 550,
    "credits": {
        "cast": [
            {"id": 819, "name": "Edward Norton", "character": "The Narrator", "order": 0},
            {"id": 287, "name": "Brad Pitt", "character": "Tyler Durden", "order": 1},
            {"id": 1283, "name": "Helena Bonham Carter", "character": "Marla", "order": 2},
        ],
        "crew": [
            {"id": 7467, "name": "David Fincher", "job": "Director", "department": "Directing"},
            {"id": 7469, "name": "Jim Uhls", "job": "Screenplay", "department": "Writing"},
            {"id": 1, "name": "Some Gaffer", "job": "Gaffer", "department": "Lighting"},
        ],
    },
}


def test_top_cast_sorts_by_order_and_truncates() -> None:
    cast = [{"id": i, "name": f"P{i}", "order": 20 - i} for i in range(20)]
    detail = {"credits": {"cast": cast}}

    result = top_cast(detail, n=5)

    assert len(result) == 5
    assert [c["order"] for c in result] == [1, 2, 3, 4, 5]


def test_top_cast_missing_credits_returns_empty() -> None:
    assert top_cast({"id": 1}) == []


def test_key_crew_keeps_only_allowlisted_jobs() -> None:
    result = key_crew(_DETAIL)

    assert {c["job"] for c in result} == {"Director", "Screenplay"}
    assert all(c["job"] != "Gaffer" for c in result)


def test_person_rows_includes_cast_and_crew() -> None:
    rows = person_rows(_DETAIL)

    tmdb_ids = [r["tmdb_id"] for r in rows]
    assert 819 in tmdb_ids
    assert 7467 in tmdb_ids
    assert len(rows) == 5


def test_to_cast_row_maps_fields() -> None:
    entry = {"id": 287, "character": "Tyler Durden", "order": 1}

    row = to_cast_row(entry, movie_id=10, person_id=99)

    assert row == {
        "movie_id": 10,
        "person_id": 99,
        "character": "Tyler Durden",
        "billing_order": 1,
    }


def test_to_cast_row_empty_character_becomes_none() -> None:
    row = to_cast_row({"id": 1, "character": "", "order": 3}, movie_id=1, person_id=2)

    assert row["character"] is None
    assert row["billing_order"] == 3


def test_to_crew_row_maps_fields_and_empty_department() -> None:
    row = to_crew_row({"id": 1, "job": "Director", "department": ""}, movie_id=1, person_id=2)

    assert row == {"movie_id": 1, "person_id": 2, "job": "Director", "department": None}
