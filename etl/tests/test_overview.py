from lib.overview import OVERVIEW_LANG, OVERVIEW_SOURCE, overview_row


def test_overview_row_fields() -> None:
    row = overview_row(42, "A short film summary.")
    assert row["movie_id"] == 42
    assert row["source"] == OVERVIEW_SOURCE
    assert row["lang"] == OVERVIEW_LANG
    assert row["content"] == "A short film summary."
    assert row["source_url"] is None
    assert row["char_count"] == len("A short film summary.")


def test_overview_row_source_and_lang_constants() -> None:
    assert OVERVIEW_SOURCE == "tmdb_overview"
    assert OVERVIEW_LANG == "en"


def test_overview_row_char_count_matches_content() -> None:
    text = "x" * 1234
    row = overview_row(1, text)
    assert row["char_count"] == 1234
