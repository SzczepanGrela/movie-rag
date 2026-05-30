import { useQuery } from "@tanstack/react-query";
import { createRoute, Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { MovieRagLogo } from "@/components/MovieRagLogo";
import { Poster } from "@/components/Poster";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type CrewMemberOut,
  getMovie,
  type MovieDetail,
  NotFoundError,
} from "@/lib/api";
import { rootRoute } from "@/routes/__root";

export const movieDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/movies/$id",
  component: MovieDetailPage,
});

function MovieDetailPage() {
  const { id } = useParams({ from: movieDetailRoute.id });
  const movieId = Number(id);

  const { data, isLoading, isError, error, refetch } = useQuery<
    MovieDetail,
    Error
  >({
    queryKey: ["movie", movieId],
    queryFn: () => getMovie(movieId),
  });

  return (
    <div className="min-h-screen bg-background">
      <main className="mx-auto max-w-3xl px-4 py-12">
        <PageChrome id={movieId} />
        {isLoading && <DetailSkeleton />}
        {isError && error instanceof NotFoundError && <NotFoundCard />}
        {isError && !(error instanceof NotFoundError) && (
          <ErrorCard message={error.message} onRetry={() => refetch()} />
        )}
        {data && <DetailBody movie={data} />}
      </main>
    </div>
  );
}

function PageChrome({ id }: { id: number }) {
  return (
    <div className="mb-8 flex items-center justify-between">
      <Link to="/" className="inline-flex items-center gap-3">
        <MovieRagLogo className="text-xl text-foreground" />
      </Link>
      <span className="font-mono text-[11px] text-muted-foreground/70">
        #{id}
      </span>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/"
      className="inline-flex items-center gap-2 text-[11px] font-mono uppercase tracking-[0.12em] text-muted-foreground hover:text-primary transition-colors mb-8"
    >
      <ArrowLeft className="size-3.5" />
      Back to search
    </Link>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-8">
      <BackLink />
      <Skeleton className="h-10 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <div className="space-y-3">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </div>
      <div className="space-y-3">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/5" />
      </div>
    </div>
  );
}

function NotFoundCard() {
  return (
    <>
      <BackLink />
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <p className="font-medium">Movie not found.</p>
        </CardContent>
      </Card>
    </>
  );
}

function ErrorCard({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <>
      <BackLink />
      <Card className="border-destructive/60 bg-destructive/10">
        <CardContent className="py-6 space-y-4">
          <p className="text-destructive font-medium text-sm">{message}</p>
          <Button onClick={onRetry} variant="outline" size="sm">
            Retry
          </Button>
        </CardContent>
      </Card>
    </>
  );
}

function DetailBody({ movie }: { movie: MovieDetail }) {
  const hasSchemaC = movie.schema_c_status === "done";
  const directorAndWriters = movie.crew.filter(
    (c) => c.job === "Director" || c.job === "Writer",
  );
  const topCast = movie.cast.slice(0, 6);
  const topQuotes = movie.quotes.slice(0, 5);

  return (
    <article className="space-y-10">
      <BackLink />
      <Hero movie={movie} />
      {movie.overview && (
        <Section label="Overview">
          <p className="text-base text-foreground/85 leading-relaxed">
            {movie.overview}
          </p>
        </Section>
      )}
      {hasSchemaC && movie.plot_summary && (
        <Section label="Plot summary">
          <p className="text-base text-foreground/85 leading-relaxed whitespace-pre-line">
            {movie.plot_summary}
          </p>
        </Section>
      )}
      {hasSchemaC && movie.atmosphere && (
        <Section label="Atmosphere">
          <p className="text-base text-foreground/85 leading-relaxed italic">
            {movie.atmosphere}
          </p>
        </Section>
      )}
      {hasSchemaC && movie.themes.length > 0 && (
        <Section label="Themes">
          <ChipList items={movie.themes} />
        </Section>
      )}
      {hasSchemaC && topQuotes.length > 0 && (
        <Section label="Quotes">
          <ul className="space-y-3">
            {topQuotes.map((q) => (
              <li key={q.quote_text} className="text-sm text-foreground/85">
                <span className="italic">"{q.quote_text}"</span>
                {q.attributed_to && (
                  <span className="text-muted-foreground">
                    {" "}
                    — {q.attributed_to}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}
      {topCast.length > 0 && (
        <Section label="Cast">
          <ul className="space-y-1.5 text-sm">
            {topCast.map((c) => (
              <li key={c.tmdb_url} className="text-foreground/85">
                <span className="font-medium">{c.name}</span>
                {c.character && (
                  <span className="text-muted-foreground">
                    {" "}
                    as {c.character}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}
      {directorAndWriters.length > 0 && (
        <Section label="Crew">
          <ul className="space-y-1.5 text-sm">
            {directorAndWriters.map((c) => (
              <CrewRow key={`${c.job}-${c.name}`} member={c} />
            ))}
          </ul>
        </Section>
      )}
    </article>
  );
}

function Hero({ movie }: { movie: MovieDetail }) {
  const metaParts = [
    movie.year?.toString(),
    movie.runtime ? `${movie.runtime} min` : null,
    movie.original_language?.toUpperCase(),
  ].filter(Boolean);

  return (
    <header className="flex flex-col gap-6 sm:flex-row">
      <Poster
        poster={movie.poster}
        size="full"
        alt={`${movie.title} poster`}
        className="w-40 shrink-0 self-center sm:w-48 sm:self-start"
      />
      <div className="flex-1 space-y-3">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-4xl font-bold tracking-tight leading-tight">
            {movie.title}
          </h1>
          {movie.vote_average !== null && (
            <span className="shrink-0 rounded-full bg-primary text-primary-foreground px-3 py-1 text-sm font-bold tracking-tight">
              {movie.vote_average.toFixed(1)}★
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 flex-wrap text-sm text-muted-foreground">
          {metaParts.length > 0 && (
            <span className="font-mono">{metaParts.join(" · ")}</span>
          )}
          {movie.genres.length > 0 && (
            <span className="flex items-center gap-1.5 flex-wrap">
              {movie.genres.map((g) => (
                <span
                  key={g.name}
                  className="rounded-full bg-primary/15 text-primary px-2 py-0.5 text-[11px] font-medium"
                >
                  {g.name}
                </span>
              ))}
            </span>
          )}
        </div>
        {movie.tagline && (
          <p className="italic text-muted-foreground text-base">
            "{movie.tagline}"
          </p>
        )}
      </div>
    </header>
  );
}

function Section({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-[11px] font-mono uppercase tracking-[0.12em] text-muted-foreground">
        {label}
      </h2>
      {children}
    </section>
  );
}

function ChipList({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className="rounded-full bg-primary/15 text-primary px-2.5 py-1 text-xs font-medium"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function CrewRow({ member }: { member: CrewMemberOut }) {
  return (
    <li className="text-foreground/85">
      <span className="text-muted-foreground">{member.job}: </span>
      <span className="font-medium">{member.name}</span>
    </li>
  );
}
