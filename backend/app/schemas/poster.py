from pydantic import BaseModel


class PosterOut(BaseModel):
    url: str
    thumb_url: str
    blurhash: str | None
