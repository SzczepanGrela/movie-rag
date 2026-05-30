from pydantic import BaseModel, Field

from app.schemas.poster import PosterOut


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class BestChunk(BaseModel):
    text: str
    score: float


class SearchResult(BaseModel):
    movie_id: int
    title: str
    year: int | None
    score: float
    best_chunk: BestChunk
    poster: PosterOut | None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total_candidates: int
    took_ms: int
