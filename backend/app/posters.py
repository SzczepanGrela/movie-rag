from app.config import settings
from app.schemas.poster import PosterOut


def build_poster(tmdb_id: int, poster_path: str | None, blurhash: str | None) -> PosterOut | None:
    if not poster_path:
        return None
    base = settings.r2_public_base
    return PosterOut(
        url=f"{base}/posters/w500/{tmdb_id}.jpg",
        thumb_url=f"{base}/posters/w154/{tmdb_id}.jpg",
        blurhash=blurhash,
    )
