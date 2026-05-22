from lib.chunks import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    _tokenizer,
    build_prefix,
    chunk_body,
    chunk_row,
    split_tokens,
)


def test_build_prefix_full() -> None:
    result = build_prefix("Fight Club", 1999, ["Drama"])
    assert result == "Title: Fight Club (1999). Genres: Drama. "


def test_build_prefix_year_none() -> None:
    assert (
        build_prefix("Some Film", None, ["Action"])
        == "Title: Some Film (unknown). Genres: Action. "
    )


def test_build_prefix_no_genres() -> None:
    assert build_prefix("X", 2010, []) == "Title: X (2010). Genres: unknown. "


def test_build_prefix_sorts_genres() -> None:
    assert build_prefix("X", 2010, ["Drama", "Action"]).endswith("Genres: Action, Drama. ")


def test_split_tokens_empty() -> None:
    assert split_tokens([], size=10, overlap=2) == []


def test_split_tokens_shorter_than_size() -> None:
    assert split_tokens([1, 2, 3], size=10, overlap=2) == [[1, 2, 3]]


def test_split_tokens_exactly_size() -> None:
    assert split_tokens(list(range(10)), size=10, overlap=2) == [list(range(10))]


def test_split_tokens_size_plus_one_makes_two_windows() -> None:
    windows = split_tokens(list(range(11)), size=10, overlap=2)
    assert len(windows) == 2
    assert windows[0] == list(range(10))
    assert windows[1] == [8, 9, 10]


def test_split_tokens_long_has_correct_stride() -> None:
    tokens = list(range(30))
    windows = split_tokens(tokens, size=10, overlap=2)
    assert windows[0] == list(range(0, 10))
    assert windows[1] == list(range(8, 18))
    assert windows[2] == list(range(16, 26))
    assert all(len(w) <= 10 for w in windows)


def test_chunk_body_empty() -> None:
    assert chunk_body("", size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) == []
    assert chunk_body("   \n  ", size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) == []


def test_chunk_body_short_text_single_chunk() -> None:
    result = chunk_body("The cat sat on the mat.", size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    assert len(result) == 1
    text, count = result[0]
    assert "cat" in text
    assert count == len(_tokenizer().encode(text, add_special_tokens=False))


def test_chunk_body_long_text_multiple_chunks() -> None:
    paragraph = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    )
    long_text = paragraph * 100
    result = chunk_body(long_text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    assert len(result) >= 3
    assert all(count <= CHUNK_SIZE for _, count in result)


def test_chunk_row_fields() -> None:
    embedding = [0.1] * 768
    row = chunk_row(
        source_text_id=5,
        movie_id=42,
        chunk_index=0,
        content="Title: X (2010). Genres: Drama. The cat sat.",
        embedding=embedding,
    )
    assert row["source_text_id"] == 5
    assert row["movie_id"] == 42
    assert row["chunk_index"] == 0
    assert row["content"].startswith("Title: X")
    assert row["embedding"] == embedding
    assert row["token_count"] == len(_tokenizer().encode(row["content"], add_special_tokens=False))
