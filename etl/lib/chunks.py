from typing import Any, cast

from transformers import AutoTokenizer, PreTrainedTokenizerBase

TOKENIZER_MODEL = "google/embeddinggemma-300m"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

_TOKENIZER: PreTrainedTokenizerBase | None = None


def _tokenizer() -> PreTrainedTokenizerBase:
    global _TOKENIZER
    if _TOKENIZER is None:
        _TOKENIZER = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
    return _TOKENIZER


def build_embed_input(title: str, year: int | None, body: str) -> str:
    year_str = str(year) if year is not None else "unknown"
    return f"title: {title} ({year_str}) | text: {body}"


def split_tokens(tokens: list[int], *, size: int, overlap: int) -> list[list[int]]:
    if not tokens:
        return []
    if len(tokens) <= size:
        return [tokens]
    stride = size - overlap
    windows: list[list[int]] = []
    for start in range(0, len(tokens), stride):
        window = tokens[start : start + size]
        if not window:
            break
        windows.append(window)
        if start + size >= len(tokens):
            break
    return windows


def chunk_body(text: str, *, size: int, overlap: int) -> list[tuple[str, int]]:
    if not text.strip():
        return []
    tokenizer = _tokenizer()
    tokens: list[int] = tokenizer.encode(text, add_special_tokens=False)
    windows = split_tokens(tokens, size=size, overlap=overlap)
    return [(cast(str, tokenizer.decode(w, skip_special_tokens=True)), len(w)) for w in windows]


def chunk_row(
    *,
    source_text_id: int,
    movie_id: int,
    chunk_index: int,
    content: str,
    embedding: list[float],
) -> dict[str, Any]:
    token_count = len(_tokenizer().encode(content, add_special_tokens=False))
    return {
        "source_text_id": source_text_id,
        "movie_id": movie_id,
        "chunk_index": chunk_index,
        "content": content,
        "token_count": token_count,
        "embedding": embedding,
    }
