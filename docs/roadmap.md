# movie-rag — Roadmap (iteration milestones)

Implementation plan broken into 8 milestones (with M1.5 as a half-step inserted to deliver a production walking skeleton early). **Each milestone is its own work session** under guided-learning collaboration (the author writes the code, Claude guides and explains new concepts before they appear in the codebase).

Each milestone has:
- **Goal** — what we accomplish
- **Deliverables** — what concretely gets built (files, endpoints, working features)
- **Acceptance** — how we verify the milestone is done
- **Learning surface** — new concepts introduced (explained before coding)
- **Estimate** — planned sessions (1 session ≈ 2-4h of focused work)
- **Dependencies** — what must be done first

The detailed design (architecture, schemas, prompts, infrastructure decisions) was captured in a separate spec prior to implementation and is kept local to the author's workspace.

---

## Milestone 1 — Repo skeleton + backend baseline

**Goal:** Empty project becomes a working "hello world" application: FastAPI in Docker, Postgres in Docker, `/health` endpoint returns 200 OK with a DB ping.

**Deliverables:**
- Folder structure (`backend/`, `frontend/`, `etl/`, `infra/`, `docs/`)
- `backend/pyproject.toml` (uv) with FastAPI, SQLAlchemy, asyncpg, pydantic-settings
- `backend/app/main.py` with `/health` endpoint
- `backend/app/db.py` (async SQLAlchemy engine + session)
- `backend/Dockerfile` (single-stage initially — multi-stage added in M8)
- `infra/docker-compose.yml` with `api` + `db` (pgvector image)
- `.env.template` in repo, `.env` in `.gitignore`
- Linting: ruff + mypy config in `pyproject.toml`
- First pytest smoke test for `/health`
- `.github/workflows/ci.yml` minimum (lint + mypy + pytest)
- README updates with local-run instructions

**Acceptance:**
- `docker compose up -d` starts `api` + `db`, both healthy
- `curl localhost:8000/health` returns `{"status":"ok","db":"ok"}`
- `uv run pytest` passes
- CI green on push to main

**Learning surface (Python/backend):**
- uv (package manager — successor to pip/poetry)
- FastAPI basics (path operations, Pydantic responses)
- Async SQLAlchemy with asyncpg
- Docker Compose networking (service name as hostname)
- pydantic-settings (typed env vars)

**Estimate:** 1 session

**Dependencies:** none

---

## Milestone 1.5 — Production walking skeleton (CI/CD + deploy)

**Goal:** The hello-world FastAPI from M1 is **in production** at `movierag.grela.dev`. Push to main = auto-deploy. From this point on, every subsequent milestone ends with a real deploy.

**Why a separate milestone:** everything below is operational infrastructure work (Cloudflare, NPM, Tailscale, VPS user setup). The author is already familiar with the pattern from a prior project, so the learning value for the code itself is low. But the portfolio value is high: a recruiter sees a functioning pipeline from the first deployment. Separating it from M1 keeps M1 clean (one session for backend skeleton) and M8 clean (polish, not infra).

**Deliverables:**

VPS setup (manual, once):
- `movie-rag` user account on VPS with forced command in `~/.ssh/authorized_keys`
- SSH key pair (public on VPS, private → GitHub Secret `DEPLOY_SSH_KEY`)
- `usermod -aG docker movie-rag` (socket access)
- `/home/movie-rag/.env` (minimum: `DB_PASS` — rest added in later milestones)
- `/home/movie-rag/deploy-launcher.sh` (copied once manually — then self-updates from the repo)

Tailscale (once):
- OAuth client created in Tailscale admin → `TS_CLIENT_ID` + `TS_AUDIENCE` as GitHub Secrets
- Tag `tag:ci-vps` permits CI access to the VPS

Cloudflare (once):
- DNS A record `movierag.grela.dev` → VPS public IP, proxied (orange cloud)
- SSL/TLS mode: **Full (strict)**
- Origin cert generated for `movierag.grela.dev` (or `*.grela.dev`), 15-year validity
- Cache rules: `/api/*` bypass, statics standard (initial config — details extended when frontend joins in M6)

Nginx Proxy Manager (once, via UI):
- Proxy Host: `movierag.grela.dev` → `api:8000` (docker network alias)
- SSL: installed Cloudflare origin cert
- Custom location for `/api/explain`: `proxy_buffering off`, `proxy_read_timeout 300s` (prepares for SSE in M7 — works from day one even before the endpoint exists)
- NPM attached to docker network `movie-rag_default`

In the repo:
- `backend/Dockerfile` — single-stage Python 3.12-slim + uv install + COPY app (multi-stage with frontend build comes later in M6 or M8)
- `infra/docker-compose.yml` — services `api` (from GHCR image, healthcheck, networks) + `db` (pgvector); no host port exposure (NPM bridges via docker network)
- `infra/deploy/deploy-launcher.sh` — 1:1 pattern from prior project (curl `deploy.sh` from `raw.githubusercontent.com` + exec)
- `infra/deploy/deploy.sh` — lock file, curl `docker-compose.yml` from repo, `docker compose pull && up -d --remove-orphans`, image prune, health check loop (20 attempts × 5s)
- `.github/workflows/ci-cd.yml` — rename from `ci.yml` (from M1), add jobs:
  - `test` (existing from M1: ruff + mypy + pytest)
  - `smoke-build`: `docker build .` verification
  - `build-push` (on push to main only): `docker/build-push-action@v6` → GHCR with tags `latest` and `<short-sha>`, cache via GHA
  - `deploy` (after build-push): `tailscale/github-action@v4` + SSH key + `ssh -i key movie-rag@${VPS_HOST} bash deploy-launcher.sh`

GitHub Secrets set (via `gh secret set`):
- `TS_CLIENT_ID`, `TS_AUDIENCE` (Tailscale OAuth)
- `DEPLOY_SSH_KEY` (private key)
- `VPS_HOST`, `VPS_SSH_PORT`

Monitoring:
- UptimeRobot signup + monitor `https://movierag.grela.dev/health` every 5 min, email alert

**Acceptance:**
- `curl https://movierag.grela.dev/health` returns 200 OK with DB ping (through Cloudflare → NPM → FastAPI container on VPS)
- Push to main → GitHub Actions green → deploy job finishes with health check pass
- UptimeRobot green for 24h after first deploy
- Image in GHCR: `ghcr.io/szczepangrela/movie-rag:latest` + SHA tag, visible in `Packages` on the profile
- Forced command verified: `ssh movie-rag@vps "ls"` returns *deploy script output*, not a directory listing

**Learning surface:**
- GitHub Actions secrets management (`gh secret set` or UI)
- Tailscale OAuth flow in CI (vs regular auth key)
- SSH forced command security pattern (`command="..."` in `authorized_keys`)
- Cloudflare Origin Certs (vs Let's Encrypt) — what they provide, why they are convenient when Cloudflare proxy is active
- Nginx Proxy Manager — UI-driven configuration vs raw `nginx.conf`
- Docker layer caching in GHA (`cache-from: type=gha`)
- Health check loops in a deploy script (idempotency; no rollback in v1)

**Reference pattern:** the prior project's `ci-cd.yml` is used 1:1.
- **Carried over verbatim:** the jobs structure (`test → build-push → deploy`), `tailscale/github-action@v4`, SSH key setup, forced command pattern, deploy-launcher → deploy.sh self-update
- **Skipped in v1:** `paths-filter` (we have one image, no change detection needed), multi-image builds, Cloudflare cache purge (not needed yet, added in M8), Grafana/Prometheus monitoring stack
- **Net new:** nothing — the pattern is proven; we just use it

**Estimate:** 1-2 sessions (mostly operational: clicking through Cloudflare, NPM, Tailscale UIs + YAML edits)

**Dependencies:** M1 (needs a working backend + `/health` endpoint to deploy)

---

## Milestone 2 — ETL: TMDb + IMDb + Wikipedia ingestion

**Goal:** 5,000 movies with metadata and raw Wikipedia Plot text are in the database. Every ETL step is idempotent and resumable.

**Deliverables:**
- `etl/01_build_movie_list.py` — TMDb popular + top-rated with filters, output: 5,000 IMDb IDs (CSV or directly into `movies` with `etl_status='seeded'`)
- `etl/02_fetch_tmdb.py` — full metadata per movie: cast, crew, genres, overview, poster_path. Insert into `movies`, `actors`, `directors`, `genres` + joins
- `etl/03_fetch_imdb_tsv.py` — download IMDb TSV dumps (once), enrich tables with ratings/votes
- `etl/04_fetch_wikipedia.py` — Wikipedia API `action=parse&section=Plot`, polite User-Agent, rate limiting, write to `source_texts`. For missing → fallback to TMDb overview with a flag
- `etl/lib/` — shared modules: `tmdb_client.py`, `wikipedia_client.py`, `imdb_dumps.py`, `db.py`
- Alembic migrations for all tables from the design (except `chunks` — that comes in M3)
- Tests: unit tests for each client (mocked requests)

**Acceptance:**
- `python -m etl.01_build_movie_list` produces 5,000 rows in `movies` with `etl_status='seeded'`
- `python -m etl.02_fetch_tmdb` populates metadata (cast, crew, genres) for all of them
- `python -m etl.03_fetch_imdb_tsv` adds ratings/votes
- `python -m etl.04_fetch_wikipedia` fills `source_texts` with ~75% Wikipedia hit rate + ~25% TMDb-overview fallback
- Re-running any script skips up-to-date data (checks `updated_at`)

**Learning surface (Python/ETL):**
- HTTP clients with retry (httpx + tenacity)
- Rate limiting / polite throttling
- Bulk inserts in SQLAlchemy
- Alembic migrations
- Resumability patterns

**Estimate:** 2-3 sessions

**Dependencies:** M1.5 (from this point on, every push to main = auto-deploy in production)

---

## Milestone 3 — ETL: Gemini schema C + posters in R2 + embeddings

**Goal:** For every movie we have the structured content in the database (plot variants, scenes, themes, atmosphere, quotes, characters), posters in Cloudflare R2, and embeddings in pgvector.

**Deliverables:**
- `etl/05_generate_schema_c.py` — Gemini Flash with `response_schema` (Pydantic), retry, cost logging, writes to `plot_variants`, `scenes`, `themes`, `atmosphere`, `quotes`, `character_descriptions`
- `etl/06_images.py` — download TMDb posters → cwebp resize 2 sizes → upload to R2 (boto3 S3-compatible client), update URL in `movies`
- `etl/07_generate_embeddings.py` — load EmbeddingGemma once, chunk atomically per movie (~44 chunks), encode in batches, insert into `chunks` with pgvector column
- `etl/08_export_actors_cache.py` — query distinct cast, normalize names, export to `data/actors.pkl`
- `etl/09_sanity_checks.py` — report: row counts per table, missing-data summary, sample of 10 queries to verify embedding behavior
- Alembic migration for `chunks` (pgvector column + ivfflat index)

**Acceptance:**
- Schema C populated for all 5,000 movies (or `etl_failed` flag with a report for outliers)
- Posters in R2: 2 sizes × 5,000 = 10,000 objects
- `chunks` table: ~220k rows, each with a 768-dim vector
- Sanity-check report shows sensible numbers

**Learning surface (Python/ML):**
- Structured output from Gemini (response_schema)
- Prompt-engineering iterations
- Cost monitoring patterns
- Cloudflare R2 with boto3 (S3-compatible)
- `sentence-transformers` model loading + batch encode
- Image processing (Pillow + cwebp via subprocess)
- pgvector basics (ivfflat index, cosine ops)

**Estimate:** 2-3 sessions

**Dependencies:** M2

---

## Milestone 4 — Backend retrieval pipeline (pure vector)

**Architectural split (decided 2026-05-28):** retrieval is divided into two endpoints with different SLAs.
- **`/api/search`** — pure vector, no LLM, no quota, instant. Best-effort similarity over chunks. Lives in M4.
- **`/api/explain`** — LLM-driven, agentic, schema-C aware, rate-limited. Handles natural-language constraints (actor / year / genre filters) via tool-calling. Lives in M7.

This split keeps M4 fast and deterministic; the smart layer (LLM query understanding, structured filters, schema C synthesis) is the dedicated job of M7.

**Goal:** The endpoints `/api/search`, `/api/movies/:id`, `/api/quota` work end-to-end. A local test (curl/httpie/pytest) returns relevant results.

**Deliverables:**
- `backend/app/search/embedder.py` — `Embedder` Protocol + `GemmaEmbedder` (sentence-transformers EmbeddingGemma, `prompt_name="query"` for queries; pre-formatted `title: X (year) | text: <body>` for documents) + `FakeEmbedder` for hermetic tests
- `backend/app/search/service.py` — embed query → pgvector cosine top-K → dedup per movie → hydrate
- `backend/app/routers/search.py` — `POST /api/search` (Annotated DI for session + embedder)
- `backend/app/routers/movies.py` — `GET /api/movies/:id` with full hydration (movie + genres + cast top-15 + crew + source_texts + schema-C tables)
- `backend/app/routers/quota.py` — `GET /api/quota` (placeholder until M7 — `/api/search` itself has no quota; this surfaces `/api/explain` budget)
- `backend/app/middleware/rate_limit.py` — slowapi per IP (light per-route limits; the strict limit lives in M7 around `/api/explain`)
- Pytest fixtures + integration tests for each endpoint (TestClient + dependency_overrides)

**NOT in M4 anymore (moved to M7):**
- Fuzzy actor extraction (rapidfuzz over actor list) — replaced by LLM filter extraction in `/api/explain`
- Cross-encoder reranking (bge-reranker-base) — abandoned 2026-05-23 because the base model gives ~6s p50 on CPU VPS (60× regression). If reranking is reintroduced later it would be a distilled model (`ms-marco-MiniLM-L6-v2`) as its own slice; it is not blocking v1.

**Acceptance:**
- `POST /api/search` with `{"query": "samurai honor and revenge"}` returns sensible top-5 (semantic relevance) with latency < 100 ms p95 locally (model warm)
- `GET /api/movies/:id` returns full object with plot variants, scenes, characters, quotes
- Rate limit works (per-IP) — 429 on burst
- All integration tests pass

**Learning surface (Python/RAG):**
- Singleton pattern for heavy AI models (FastAPI lifespan + `app.state` + DI)
- Asymmetric query/document embedding (prompt-aware encoding)
- pgvector queries (`<=>` operator, HNSW index, `cosine_distance` ORM)
- Two-endpoint architecture (fast deterministic vs LLM-driven smart)
- FastAPI middleware patterns
- Integration testing against a test DB

**Estimate:** 2-3 sessions

**Status (2026-05-28):** `POST /api/search` shipped to production. `GET /api/movies/:id` and `/api/quota` still pending.

**Dependencies:** M3

---

## Milestone 5 — Frontend skeleton

**Goal:** `bun run dev` shows a working React application with multi-page routing, dark theme, and shadcn/ui baseline. Pages are empty placeholders but routing works.

**Deliverables:**
- `frontend/package.json` (bun) with the full stack from the design
- `frontend/vite.config.ts` with React Compiler plugin + TanStack Router plugin
- `frontend/biome.json` (lint + format)
- `frontend/tsconfig.json`
- `frontend/src/main.tsx` — entry point with RouterProvider, QueryClientProvider, ThemeProvider
- `frontend/src/routes/__root.tsx` — RootLayout (nav, container)
- `frontend/src/routes/index.tsx` — placeholder `SearchPage`
- `frontend/src/routes/movie.$id.tsx` — placeholder `MovieDetailPage`
- `frontend/src/routes/about.tsx` — `AboutPage` baseline
- `frontend/src/components/ui/` — shadcn init + Button, Card, Skeleton
- `frontend/app.css` with Tailwind v4 `@theme`
- Vitest setup + a sample component test
- README updates: how to run the frontend, folder structure

**Acceptance:**
- `bun install && bun run dev` starts the dev server, opens `localhost:5173`
- Navigation between `/`, `/movie/123`, `/about` works (TanStack Router)
- Dark mode is the default; toggle works
- `bun run biome ci` + `bun run tsc --noEmit` + `bun run test` pass
- New CI job `test-frontend` added to `.github/workflows/ci-cd.yml`

**Learning surface (frontend — large introduction, many concepts to explain):**
- **Vite** — bundler/dev server, how it differs from Webpack
- **React** — components, JSX, props, hooks (useState, useEffect)
- **TypeScript** in React — typing props, generics
- **TanStack Router** — type-safe routing, file-based routes, params
- **TanStack Query** — server state, queries, mutations, cache
- **Tailwind v4** — utility-first, class-based, CSS-first config
- **shadcn/ui** — why it is "not a library but a collection of components"
- **Biome** — replacement for ESLint + Prettier
- **Bun** — JS runtime + package manager

⚠ **Heaviest learning milestone.** Expect to slow down here and work through small tutorials/experiments before writing the actual app code.

**Estimate:** 2-3 sessions (with extra buffer for learning)

**Dependencies:** M1 (CI). Can proceed in parallel with M3 — the frontend skeleton does not need the backend retrieval to be working, only `/health`.

---

## Milestone 6 — Search UI + Movie detail page (backend integration)

**Goal:** End-to-end working movie search in the browser. The user types a query, gets results, clicks a card, sees the full movie page.

**Deliverables:**
- `frontend/src/components/SearchBar.tsx` — RHF + zod, debounce, submit
- `frontend/src/components/MovieCard.tsx` — poster, title, year, score, chunk preview, link
- `frontend/src/components/ResultsGrid.tsx` — responsive grid + LoadingSkeleton + EmptyState
- `frontend/src/components/MatchedActorsChip.tsx`
- `frontend/src/components/QuotaBanner.tsx`
- `frontend/src/api/` — typed API client (fetch wrappers + zod schemas for responses)
- `frontend/src/hooks/useSearch.ts` — TanStack Query hook
- `frontend/src/hooks/useMovie.ts` — TanStack Query hook
- `frontend/src/routes/index.tsx` — full `SearchPage` integrated
- `frontend/src/routes/movie.$id.tsx` — full `MovieDetailPage` with tabs (Plot/Scenes/Characters/Quotes), MovieHeader, BackButton preserving query state
- shadcn Tabs, Accordion, Carousel components installed
- Vitest tests for the most important components (MovieCard, ResultsGrid empty state)

**Acceptance:**
- Typing a query → submit → results grid (with mocked backend or real one from M4)
- Click on a MovieCard → navigation to `/movie/:id`, movie data shown across tabs
- Back button returns to `/?q=...` with results preserved
- Responsive: works on mobile (1 column) and desktop (3-4 columns)
- Loading skeletons visible during fetch
- Empty state visible for 0 results

**Learning surface (frontend):**
- React Hook Form + zod (forms + validation)
- TanStack Query queries with dependent params
- URL state via TanStack Router search params
- Conditional rendering patterns
- Loading states / skeletons / error boundaries
- shadcn Tabs / Accordion / Carousel components
- Responsive design with Tailwind breakpoints

**Estimate:** 2-3 sessions

**Dependencies:** M4 (backend retrieval), M5 (frontend skeleton)

---

## Milestone 7 — Agentic `/api/explain` (LLM tool-use over schema C)

**Architectural pivot (decided 2026-05-28):** `/api/explain` is no longer "stream a Gemini explanation for the search results already shown". It is the **smart entry point** of the system. It takes the raw user query, an LLM (a) parses intent + extracts structured filters (actor / year / genre / director), (b) calls retrieval tools internally (`/api/search` semantic + structured WHERE), (c) optionally pulls richer context from schema C (scenes, character_descriptions, quotes), (d) synthesizes a final answer with citations.

This handles the known weakness of bi-encoders: pure vector retrieval is poor at exact-match on proper nouns ("film z Nicolasem Cagem"). LLM query understanding solves it cleanly without needing fuzzy actor extraction or hand-tuned filters.

**Provider:** TBD between **Groq + llama-3.3-70b** (free tier, ~400ms, 30 req/min, strong tool calling) and **Google AI Studio + Gemini 2.0 Flash** (free tier, 15 req/min, strong PL). Decision deferred to the start of M7. Gemini Vertex remains used by the **ETL** (schema C generation) only — it is not used by `/api/explain`.

**Deliverables:**
- `backend/app/llm/client.py` — `LLMClient` Protocol + concrete (Groq or Gemini) + `FakeLLMClient` for tests
- `backend/app/llm/tools.py` — function-calling tool schemas: `search_movies(semantic_query, filters)`, `get_movie_detail(id)`, `get_movie_scenes(movie_id, query)`, `get_movie_quotes(movie_id, query)`
- `backend/app/services/turnstile.py` — verify token via Cloudflare API (kept for spam protection on the expensive endpoint)
- `backend/app/services/quota.py` — daily counter per IP (Redis or file-backed with lock)
- `backend/app/routers/explain.py` — `POST /api/explain` with `StreamingResponse` SSE (LLM step-by-step: tool calls + final synthesis)
- `backend/app/routers/quota.py` — full counter integration (replaces M4 placeholder)
- `frontend/src/components/TurnstileWidget.tsx` — Cloudflare Turnstile React widget
- `frontend/src/hooks/useExplainStream.ts` — custom hook with fetch + ReadableStream SSE parser
- `frontend/src/components/ExplainSection.tsx` — input + Turnstile + streaming results + cited movie cards
- Update `QuotaBanner` — shows current state polling `/api/quota`

**Pre-requisite (separate sub-slice, may land before M7):** **embed-scenes** — embedding the `scenes` table (105 k rows) so `get_movie_scenes` can do semantic lookup, not just LIKE. Decision pending — if not done, `get_movie_scenes` falls back to fetching all scenes for a movie and letting the LLM filter.

**Acceptance:**
- `POST /api/explain {"query": "film with Nicolas Cage where he jumps from a building"}` returns a structured answer naming the film(s) with citations
- Pure-vector `/api/search` continues to work independently (no LLM dependency, no shared quota)
- LLM tool calls validated server-side (no hallucinated filters — e.g. unknown actors → fall back gracefully)
- Backend rate limit (5/min per IP) + daily quota work; 429 with `resets_at`
- Turnstile gate rejects invalid tokens
- Provider error (rate limit / timeout) returns a graceful 503 with retry-after, not a crash

**Learning surface:**
- LLM tool calling / function calling
- Agentic RAG pattern (LLM as orchestrator over retrieval tools)
- Async generators in Python (`async def ... yield`)
- FastAPI `StreamingResponse` + SSE format
- ReadableStream parsing in the browser
- Structured filter extraction with validation against the DB
- AbortController for cleanup
- Cloudflare Turnstile integration

**Estimate:** 3-4 sessions (more than the old M7 because the agentic layer is the new heart of the system)

**Dependencies:** M6 (UI integration). Internally also depends on `GET /api/movies/:id` from M4 (used as a tool).

---

## Milestone 8 — Portfolio polish + production readiness

**Goal:** The project looks like a portfolio-ready piece. The README is an attractive pitch, the AboutPage explains it technically, Lighthouse is solid, edge cases are handled, backups run. The deploy pipeline (from M1.5) has been ready for ages — this milestone has no infrastructure surprises, only production finishing.

**Deliverables:**
- `frontend/src/routes/about.tsx` — final AboutPage content: project description, how the retrieval pipeline works, tech stack with links, **architecture diagram** (SVG export from draw.io or inline Mermaid)
- README final: production demo link `https://movierag.grela.dev`, screenshots / animated GIF of search flow, real "Running locally" section, architecture overview
- `backend/Dockerfile` upgraded to **multi-stage** (if not done in M6 with the frontend): bun build frontend → python copy to `/static` → pre-download AI models in the image layer (faster cold start on VPS)
- Cloudflare cache rules final for frontend statics (`/static/assets/*` immutable 1y, once frontend assets are present)
- Backup script `/opt/movie-rag-backup/backup-db.sh` + cron daily (`0 3 * * *`), retention 7 days (`find -mtime +7 -delete`)
- (Optional) Off-VPS backup to R2: `rclone copy /var/lib/movie-rag/backup remote-r2:movie-rag-backups`
- Lighthouse audit + fix obvious issues (Performance ≥ 80, Accessibility ≥ 90)
- Edge case review and fixes where needed:
  - empty search results (empty state)
  - explain quota exhausted (banner + disabled button + countdown)
  - DB down (`/health` 503)
  - missing R2 image (fallback placeholder)
  - long query (>200 chars) — frontend validation
- (Optional) Demo video / GIF in README
- `LICENSE` (MIT or other — author's call)
- Git tag `v1.0.0` on main after everything is in place

**Acceptance:**
- AboutPage publicly available with full content + architecture diagram
- README meets the "v1 success" criteria from the design
- Lighthouse: Performance ≥ 80, Accessibility ≥ 90, Best Practices ≥ 90
- Backup visible in `/var/lib/movie-rag/backup/` the day after enabling cron
- All edge cases have a test (manual or automated) documented
- Tag `v1.0.0` pushed

**Learning surface:**
- Lighthouse audits + typical optimizations (lazy load images, code splitting, font preload)
- Multi-stage Dockerfile + Docker layer caching strategies
- Cron + retention scripts (`find -mtime`, rclone)
- draw.io export to SVG (or Mermaid as inline alternative in README)
- Git tagging convention (semver)

**Estimate:** 1-2 sessions

**Dependencies:** M7 (all functionality must be in place). The entire deploy infrastructure (CI/CD, NPM, Cloudflare, Tailscale) is **already in place since M1.5** — this milestone is cleanup and polish only.

---

## After v1 — next phases

### v2: MAD augmentation

Download and integrate the MAD dataset (650 movies with professional audio descriptions) as additional chunks in the database. A/B-test retrieval quality with/without MAD.

**Requires:** registration + NDA with the MAD team.

### v3: Subtitle pipeline (optional)

If MAD proves insufficient — an OpenSubtitles VIP → Gemini → structured scenes pipeline. Treated as a separate sub-project with its own ETL.

---

## Notes on pace

- **Estimates are optimistic.** A first React project always takes longer than expected. M5 and M6 will likely take 2× the plan.
- **Each milestone is a checkpoint.** After finishing one: short review, commit, optionally git tag (`v1.0.0-m1`, etc.).
- **Some milestones can run in parallel** — e.g. M5 (frontend skeleton) can proceed alongside M3 (ETL Gemini); they do not depend on each other.
- **When something goes sideways — go back to the design.** The spec is always authoritative; in case of milestone-vs-spec conflict, the spec wins.

---

## Status

- **Current milestone:** M4 in progress
- **Done:** M1, M1.5, M2 (A–G), M3 (chunking + EmbeddingGemma + pgvector HNSW), schema-C generation (Gemini Vertex → 6 tables, 4 706 / 4 719 movies; data backfilled to prod-DB on 2026-05-23), M4 minimal (`POST /api/search` shipped, prompt-aware embed re-run on 13 556 chunks).
- **Open inside M4:** `GET /api/movies/:id`, `/api/quota` placeholder, per-IP rate limit.
- **Open architectural pivots:** see updated M4 and M7 sections above (clean split: pure vector `/api/search` vs agentic `/api/explain`).
- **Suggested next step:** `GET /api/movies/:id` — small focused slice, unblocks both M5 frontend and the `get_movie_detail` tool in M7.
