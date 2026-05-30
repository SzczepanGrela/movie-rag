from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.genre import movie_genres

if TYPE_CHECKING:
    from app.models.chunk import Chunk
    from app.models.credits import MovieCast, MovieCrew
    from app.models.genre import Genre
    from app.models.schema_c import (
        Atmosphere,
        CharacterDescription,
        PlotVariant,
        Quote,
        Scene,
        Theme,
    )
    from app.models.source_text import SourceText


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    original_title: Mapped[str | None] = mapped_column(String(500))
    year: Mapped[int | None] = mapped_column(Integer)
    runtime: Mapped[int | None] = mapped_column(Integer)
    overview: Mapped[str | None] = mapped_column(Text)
    tagline: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None] = mapped_column(Date)
    vote_average: Mapped[float | None] = mapped_column(Float)
    vote_count: Mapped[int | None] = mapped_column(Integer)
    original_language: Mapped[str | None] = mapped_column(String(10))
    poster_path: Mapped[str | None] = mapped_column(Text)
    blurhash: Mapped[str | None] = mapped_column(Text)
    etl_status: Mapped[str] = mapped_column(String(20), server_default="seeded")
    schema_c_status: Mapped[str] = mapped_column(String(20), server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    genres: Mapped[list["Genre"]] = relationship(secondary=movie_genres, back_populates="movies")
    cast: Mapped[list["MovieCast"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    crew: Mapped[list["MovieCrew"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    source_texts: Mapped[list["SourceText"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    plot_variants: Mapped[list["PlotVariant"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    themes: Mapped[list["Theme"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    atmosphere: Mapped["Atmosphere | None"] = relationship(
        back_populates="movie", cascade="all, delete-orphan", uselist=False
    )
    quotes: Mapped[list["Quote"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
    character_descriptions: Mapped[list["CharacterDescription"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )
