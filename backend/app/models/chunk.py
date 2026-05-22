from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.movie import Movie
    from app.models.source_text import SourceText


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (UniqueConstraint("source_text_id", "chunk_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_text_id: Mapped[int] = mapped_column(
        ForeignKey("source_texts.id", ondelete="CASCADE"), index=True
    )
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship(back_populates="chunks")
    source_text: Mapped["SourceText"] = relationship(back_populates="chunks")
