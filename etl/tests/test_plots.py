from lib.plots import (
    LANG,
    SOURCE,
    build_search_query,
    html_to_text,
    page_url,
    source_text_row,
)


def test_build_search_query_with_year() -> None:
    assert build_search_query("Fight Club", 1999) == "Fight Club 1999 film"


def test_build_search_query_without_year() -> None:
    assert build_search_query("Unknown Title", None) == "Unknown Title film"


def test_html_to_text_strips_sup_references() -> None:
    html = '<p>The narrator meets Tyler.<sup class="reference">[1]</sup> They fight.</p>'
    assert html_to_text(html) == "The narrator meets Tyler. They fight."


def test_html_to_text_strips_editsection_and_collapses_whitespace() -> None:
    html = (
        '<h2>Plot<span class="mw-editsection">[edit]</span></h2>'
        "<p>Line one.</p>\n\n   <p>Line   two.</p>"
    )
    assert html_to_text(html) == "Plot Line one. Line two."


def test_html_to_text_empty_input() -> None:
    assert html_to_text("") == ""
    assert html_to_text("   \n  ") == ""


def test_page_url_encodes_spaces_and_specials() -> None:
    assert page_url("Fight Club") == "https://en.wikipedia.org/wiki/Fight_Club"
    assert page_url("Amélie") == "https://en.wikipedia.org/wiki/Am%C3%A9lie"
    assert (
        page_url("Léon: The Professional")
        == "https://en.wikipedia.org/wiki/L%C3%A9on%3A_The_Professional"
    )


def test_source_text_row_fields() -> None:
    row = source_text_row(42, "Fight Club", "The narrator meets Tyler.")
    assert row == {
        "movie_id": 42,
        "source": SOURCE,
        "lang": LANG,
        "content": "The narrator meets Tyler.",
        "source_url": "https://en.wikipedia.org/wiki/Fight_Club",
        "char_count": len("The narrator meets Tyler."),
    }
    assert SOURCE == "wikipedia"
    assert LANG == "en"
