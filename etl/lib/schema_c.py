from typing import Any

from pydantic import BaseModel, Field

MAX_SCENES = 30
MAX_THEMES = 7
MAX_QUOTES = 5
MAX_CHARS = 5

PLOT_KINDS = ("concise", "chronological", "thematic")


class PlotVariantsOut(BaseModel):
    concise: str = Field(description="One marketing-style paragraph summarizing the plot.")
    chronological: str = Field(description="Full plot told in order, 3-5 paragraphs.")
    thematic: str = Field(description="1-2 paragraphs about the themes and emotions.")


class SceneOut(BaseModel):
    title: str = Field(description="Short scene title.")
    description: str = Field(description="What happens in the scene.")
    characters: list[str] = Field(description="Names of characters present in the scene.")
    mood: list[str] = Field(description="1-3 adjectives describing the scene's mood.")


class QuoteOut(BaseModel):
    quote_text: str = Field(description="A memorable line of dialogue from the film.")
    attributed_to: str = Field(description="Character or speaker the quote is attributed to.")


class CharacterOut(BaseModel):
    character_name: str = Field(description="Name of the character.")
    description: str = Field(description="A few sentences describing the character.")


class SchemaCOut(BaseModel):
    plot_variants: PlotVariantsOut
    scenes: list[SceneOut] = Field(description="15-30 key scenes in chronological order.")
    themes: list[str] = Field(description="3-7 central themes.")
    atmosphere: str = Field(description="1-2 sentences describing the film's overall atmosphere.")
    quotes: list[QuoteOut] = Field(description="Up to 5 memorable quotes.")
    characters: list[CharacterOut] = Field(
        description="Up to 5 main characters, most important first."
    )


def build_prompt(title: str, year: int | None, source_text: str) -> str:
    year_str = str(year) if year is not None else "unknown year"
    return (
        f"You are a film analyst. Based on the plot summary below for the movie "
        f'"{title}" ({year_str}), produce structured content in English.\n\n'
        "Requirements:\n"
        "- plot_variants: exactly three retellings (concise, chronological, thematic).\n"
        "- scenes: 15-30 key scenes in chronological order, each with a title, description, "
        "the characters present, and a 1-3 adjective mood.\n"
        "- themes: 3-7 central themes.\n"
        "- atmosphere: 1-2 sentences on the overall mood.\n"
        "- quotes: up to 5 memorable lines with who said them. Leave empty if none are known.\n"
        "- characters: up to 5 main characters, most important first.\n\n"
        f"Plot summary:\n{source_text}"
    )


def to_rows(movie_id: int, data: SchemaCOut) -> dict[str, list[dict[str, Any]]]:
    plot_variants = [
        {"movie_id": movie_id, "kind": kind, "text": getattr(data.plot_variants, kind)}
        for kind in PLOT_KINDS
    ]
    scenes = [
        {
            "movie_id": movie_id,
            "scene_index": idx,
            "title": scene.title,
            "description": scene.description,
            "mood": ", ".join(scene.mood),
            "characters": scene.characters,
        }
        for idx, scene in enumerate(data.scenes[:MAX_SCENES])
    ]
    themes = [
        {"movie_id": movie_id, "theme_index": idx, "theme": theme}
        for idx, theme in enumerate(data.themes[:MAX_THEMES])
    ]
    atmosphere = (
        [{"movie_id": movie_id, "text": data.atmosphere}] if data.atmosphere.strip() else []
    )
    quotes = [
        {
            "movie_id": movie_id,
            "quote_index": idx,
            "quote_text": quote.quote_text,
            "attributed_to": quote.attributed_to or None,
        }
        for idx, quote in enumerate(data.quotes[:MAX_QUOTES])
    ]
    character_descriptions = [
        {
            "movie_id": movie_id,
            "char_index": idx,
            "character_name": char.character_name,
            "description": char.description,
        }
        for idx, char in enumerate(data.characters[:MAX_CHARS])
    ]
    return {
        "plot_variants": plot_variants,
        "scenes": scenes,
        "themes": themes,
        "atmosphere": atmosphere,
        "quotes": quotes,
        "character_descriptions": character_descriptions,
    }
