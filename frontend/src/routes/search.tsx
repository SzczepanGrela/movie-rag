import { useQuery } from "@tanstack/react-query";
import { createRoute, Link } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { type FormEvent, useState } from "react";
import { MovieRagLogo } from "@/components/MovieRagLogo";
import { Poster } from "@/components/Poster";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { type SearchResponse, searchMovies } from "@/lib/api";
import { rootRoute } from "@/routes/__root";

export function SearchPage() {
  const [draft, setDraft] = useState("");
  const [submitted, setSubmitted] = useState("");

  const { data, isFetching, isError, error } = useQuery<SearchResponse, Error>({
    queryKey: ["search", submitted],
    queryFn: () => searchMovies(submitted),
    enabled: !!submitted,
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(draft.trim());
  }

  const showSkeleton = isFetching && !data;
  const hasResults = data && !isFetching && data.results.length > 0;
  const noResults = data && !isFetching && data.results.length === 0;

  return (
    <div className="min-h-screen bg-background">
      <main className="mx-auto max-w-3xl px-4 py-16 sm:py-24">
        <header className="space-y-5 text-center mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3.5 py-1 text-[11px] font-mono uppercase tracking-[0.12em] text-muted-foreground backdrop-blur-sm">
            <span
              className="size-1.5 rounded-full bg-primary"
              aria-hidden="true"
            />
            <span>Semantic search · 4,719 films</span>
          </div>
          <h1 className="flex justify-center">
            <MovieRagLogo className="text-5xl sm:text-6xl text-foreground" />
          </h1>
          <p className="text-base text-muted-foreground max-w-md mx-auto">
            Describe a vibe, a plot, a feeling — find the film.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="flex gap-2 mb-10 rounded-2xl border border-border bg-card/80 p-2 shadow-[0_8px_32px_-12px_rgba(0,0,0,0.6)] backdrop-blur-sm focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/25 transition"
        >
          <Input
            type="text"
            placeholder="samurai honor and revenge…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="border-0 shadow-none focus-visible:ring-0 text-base bg-transparent placeholder:text-muted-foreground/60"
            autoFocus
          />
          <Button
            type="submit"
            disabled={!draft.trim() || isFetching}
            className="gap-1.5 px-5 font-semibold"
          >
            <Search className="size-4" />
            Search
          </Button>
        </form>

        {showSkeleton && (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <Card key={i} className="overflow-hidden">
                <CardHeader>
                  <Skeleton className="h-5 w-3/5" />
                </CardHeader>
                <CardContent className="space-y-2">
                  <Skeleton className="h-3 w-1/3" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-4/5" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {isError && (
          <Card className="border-destructive/60 bg-destructive/10">
            <CardContent className="py-6">
              <p className="text-destructive font-medium text-sm">
                {error?.message ?? "Unknown error"}
              </p>
            </CardContent>
          </Card>
        )}

        {noResults && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <p>No results for "{submitted}".</p>
            </CardContent>
          </Card>
        )}

        {hasResults && (
          <div className="space-y-4">
            <div className="flex items-baseline justify-between text-[11px] font-mono uppercase tracking-[0.12em] text-muted-foreground px-1">
              <span>
                {data.results.length}{" "}
                {data.results.length === 1 ? "result" : "results"}
              </span>
              <span>{data.took_ms} ms</span>
            </div>
            {data.results.map((r) => {
              const matchPct = Math.round(r.score * 100);
              return (
                <Link
                  key={r.movie_id}
                  to="/movies/$id"
                  params={{ id: String(r.movie_id) }}
                  className="block"
                >
                  <Card className="group cursor-pointer transition-all border-border/80 hover:border-primary/50 hover:shadow-[0_10px_40px_-12px_rgba(245,213,71,0.25)] hover:-translate-y-0.5">
                    <div className="flex gap-4 p-4">
                      <Poster
                        poster={r.poster}
                        size="thumb"
                        alt={`${r.title} poster`}
                        className="w-16 shrink-0"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-baseline justify-between gap-3">
                          <h3 className="text-lg font-semibold leading-tight tracking-tight group-hover:text-primary transition-colors">
                            {r.title}
                          </h3>
                          <div className="flex items-baseline gap-2 shrink-0">
                            {r.year ? (
                              <span className="font-mono text-[11px] text-muted-foreground tracking-wider">
                                {r.year}
                              </span>
                            ) : null}
                            <span className="rounded-full bg-primary text-primary-foreground px-2.5 py-0.5 text-[11px] font-bold tracking-tight">
                              {matchPct}%
                            </span>
                          </div>
                        </div>
                        <p className="mt-2 line-clamp-3 text-sm text-foreground/80 leading-relaxed">
                          {r.best_chunk.text}
                        </p>
                        <p className="mt-2 font-mono text-[10px] text-muted-foreground/70">
                          #{r.movie_id}
                        </p>
                      </div>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}

export const searchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: SearchPage,
});
