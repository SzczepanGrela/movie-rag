from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.genre import movie_genres

if TYPE_CHECKING:
    from app.models.credits import MovieCast, MovieCrew
    from app.models.genre import Genre
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
    etl_status: Mapped[str] = mapped_column(String(20), server_default="seeded")
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
