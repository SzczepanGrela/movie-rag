def top1(ranked_movie_ids: list[int], expected: int) -> bool:
    return bool(ranked_movie_ids) and ranked_movie_ids[0] == expected


def recall_at_k(ranked_movie_ids: list[int], expected: int, *, k: int) -> bool:
    return expected in ranked_movie_ids[:k]
