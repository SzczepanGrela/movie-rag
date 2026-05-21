from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.movie import Movie


class SourceText(Base):
    __tablename__ = "source_texts"
    __table_args__ = (UniqueConstraint("movie_id", "source", "lang"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(50))
    lang: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    char_count: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship(back_populates="source_texts")
