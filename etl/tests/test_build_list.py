from lib.build_list import dedupe_by_tmdb_id, to_movie_row


def test_to_movie_row_maps_tmdb_response() -> None:
    api_dict = {
        "id": 550,
        "title": "Fight Club",
        "original_title": "Fight Club",
        "release_date": "1999-10-15",
        "overview": "An insomniac office worker...",
        "popularity": 61.4,
        "vote_average": 8.4,
        "vote_count": 27000,
        "original_language": "en",
    }

    row = to_movie_row(api_dict)

    assert row == {
        "tmdb_id": 550,
        "title": "Fight Club",
        "original_title": "Fight Club",
        "year": 1999,
    }


def test_to_movie_row_handles_missing_release_date() -> None:
    row = to_movie_row(
        {"id": 1, "title": "No Date Movie", "original_title": None, "release_date": ""}
    )

    assert row["year"] is None
    assert row["tmdb_id"] == 1
    assert row["title"] == "No Date Movie"


def test_to_movie_row_handles_garbage_release_date() -> None:
    row = to_movie_row({"id": 2, "title": "Bad Date", "release_date": "not-a-date"})

    assert row["year"] is None


def test_dedupe_by_tmdb_id_keeps_first_occurrence() -> None:
    rows = [
        {"tmdb_id": 1, "title": "First"},
        {"tmdb_id": 2, "title": "Second"},
        {"tmdb_id": 1, "title": "Duplicate (should be dropped)"},
    ]

    out = dedupe_by_tmdb_id(rows)

    assert len(out) == 2
    assert out[0]["title"] == "First"
    assert out[1]["title"] == "Second"
