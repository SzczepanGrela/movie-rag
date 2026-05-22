from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup

SOURCE = "wikipedia"
LANG = "en"
WIKI_BASE = "https://en.wikipedia.org/wiki/"


def build_search_query(title: str, year: int | None) -> str:
    if year is None:
        return f"{title} film"
    return f"{title} {year} film"


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for sup in soup.find_all("sup"):
        sup.decompose()
    for style in soup.find_all("style"):
        style.decompose()
    for edit in soup.find_all(class_="mw-editsection"):
        edit.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())


def page_url(page_title: str) -> str:
    return WIKI_BASE + quote(page_title.replace(" ", "_"))


def source_text_row(movie_id: int, page_title: str, content: str) -> dict[str, Any]:
    return {
        "movie_id": movie_id,
        "source": SOURCE,
        "lang": LANG,
        "content": content,
        "source_url": page_url(page_title),
        "char_count": len(content),
    }
