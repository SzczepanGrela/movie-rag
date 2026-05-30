export type BestChunk = { text: string; score: number };

export type PosterData = {
  url: string;
  thumb_url: string;
  blurhash: string | null;
};

export type SearchResult = {
  movie_id: number;
  title: string;
  year: number | null;
  score: number;
  best_chunk: BestChunk;
  poster: PosterData | null;
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

export type GenreOut = { name: string };

export type CastMemberOut = {
  name: string;
  character: string | null;
  tmdb_url: string;
};

export type CrewMemberOut = {
  name: string;
  job: string;
  department: string | null;
};

export type QuoteOut = {
  quote_text: string;
  attributed_to: string | null;
};

export type CharacterDescriptionOut = {
  character_name: string;
  description: string;
};

export type SourceTextOut = {
  source: string;
  lang: string;
  source_url: string | null;
  fetched_at: string;
};

export type SceneRefOut = {
  id: number;
  scene_index: number;
  title: string;
};

export type MovieDetail = {
  id: number;
  tmdb_id: number;
  imdb_id: string | null;
  title: string;
  original_title: string | null;
  year: number | null;
  runtime: number | null;
  release_date: string | null;
  overview: string | null;
  tagline: string | null;
  vote_average: number | null;
  vote_count: number | null;
  original_language: string | null;
  schema_c_status: string;
  poster: PosterData | null;
  genres: GenreOut[];
  cast: CastMemberOut[];
  crew: CrewMemberOut[];
  sources: SourceTextOut[];
  plot_summary: string | null;
  atmosphere: string | null;
  themes: string[];
  quotes: QuoteOut[];
  character_descriptions: CharacterDescriptionOut[];
  scenes: SceneRefOut[];
};

export class NotFoundError extends Error {
  constructor() {
    super("Not found");
    this.name = "NotFoundError";
  }
}

export async function getMovie(id: number): Promise<MovieDetail> {
  const res = await fetch(`/api/movies/${id}`);
  if (res.status === 404) throw new NotFoundError();
  if (!res.ok) throw new Error(`Failed to load movie: ${res.status}`);
  return res.json();
}
