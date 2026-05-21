from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.movie import Movie
    from app.models.person import Person


class MovieCast(Base):
    __tablename__ = "movie_cast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), index=True)
    character: Mapped[str | None] = mapped_column(String(300))
    billing_order: Mapped[int | None] = mapped_column(Integer)

    movie: Mapped["Movie"] = relationship(back_populates="cast")
    person: Mapped["Person"] = relationship(back_populates="cast_roles")


class MovieCrew(Base):
    __tablename__ = "movie_crew"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), index=True)
    job: Mapped[str] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))

    movie: Mapped["Movie"] = relationship(back_populates="crew")
    person: Mapped["Person"] = relationship(back_populates="crew_roles")
