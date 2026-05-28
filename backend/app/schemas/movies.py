from datetime import date, datetime

from pydantic import BaseModel


class GenreOut(BaseModel):
    name: str


class CastMemberOut(BaseModel):
    name: str
    character: str | None
    tmdb_url: str


class CrewMemberOut(BaseModel):
    name: str
    job: str
    department: str | None


class SourceTextOut(BaseModel):
    source: str
    lang: str
    source_url: str | None
    fetched_at: datetime


class SceneRefOut(BaseModel):
    id: int
    scene_index: int
    title: str


class QuoteOut(BaseModel):
    quote_text: str
    attributed_to: str | None


class CharacterDescriptionOut(BaseModel):
    character_name: str
    description: str


class MovieDetail(BaseModel):
    id: int
    tmdb_id: int
    imdb_id: str | None
    title: str
    original_title: str | None
    year: int | None
    runtime: int | None
    release_date: date | None
    overview: str | None
    tagline: str | None
    vote_average: float | None
    vote_count: int | None
    original_language: str | None
    schema_c_status: str

    genres: list[GenreOut]
    cast: list[CastMemberOut]
    crew: list[CrewMemberOut]
    sources: list[SourceTextOut]

    plot_summary: str | None
    atmosphere: str | None
    themes: list[str]
    quotes: list[QuoteOut]
    character_descriptions: list[CharacterDescriptionOut]
    scenes: list[SceneRefOut]
