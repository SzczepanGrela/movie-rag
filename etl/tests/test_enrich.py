from datetime import date

from lib.enrich import (
    genre_tmdb_ids,
    parse_release_date,
    to_enrichment_row,
    to_genre_row,
)

_DETAIL = {
    "id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "runtime": 139,
    "imdb_id": "tt0137523",
    "overview": "An insomniac office worker...",
    "tagline": "Mischief. Mayhem. Soap.",
    "release_date": "1999-10-15",
    "vote_average": 8.4,
    "vote_count": 27000,
    "original_language": "en",
    "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
}


def test_to_enrichment_row_maps_full_detail() -> None:
    row = to_enrichment_row(_DETAIL)

    assert row["tmdb_id"] == 550
    assert row["title"] == "Fight Club"
    assert row["year"] == 1999
    assert row["runtime"] == 139
    assert row["imdb_id"] == "tt0137523"
    assert row["overview"] == "An insomniac office worker..."
    assert row["tagline"] == "Mischief. Mayhem. Soap."
    assert row["release_date"] == date(1999, 10, 15)
    assert row["vote_average"] == 8.4
    assert row["vote_count"] == 27000
    assert row["original_language"] == "en"
    assert row["etl_status"] == "enriched"


def test_to_enrichment_row_empty_strings_become_none() -> None:
    row = to_enrichment_row({"id": 1, "title": "X", "imdb_id": "", "overview": "", "tagline": ""})

    assert row["imdb_id"] is None
    assert row["overview"] is None
    assert row["tagline"] is None


def test_parse_release_date_handles_empty_and_garbage() -> None:
    assert parse_release_date("") is None
    assert parse_release_date(None) is None
    assert parse_release_date("not-a-date") is None
    assert parse_release_date("2001-02-03") == date(2001, 2, 3)


def test_genre_tmdb_ids_and_to_genre_row() -> None:
    assert genre_tmdb_ids(_DETAIL) == [18, 53]
    assert genre_tmdb_ids({"id": 1, "title": "X"}) == []
    assert to_genre_row({"id": 18, "name": "Drama"}) == {"tmdb_id": 18, "name": "Drama"}
