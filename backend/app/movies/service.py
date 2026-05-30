from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Movie
from app.models.credits import MovieCast, MovieCrew
from app.posters import build_poster
from app.schemas.movies import (
    CastMemberOut,
    CharacterDescriptionOut,
    CrewMemberOut,
    GenreOut,
    MovieDetail,
    QuoteOut,
    SceneRefOut,
    SourceTextOut,
)

CAST_LIMIT = 15
CONCISE_VARIANT_KIND = "concise"
TMDB_PERSON_URL = "https://www.themoviedb.org/person/{tmdb_id}"


async def get_by_id(session: AsyncSession, movie_id: int) -> Movie | None:
    stmt = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.cast).selectinload(MovieCast.person),
            selectinload(Movie.crew).selectinload(MovieCrew.person),
            selectinload(Movie.source_texts),
            selectinload(Movie.plot_variants),
            selectinload(Movie.scenes),
            selectinload(Movie.themes),
            selectinload(Movie.atmosphere),
            selectinload(Movie.quotes),
            selectinload(Movie.character_descriptions),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def to_detail(movie: Movie) -> MovieDetail:
    cast_sorted = sorted(
        movie.cast,
        key=lambda c: (c.billing_order is None, c.billing_order or 0),
    )[:CAST_LIMIT]
    cast = [
        CastMemberOut(
            name=c.person.name,
            character=c.character,
            tmdb_url=TMDB_PERSON_URL.format(tmdb_id=c.person.tmdb_id),
        )
        for c in cast_sorted
    ]

    crew_sorted = sorted(
        movie.crew,
        key=lambda c: (c.department or "", c.job, c.person.name),
    )
    crew = [
        CrewMemberOut(
            name=c.person.name,
            job=c.job,
            department=c.department,
        )
        for c in crew_sorted
    ]

    plot_summary: str | None = next(
        (pv.text for pv in movie.plot_variants if pv.kind == CONCISE_VARIANT_KIND),
        None,
    )

    themes = [t.theme for t in sorted(movie.themes, key=lambda t: t.theme_index)]

    scenes = [
        SceneRefOut(id=s.id, scene_index=s.scene_index, title=s.title)
        for s in sorted(movie.scenes, key=lambda s: s.scene_index)
    ]

    quotes = [
        QuoteOut(quote_text=q.quote_text, attributed_to=q.attributed_to)
        for q in sorted(movie.quotes, key=lambda q: q.quote_index)
    ]

    character_descriptions = [
        CharacterDescriptionOut(
            character_name=cd.character_name,
            description=cd.description,
        )
        for cd in sorted(movie.character_descriptions, key=lambda cd: cd.char_index)
    ]

    return MovieDetail(
        id=movie.id,
        tmdb_id=movie.tmdb_id,
        imdb_id=movie.imdb_id,
        title=movie.title,
        original_title=movie.original_title,
        year=movie.year,
        runtime=movie.runtime,
        release_date=movie.release_date,
        overview=movie.overview,
        tagline=movie.tagline,
        vote_average=movie.vote_average,
        vote_count=movie.vote_count,
        original_language=movie.original_language,
        schema_c_status=movie.schema_c_status,
        poster=build_poster(movie.tmdb_id, movie.poster_path, movie.blurhash),
        genres=[GenreOut(name=g.name) for g in movie.genres],
        cast=cast,
        crew=crew,
        sources=[
            SourceTextOut(
                source=s.source,
                lang=s.lang,
                source_url=s.source_url,
                fetched_at=s.fetched_at,
            )
            for s in movie.source_texts
        ],
        plot_summary=plot_summary,
        atmosphere=movie.atmosphere.text if movie.atmosphere else None,
        themes=themes,
        quotes=quotes,
        character_descriptions=character_descriptions,
        scenes=scenes,
    )
