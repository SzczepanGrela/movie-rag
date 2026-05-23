from lib.schema_c import (
    MAX_SCENES,
    CharacterOut,
    PlotVariantsOut,
    QuoteOut,
    SceneOut,
    SchemaCOut,
    build_prompt,
    to_rows,
)


def make_schema_c(
    *,
    n_scenes: int = 3,
    n_themes: int = 3,
    n_quotes: int = 2,
    n_chars: int = 2,
    atmosphere: str = "Tense and brooding.",
) -> SchemaCOut:
    return SchemaCOut(
        plot_variants=PlotVariantsOut(
            concise="Concise.", chronological="Chronological.", thematic="Thematic."
        ),
        scenes=[
            SceneOut(
                title=f"Scene {i}",
                description=f"Description {i}",
                characters=["Alice", "Bob"],
                mood=["dark", "tense"],
            )
            for i in range(n_scenes)
        ],
        themes=[f"theme-{i}" for i in range(n_themes)],
        atmosphere=atmosphere,
        quotes=[
            QuoteOut(quote_text=f"Quote {i}", attributed_to=f"Person {i}") for i in range(n_quotes)
        ],
        characters=[
            CharacterOut(character_name=f"Char {i}", description=f"Desc {i}")
            for i in range(n_chars)
        ],
    )


def test_build_prompt_contains_inputs() -> None:
    prompt = build_prompt("Fight Club", 1999, "A man forms a club.")
    assert "Fight Club" in prompt
    assert "1999" in prompt
    assert "A man forms a club." in prompt
    assert "English" in prompt


def test_build_prompt_year_none() -> None:
    assert "unknown year" in build_prompt("X", None, "plot")


def test_to_rows_all_keys() -> None:
    rows = to_rows(42, make_schema_c())
    assert set(rows.keys()) == {
        "plot_variants",
        "scenes",
        "themes",
        "atmosphere",
        "quotes",
        "character_descriptions",
    }


def test_to_rows_plot_variants_three_kinds() -> None:
    rows = to_rows(42, make_schema_c())
    pv = rows["plot_variants"]
    assert len(pv) == 3
    assert [r["kind"] for r in pv] == ["concise", "chronological", "thematic"]
    assert all(r["movie_id"] == 42 for r in pv)


def test_to_rows_scene_cap_and_indices() -> None:
    rows = to_rows(42, make_schema_c(n_scenes=40))
    scenes = rows["scenes"]
    assert len(scenes) == MAX_SCENES
    assert [s["scene_index"] for s in scenes] == list(range(MAX_SCENES))


def test_to_rows_mood_joined() -> None:
    rows = to_rows(42, make_schema_c())
    assert rows["scenes"][0]["mood"] == "dark, tense"
    assert rows["scenes"][0]["characters"] == ["Alice", "Bob"]


def test_to_rows_atmosphere_single_row() -> None:
    assert len(to_rows(42, make_schema_c())["atmosphere"]) == 1


def test_to_rows_atmosphere_empty_skipped() -> None:
    assert to_rows(42, make_schema_c(atmosphere="  "))["atmosphere"] == []


def test_to_rows_quote_and_char_indices() -> None:
    rows = to_rows(42, make_schema_c(n_quotes=3, n_chars=4))
    assert [q["quote_index"] for q in rows["quotes"]] == [0, 1, 2]
    assert [c["char_index"] for c in rows["character_descriptions"]] == [0, 1, 2, 3]


def test_to_rows_quote_and_char_caps() -> None:
    rows = to_rows(42, make_schema_c(n_quotes=10, n_chars=10))
    assert len(rows["quotes"]) == 5
    assert len(rows["character_descriptions"]) == 5


def test_to_rows_empty_lists() -> None:
    rows = to_rows(42, make_schema_c(n_scenes=0, n_themes=0, n_quotes=0, n_chars=0))
    assert rows["scenes"] == []
    assert rows["themes"] == []
    assert rows["quotes"] == []
    assert rows["character_descriptions"] == []
    assert len(rows["plot_variants"]) == 3
