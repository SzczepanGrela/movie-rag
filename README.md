# movie-rag

**Semantic movie search — find a film by its vibe, its plot, or a single scene you remember.**

Keyword search breaks the moment you don't know the exact words. MovieRAG embeds the *meaning* of 4,719 films — their plots, their atmosphere, and every individual scene — so you can search the way you actually remember movies.

[![CI/CD](https://github.com/SzczepanGrela/movie-rag/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/SzczepanGrela/movie-rag/actions)
[![Status](https://img.shields.io/website?down_color=red&down_message=down&label=movierag.grela.dev&up_color=brightgreen&up_message=up&url=https%3A%2F%2Fmovierag.grela.dev%2Fhealth)](https://stats.uptimerobot.com/XXQ6MTQxVH)

🌐 **Live:** [movierag.grela.dev](https://movierag.grela.dev) &nbsp;·&nbsp; 📊 **Uptime:** [status page](https://stats.uptimerobot.com/XXQ6MTQxVH)

---

## Two ways to search

The app exposes two complementary modes — they share the same vector index but answer different needs.

| | **Search** · `/api/search` | **Ask AI** · `/api/explain` |
|---|---|---|
| **What it is** | pure vector similarity — instant, deterministic, no LLM | an agentic LLM that reasons over the data and cites its sources |
| **Good for** | browsing films that match a **vibe**, a **plot**, or a single remembered **scene** | naming **one** film you can't quite place — fuzzy, multi-detail, "what's that movie where…?" |
| **You get** | a ranked list with posters and relevance scores | a single reasoned answer, streamed token by token, with cited films |
| **Cost / speed** | free, instant (~0.4 s) | rate-limited, ~10–15 s (a few reasoning steps) |

A query like *"children hide from raptors in a kitchen"* or *"a lonely robot finds friendship"* is a job for **Search**. A tip-of-the-tongue question like *"what's the film where a man relives the same day over and over?"* — where the right answer might not be the closest vector — is where **Ask AI** earns its latency.

## How it works

**Serving** — two endpoints, two jobs:

```
/api/search  (instant, no LLM)
  query → EmbeddingGemma (CPU) → pgvector cosine search over 118,730 vectors
        → per-kind weighting (plot · overview · scene) + best-chunk-per-movie
        → ranked films, each with the fragment that matched

/api/explain  (agentic, SSE, Turnstile-gated)
  query → Groq llama-3.3-70b → tool calls (search_movies, get_movie_detail,
          get_movie_scenes, get_movie_quotes) → reasoned, cited answer streamed
```

**Ingestion** — everything is precomputed offline:

```
TMDB · IMDb · Wikipedia → raw metadata
  ├─ Gemini 2.5 Flash → schema C: plot variants, 15–30 scene descriptions
  │                     (with mood + characters), themes, atmosphere, quotes
  ├─ EmbeddingGemma → embed plot + overview + every scene → pgvector
  │                   (768-dim, HNSW index, cosine)
  └─ posters → Cloudflare R2 (+ BlurHash placeholders for zero layout shift)
```

The plot, the TMDB overview, and each individual scene are embedded into the index — so a film can be matched by its whole story *or* by one specific moment. The remaining structured tables (quotes, characters, themes) feed the agent's retrieval tools rather than the vector search.

## By the numbers

| | |
|---|---|
| Films | 4,719 |
| Vectors in the index | 118,730 (plot · overview · scene) |
| Embedding dimension | 768 (EmbeddingGemma) |
| Public endpoints | 2 (`/api/search`, `/api/explain`) |

## Tech stack

**Backend** — Python 3.12 · FastAPI · async SQLAlchemy + asyncpg · Postgres 16 + pgvector · EmbeddingGemma (`google/embeddinggemma-300m`, runs on CPU) · Groq `llama-3.3-70b` for the agentic endpoint (OpenAI-compatible client) · Pydantic · uv · ruff + mypy (strict).

**Frontend** — Vite 8 · React 19 · TypeScript · Tailwind CSS v4 · shadcn/ui · TanStack Router + Query · Bun · Biome · Server-Sent Events for streaming answers.

**Data & ML** — Gemini 2.5 Flash (offline schema-C generation) · EmbeddingGemma (embeddings) · Groq (serving-time reasoning).

**Infrastructure** — Docker · Cloudflare (DNS, edge TLS, R2 object storage, Turnstile captcha on the AI endpoint) · Nginx Proxy Manager on a VPS · Tailscale OAuth + SSH for CI/CD deploys · GitHub Actions (lint, type-check, tests, build, push to GHCR, deploy) · UptimeRobot.

**Data sources** — TMDB (metadata, cast, posters), IMDb non-commercial dumps (IDs, ratings), Wikipedia (plot sections), Gemini (structured content).

## Architecture at a glance

```
Browser ─→ Cloudflare (edge TLS, Turnstile)
        ─→ Nginx Proxy Manager (VPS)
        ─→ frontend container (nginx: serves the React SPA,
        │     proxies /api + /health to the api over the docker network)
        ─→ api container (FastAPI; EmbeddingGemma in-process)
              └─ Postgres + pgvector (sibling container)

Posters:      Browser ─→ Cloudflare R2 (movierag-assets.grela.dev)
Ask AI:       api ─→ Groq API ─→ SSE stream ─→ Browser
```

Migrations run on every deploy (`alembic upgrade head`) before the new api serves traffic. Detailed design specs and the implementation roadmap are kept in the author's local workspace; [`docs/roadmap.md`](docs/roadmap.md) tracks public milestone scope.

## Running locally

Prerequisites: Docker + Docker Compose, [`uv`](https://docs.astral.sh/uv/) (Python), and [Bun](https://bun.sh/) (frontend).

```bash
git clone https://github.com/SzczepanGrela/movie-rag.git
cd movie-rag

# local dev secrets — set POSTGRES_PASSWORD to anything for local use
cp infra/.env.template infra/.env   # then edit

# the compose network is declared external; create it once
docker network create movierag_network

# start db + api (+ frontend) with the dev override
cd infra
docker compose up -d --build

curl localhost:8000/health   # → {"status":"ok","db":"ok"}
```

Note: `/api/search` and `/api/explain` need a populated database (the offline ETL builds the vector index). `/api/explain` is skipped without a `GROQ_API_KEY`, and its Turnstile check is bypassed locally when no `TURNSTILE_SECRET` is set.

Checks (run in `backend/` and `etl/` for Python, `frontend/` for the web app):

```bash
# backend / etl
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest

# frontend
bun install
bunx biome check . && bunx tsc --noEmit && bun run build
```

## Status

Live and deployed: semantic search, scene-level search, the agentic Ask-AI endpoint, posters, and a full React frontend are all in production behind CI/CD auto-deploy from `main`. Remaining polish (a LICENSE, DB backups, a Lighthouse pass, a `v1.0.0` tag) is tracked in the roadmap.

## License

To be decided — likely MIT for the code, with attribution requirements for the data sources (TMDB, IMDb, Wikipedia).

---

*Built by [Szczepan Grela](https://github.com/SzczepanGrela) as a portfolio and learning project — a first React app and a hands-on tour of modern RAG (atomic chunking, asymmetric embeddings, agentic tool-use, structured LLM output). Design and implementation were carried out in a guided-learning workflow with Claude (Anthropic).*
