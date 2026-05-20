# movie-rag

**RAG-powered movie search by plot, scenes, themes, and cast.**

Ask in plain English what you want to watch and get matching movies back — described by their actual plot, scenes, and atmosphere, not just genre tags.

> **Status:** M1.5 complete — backend deployed in production with auto-deploy CI/CD. Working toward v1; ETL (M2) next. See [`docs/roadmap.md`](docs/roadmap.md) for milestone progress.

[![CI/CD](https://github.com/SzczepanGrela/movie-rag/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/SzczepanGrela/movie-rag/actions)
[![Status](https://img.shields.io/website?down_color=red&down_message=down&label=movierag.grela.dev&up_color=brightgreen&up_message=up&url=https%3A%2F%2Fmovierag.grela.dev%2Fhealth)](https://stats.uptimerobot.com/XXQ6MTQxVH)

🌐 **Live:** [`https://movierag.grela.dev/health`](https://movierag.grela.dev/health) — `/health` is currently the only public endpoint; full v1 endpoints arrive milestone by milestone
📊 **Uptime:** [public status page](https://stats.uptimerobot.com/XXQ6MTQxVH)

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
| **M1: backend skeleton** | ✅ done | uv + FastAPI + async SQLAlchemy + pgvector + Docker + CI (ruff, mypy strict, pytest) |
| **M1.5: production deploy** | ✅ done | Auto-deploy from `main` → `movierag.grela.dev`; Cloudflare + NPM + Tailscale OAuth + GHCR |
| **M2-M8 (v1)** | 🔨 in progress | ETL ingestion → retrieval → frontend → AI streaming, end-to-end working app |
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
├── backend/                          FastAPI app, retrieval logic (in progress)
│   ├── app/                          Application code
│   ├── tests/                        Pytest integration tests
│   ├── Dockerfile                    Single-stage image (slim + uv)
│   └── pyproject.toml                Deps, ruff/mypy/pytest config
├── etl/                              One-shot scripts (M2+): TMDb / Wikipedia /
│                                     Gemini / images / embeddings
├── frontend/                         Vite + React app (M5+)
├── infra/
│   ├── deploy/                       VPS deploy scripts (self-updating)
│   ├── docker-compose.yml            Production base — GHCR image, healthcheck
│   └── docker-compose.override.yml   Dev override — local build + host ports
├── docs/
│   └── roadmap.md                    Milestone roadmap (canonical scope)
└── .github/
    └── workflows/
        └── ci-cd.yml                 Lint + typecheck + test + build-push + deploy
```

*(Structure being built out per milestone — current state may not yet contain all of these.)*

## Running locally

Prerequisites: Docker + Docker Compose, [`uv`](https://docs.astral.sh/uv/) for the Python side.

```bash
git clone https://github.com/SzczepanGrela/movie-rag.git
cd movie-rag

# local dev secrets — POSTGRES_PASSWORD is whatever you want
cp infra/.env.template infra/.env
# edit infra/.env

# external network is declared in compose; create it once locally
docker network create movierag_network

# start the stack (db + api)
cd infra
docker compose up -d --build

curl localhost:8000/health
# → {"status":"ok","db":"ok"}
```

Tests run directly via `uv`:

```bash
cd backend
uv sync
uv run pytest        # integration smoke against compose db
uv run ruff check .  # lint
uv run mypy          # strict type check
```

## License

To be decided — likely MIT for code, with attribution requirements for data sources (TMDb, IMDb, Wikipedia).

---

*Built by [Szczepan Grela](https://github.com/SzczepanGrela). Design and implementation guided by Claude (Anthropic) in a guided-learning workflow — see commit messages and design docs for context on decision-making.*
