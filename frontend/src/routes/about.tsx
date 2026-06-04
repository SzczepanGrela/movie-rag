import { createRoute, Link } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";
import { EtlDiagram, ServingDiagram } from "@/components/about/Diagram";
import { MovieRagLogo } from "@/components/MovieRagLogo";
import { PageShell } from "@/components/PageShell";
import { SectionHeading } from "@/components/SectionHeading";
import { StatusPill } from "@/components/StatusPill";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cardHover } from "@/lib/ui";
import { rootRoute } from "@/routes/__root";

type Tool = { label: string; href: string };
type StackGroup = { title: string; tools: Tool[] };

const METRICS = [
  { value: "4,719", label: "films" },
  { value: "118,730", label: "vectors" },
  { value: "768", label: "dim" },
  { value: "2", label: "endpoints" },
];

const STACK: StackGroup[] = [
  {
    title: "Backend",
    tools: [
      { label: "FastAPI", href: "https://fastapi.tiangolo.com/" },
      { label: "SQLAlchemy", href: "https://www.sqlalchemy.org/" },
      { label: "asyncpg", href: "https://github.com/MagicStack/asyncpg" },
      { label: "pgvector", href: "https://github.com/pgvector/pgvector" },
      { label: "Pydantic", href: "https://docs.pydantic.dev/" },
    ],
  },
  {
    title: "Frontend",
    tools: [
      { label: "React", href: "https://react.dev/" },
      { label: "Vite", href: "https://vite.dev/" },
      { label: "TanStack Router", href: "https://tanstack.com/router" },
      { label: "TanStack Query", href: "https://tanstack.com/query" },
      { label: "Tailwind CSS", href: "https://tailwindcss.com/" },
      { label: "shadcn/ui", href: "https://ui.shadcn.com/" },
      { label: "Bun", href: "https://bun.sh/" },
    ],
  },
  {
    title: "Data & ML",
    tools: [
      {
        label: "EmbeddingGemma",
        href: "https://huggingface.co/google/embeddinggemma-300m",
      },
      { label: "Gemini", href: "https://ai.google.dev/" },
      { label: "Groq", href: "https://groq.com/" },
    ],
  },
  {
    title: "Infra",
    tools: [
      { label: "Docker", href: "https://www.docker.com/" },
      {
        label: "Cloudflare R2",
        href: "https://www.cloudflare.com/developer-platform/r2/",
      },
      {
        label: "Cloudflare Turnstile",
        href: "https://www.cloudflare.com/products/turnstile/",
      },
      {
        label: "Nginx Proxy Manager",
        href: "https://nginxproxymanager.com/",
      },
      { label: "Tailscale", href: "https://tailscale.com/" },
      {
        label: "GitHub Actions",
        href: "https://github.com/features/actions",
      },
    ],
  },
];

export function AboutPage() {
  return (
    <PageShell mainClassName="py-16 sm:py-24">
      <section className="mb-16 space-y-6 text-center">
        <h1 className="sr-only">About MovieRAG</h1>
        <div className="relative flex justify-center">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 -z-10"
            style={{
              background:
                "radial-gradient(ellipse at center, rgba(245,213,71,0.14), transparent 70%)",
            }}
          />
          <MovieRagLogo className="text-5xl sm:text-6xl text-foreground" />
        </div>
        <div className="flex justify-center">
          <StatusPill dot>Semantic + agentic · 4,719 films</StatusPill>
        </div>
        <p className="mx-auto max-w-xl text-base text-muted-foreground">
          A semantic search engine over 4,719 films. Describe a vibe, a plot, or
          a feeling — and find the movie, even when you can't recall its name.
        </p>
        <dl className="mx-auto grid max-w-xl grid-cols-2 gap-3 sm:grid-cols-4">
          {METRICS.map((m) => (
            <div
              key={m.label}
              className="flex flex-col-reverse rounded-xl border border-border bg-card/40 px-3 py-4"
            >
              <dt className="mt-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {m.label}
              </dt>
              <dd className="text-2xl font-bold tracking-tight text-primary">
                {m.value}
              </dd>
            </div>
          ))}
        </dl>
        <div className="flex justify-center pt-1">
          <Button asChild size="lg">
            <Link to="/">Try it live</Link>
          </Button>
        </div>
      </section>

      <section className="mb-16">
        <SectionHeading index="01">The problem</SectionHeading>
        <div className="space-y-3 text-sm leading-relaxed text-foreground/80">
          <p>
            Keyword search breaks the moment you don't know the exact words. Ask
            for <em>"a film where a guy jumps off a building"</em> and a literal
            index returns nothing useful.
          </p>
          <p>
            MovieRAG embeds the <em>meaning</em> of each film and matches it
            against the meaning of your query. For trickier asks — a specific
            actor, a year, or "that scene where…" — an LLM reads the question,
            calls retrieval tools, and reasons over structured plot data to name
            the film.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <SectionHeading index="02">How it works · serving</SectionHeading>
        <p className="mb-6 text-sm leading-relaxed text-foreground/80">
          Two endpoints with different jobs.{" "}
          <code className="font-mono text-primary">/api/search</code> is pure
          vector similarity: instant, deterministic, no LLM — reach for it to
          browse films that match a vibe, a plot, or a single scene.{" "}
          <code className="font-mono text-primary">/api/explain</code> is
          agentic: an LLM parses intent, calls retrieval tools over structured
          data, and streams a cited answer token by token — reach for it when
          you want one film reasoned out and named from a description you can't
          quite place.
        </p>
        <ServingDiagram />
      </section>

      <section className="mb-16">
        <SectionHeading index="03">How it's built · ingestion</SectionHeading>
        <p className="mb-6 text-sm leading-relaxed text-foreground/80">
          Everything is precomputed offline. An LLM (Gemini) reads the raw
          metadata from TMDB, IMDb and Wikipedia and structures it into six
          tables — plot, scenes, themes, atmosphere, quotes and characters. The
          plot, the overview and every individual scene are embedded with
          EmbeddingGemma into pgvector, so a film can be matched by its whole
          story or by a single remembered scene; the remaining tables feed the
          agent's retrieval tools. Posters go to Cloudflare R2 with BlurHash
          placeholders.
        </p>
        <EtlDiagram />
      </section>

      <section>
        <SectionHeading index="04">Tech stack</SectionHeading>
        <div className="grid gap-3 sm:grid-cols-2">
          {STACK.map((group) => (
            <Card key={group.title} className={cardHover}>
              <CardContent className="py-4">
                <p className="mb-2.5 text-sm font-semibold text-foreground">
                  {group.title}
                </p>
                <ul className="flex flex-wrap gap-1.5">
                  {group.tools.map((tool) => (
                    <li key={tool.label}>
                      <a
                        href={tool.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-full border border-border bg-card/60 px-2.5 py-0.5 text-xs text-muted-foreground hover:border-primary/50 hover:text-primary transition-colors"
                      >
                        {tool.label}
                        <ExternalLink className="size-2.5" aria-hidden="true" />
                      </a>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-16 rounded-2xl border border-border bg-card/40 px-6 py-10 text-center">
        <h2 className="text-xl font-semibold tracking-tight">
          Find your next film
        </h2>
        <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
          Search by vibe, or let the AI reason it out from a half-remembered
          scene.
        </p>
        <div className="mt-5 flex justify-center gap-3">
          <Button asChild>
            <Link to="/">Search</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/ask">Ask AI</Link>
          </Button>
        </div>
      </section>
    </PageShell>
  );
}

export const aboutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/about",
  component: AboutPage,
});
