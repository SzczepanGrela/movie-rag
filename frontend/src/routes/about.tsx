import { createRoute } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";
import type { ReactNode } from "react";
import { EtlDiagram, ServingDiagram } from "@/components/about/Diagram";
import { MovieRagLogo } from "@/components/MovieRagLogo";
import { PageShell } from "@/components/PageShell";
import { Card, CardContent } from "@/components/ui/card";
import { rootRoute } from "@/routes/__root";

type Tool = { label: string; href: string };
type StackGroup = { title: string; tools: Tool[] };

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

function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-border bg-card/60 px-3.5 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground backdrop-blur-sm">
      {children}
    </span>
  );
}

function SectionHeading({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-4 font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
      {children}
    </h2>
  );
}

export function AboutPage() {
  return (
    <PageShell mainClassName="py-16 sm:py-24">
      <section className="mb-16 space-y-5 text-center">
        <h1 className="flex justify-center">
          <MovieRagLogo className="text-5xl sm:text-6xl text-foreground" />
        </h1>
        <p className="mx-auto max-w-xl text-base text-muted-foreground">
          A semantic search engine over 4,719 films. Describe a vibe, a plot, or
          a feeling — and find the movie, even when you can't recall its name.
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <Badge>4,719 films</Badge>
          <Badge>semantic + agentic</Badge>
        </div>
      </section>

      <section className="mb-16">
        <SectionHeading>The problem</SectionHeading>
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
        <SectionHeading>How it works · serving</SectionHeading>
        <p className="mb-6 text-sm leading-relaxed text-foreground/80">
          Two endpoints with different jobs.{" "}
          <code className="font-mono text-primary">/api/search</code> is pure
          vector similarity: instant, deterministic, no LLM.{" "}
          <code className="font-mono text-primary">/api/explain</code> is
          agentic: an LLM parses intent, calls retrieval tools over structured
          data, and streams a cited answer token by token.
        </p>
        <ServingDiagram />
      </section>

      <section className="mb-16">
        <SectionHeading>How it's built · ingestion</SectionHeading>
        <p className="mb-6 text-sm leading-relaxed text-foreground/80">
          Everything is precomputed offline. Metadata from TMDB, IMDb and
          Wikipedia is structured by an LLM into six tables (plot, scenes,
          themes, atmosphere, quotes, characters), embedded with EmbeddingGemma,
          and stored in pgvector. Posters go to Cloudflare R2 with BlurHash
          placeholders.
        </p>
        <EtlDiagram />
      </section>

      <section>
        <SectionHeading>Tech stack</SectionHeading>
        <div className="grid gap-3 sm:grid-cols-2">
          {STACK.map((group) => (
            <Card key={group.title}>
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
    </PageShell>
  );
}

export const aboutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/about",
  component: AboutPage,
});
