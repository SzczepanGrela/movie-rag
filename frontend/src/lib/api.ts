export type BestChunk = { text: string; score: number };

export type SearchResult = {
  movie_id: number;
  title: string;
  year: number | null;
  score: number;
  best_chunk: BestChunk;
};

export type SearchResponse = {
  results: SearchResult[];
  total_candidates: number;
  took_ms: number;
};

export async function searchMovies(
  query: string,
  limit = 10,
): Promise<SearchResponse> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) {
    throw new Error(`Search failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
