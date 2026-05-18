# movie-rag

**RAG-powered movie search by plot, scenes, themes, and cast.**

Ask in plain English what you want to watch and get matching movies back — described by their actual plot, scenes, and atmosphere, not just genre tags.

> **Status:** design complete, implementation in progress. The first working iteration is being built. See [`docs/roadmap.md`](docs/roadmap.md) for milestone progress.

---

## What it does (v1 vision)

You type a natural-language query like:

> *"slow-burn thrillers from the 90s with an unreliable narrator"*
>
> *"movies with Tom Hardy where the main character is going through a crisis"*
>
> *"a movie with a scene where someone opens a closet and finds something unexpected"*

The system returns matching films with:
- Poster, title, year, genres
- The single scene or plot fragment that best matched your query
- A relevance score
- Optional one-click AI explanation of *why* each movie matches (streamed token-by-token, like ChatGPT)

## How it works

```
query
  │
  ├─ extract actor names locally (rapidfuzz)
  ├─ embed query with EmbeddingGemma (local, CPU)
  ├─ vector search in pgvector (filtered by actors if any)
  ├─ rerank top-K with bge-reranker-base (cross-encoder)
  └─ return top-N films with best-matching chunk

  optional:
  └─ "Explain match" → Gemini Flash streaming (SSE)
```

Underneath, each film has been pre-processed into structured content by Gemini Flash:
- 3 plot variants (concise / chronological / thematic)
- 15-30 scene descriptions with mood and characters
- Themes, atmosphere, memorable quotes, character descriptions

This rich content is split into ~220k chunks across 5000 films, each embedded as a 768-dim vector and stored in Postgres with pgvector.

## Tech stack

**Backend**
- Python 3.12 + FastAPI + SQLAlchemy + uv
- Postgres 17 + pgvector
- EmbeddingGemma (Google, ~300M parameters, multilingual, runs on CPU)
- bge-reranker-base (BAAI, cross-encoder for retrieval reranking)
- rapidfuzz (fuzzy actor name extraction)
- Gemini 1.5 Flash (for content generation in ETL and on-demand explanations)

**Frontend**
- Vite 6 + React 19 + TypeScript
- Tailwind CSS v4 + shadcn/ui
- TanStack Router + TanStack Query
- React Hook Form + zod
- Biome (lint + format)
- Bun runtime
- Server-Sent Events for streaming AI explanations

**Infrastructure**
- Docker single-image deploy (backend serves bundled React build)
- Cloudflare R2 (movie poster storage)
- Cloudflare DNS + edge proxy + Full Strict SSL + Turnstile (captcha for AI endpoint)
- Nginx Proxy Manager on VPS (TLS termination, vhost routing)
- Tailscale OAuth + SSH forced-command for CI/CD deploy
- GitHub Actions (lint, type-check, tests, build, push to GHCR, deploy)
- UptimeRobot (health monitoring)

**Data sources**
- TMDb API (metadata, cast, posters)
- IMDb non-commercial TSV dumps (ratings, IDs)
- Wikipedia API (plot sections)
- Gemini Flash (structured content generation)

## Architecture at a glance

```
Browser → Cloudflare (edge TLS, WAF, cache)
       → Nginx Proxy Manager (on VPS)
       → FastAPI container (single image, serves static React + API)
            ├─ EmbeddingGemma (in-process)
            ├─ bge-reranker-base (in-process)
            └─ Postgres + pgvector (sibling container)

Movie posters: Browser → Cloudflare R2 (direct)
AI explanation: FastAPI → Gemini Flash API → SSE stream → Browser
```

The implementation roadmap is in [`docs/roadmap.md`](docs/roadmap.md). Detailed architectural decisions were documented in a separate design spec prior to implementation and are kept local to the author's workspace (not in this public repo).

## Project status and phasing

| Phase | Status | What |
|---|---|---|
| **Design** | ✅ done | Full spec + 8-milestone roadmap |
| **v1: M1-M8** | 🔨 in progress | TMDb + Wikipedia + Gemini pipeline, end-to-end working app, deployed |
| **v2** | ⏳ planned | MAD (Movie Audio Descriptions) augmentation — 650 films enriched with professional audio descriptions |
| **v3** | 💭 idea | Subtitle → scene pipeline (if MAD proves insufficient) |

Current milestone: see `docs/roadmap.md` for which milestone is active.

## Goals beyond the product

This is also a **learning project**. The author had no prior React experience before starting it. The repo doubles as:
- A portfolio piece (publicly deployed, full CI/CD)
- A hands-on lesson in modern RAG (hybrid search, atomic chunking, reranking, structured LLM output)
- A first React app, building competence with the 2026 frontend stack

The codebase will evolve in public; design decisions and trade-offs are documented in the spec for full transparency.

## Repository structure

```
movie-rag/
├── backend/          FastAPI app, retrieval logic
├── frontend/         Vite + React app
├── etl/              One-shot scripts: TMDb fetch, Wikipedia fetch,
│                     Gemini generate, image pipeline, embedding load
├── infra/
│   ├── deploy/       deploy.sh, deploy-launcher.sh
│   └── docker-compose.yml
├── docs/
│   ├── roadmap.md    Milestone roadmap
│   └── superpowers/
│       └── specs/    Design specs
└── .github/
    └── workflows/    CI/CD pipelines
```

*(Structure being built out per milestone — current state may not yet contain all of these.)*

## Running locally

Setup instructions will be added once Milestone 1 (Repo skeleton + backend baseline) is complete. Watch this space.

## License

To be decided — likely MIT for code, with attribution requirements for data sources (TMDb, IMDb, Wikipedia).

---

*Built by [Szczepan Grela](https://github.com/SzczepanGrela). Design and implementation guided by Claude (Anthropic) in a guided-learning workflow — see commit messages and design docs for context on decision-making.*
