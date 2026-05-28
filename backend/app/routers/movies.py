from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.movies import service
from app.schemas.movies import MovieDetail

router = APIRouter(prefix="/api", tags=["movies"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/movies/{movie_id}", response_model=MovieDetail)
async def get_movie(movie_id: int, session: SessionDep) -> MovieDetail:
    movie = await service.get_by_id(session, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="movie_not_found")
    return service.to_detail(movie)
