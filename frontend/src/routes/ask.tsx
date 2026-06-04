import { createRoute, Link } from "@tanstack/react-router";
import { Clock, Sparkles } from "lucide-react";
import { type FormEvent, useRef, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Poster } from "@/components/Poster";
import { StatusPill } from "@/components/StatusPill";
import { Turnstile, type TurnstileHandle } from "@/components/Turnstile";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  type CitedMovie,
  type ExplainToolCall,
  explainStream,
} from "@/lib/explain";
import { cardHover } from "@/lib/ui";
import { rootRoute } from "@/routes/__root";

const PROMPTS = [
  "What's the movie where a man relives the same day over and over?",
  "A thief who enters people's dreams to steal secrets — what's the film?",
  "What's that film with a lighthouse keeper and his assistant going mad?",
];

export function AskPage() {
  const [draft, setDraft] = useState("");
  const [answer, setAnswer] = useState("");
  const [toolCalls, setToolCalls] = useState<
    { call: ExplainToolCall; seq: number }[]
  >([]);
  const seqRef = useRef(0);
  const [cited, setCited] = useState<CitedMovie[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const turnstileRef = useRef<TurnstileHandle | null>(null);

  async function runQuery(q: string) {
    const query = q.trim();
    if (!query || running) return;
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setDraft(query);
    setAnswer("");
    setToolCalls([]);
    seqRef.current = 0;
    setCited([]);
    setError(null);
    setRunning(true);

    let token: string | null;
    try {
      token = (await turnstileRef.current?.execute()) ?? null;
    } catch {
      if (abortRef.current === ctrl) {
        setError("Verification failed. Please try again.");
        setRunning(false);
      }
      return;
    }

    try {
      await explainStream(
        query,
        {
          onToolCall: (t) => {
            const seq = seqRef.current++;
            setToolCalls((prev) => [...prev, { call: t, seq }]);
          },
          onChunk: (text) => setAnswer((prev) => prev + text),
          onCitedMovie: (m) =>
            setCited((prev) =>
              prev.some((c) => c.movie_id === m.movie_id) ? prev : [...prev, m],
            ),
          onError: (_code, message) =>
            setError(message ?? "Something went wrong."),
          onDone: () => {},
        },
        ctrl.signal,
        token,
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError" && abortRef.current === ctrl) {
        setError("Something went wrong.");
      }
    } finally {
      if (abortRef.current === ctrl) setRunning(false);
    }
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void runQuery(draft);
  }

  return (
    <PageShell mainClassName="py-16 sm:py-24">
      <header className="mb-10 space-y-5 text-center">
        <div className="flex justify-center">
          <StatusPill dot>Agentic · tool-using LLM</StatusPill>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Ask <span className="text-primary">AI</span>
        </h1>
        <p className="mx-auto max-w-md text-base text-muted-foreground">
          Can't quite place a film? Ask in plain words — the AI reasons over the
          data, names it, and cites its sources.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="mb-10 flex gap-2 rounded-2xl border border-border bg-card/80 p-2 shadow-[0_8px_32px_-12px_rgba(0,0,0,0.6)] backdrop-blur-sm focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/25 transition"
      >
        <Input
          type="text"
          placeholder="What's that movie where…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="border-0 bg-transparent shadow-none focus-visible:ring-0 text-base placeholder:text-muted-foreground/60"
          autoFocus
        />
        <Button
          type="submit"
          disabled={!draft.trim() || running}
          className="gap-1.5 px-5 font-semibold"
        >
          <Sparkles className="size-4" aria-hidden="true" />
          {running ? "Thinking…" : "Ask"}
        </Button>
      </form>

      <Turnstile ref={turnstileRef} />

      {running && !answer && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-border bg-card/40 px-4 py-3 text-sm text-muted-foreground">
          <Clock
            className="mt-0.5 size-4 shrink-0 text-primary"
            aria-hidden="true"
          />
          <span>
            This usually takes{" "}
            <span className="font-medium text-foreground">10–15s</span>.
            MovieRAG runs its semantic model on a CPU-only server (no GPU), so
            the AI runs a few searches before answering.
          </span>
        </div>
      )}

      {!running && !answer && !error && toolCalls.length === 0 && (
        <div className="mb-6 space-y-3">
          <p className="text-center font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            Try asking
          </p>
          <div className="flex flex-col gap-2">
            {PROMPTS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => void runQuery(p)}
                className={`rounded-xl border border-border bg-card/60 px-4 py-2.5 text-left text-sm text-muted-foreground hover:text-primary hover:border-primary/50 ${cardHover}`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {toolCalls.length > 0 && (
        <div className="mb-4 space-y-2">
          <p className="px-1 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            {running ? "Working…" : "Steps"}
          </p>
          <div className="flex flex-wrap gap-2">
            {toolCalls.map(({ call, seq }) => (
              <span
                key={seq}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 font-mono text-[11px] text-muted-foreground"
              >
                <span className="text-primary">{seq + 1}</span>
                {call.tool}
              </span>
            ))}
          </div>
        </div>
      )}

      {error && (
        <Card className="mb-4 border-destructive/60 bg-destructive/10">
          <CardContent className="py-4 text-sm font-medium text-destructive">
            {error}
          </CardContent>
        </Card>
      )}

      {answer && (
        <Card className="mb-6">
          <CardContent className="whitespace-pre-wrap py-6 text-sm leading-relaxed text-foreground/90">
            {answer}
          </CardContent>
        </Card>
      )}

      {cited.length > 0 && (
        <div className="space-y-2">
          <p className="px-1 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            Cited films
          </p>
          {cited.map((m) => (
            <Link
              key={m.movie_id}
              to="/movies/$id"
              params={{ id: String(m.movie_id) }}
              className="block"
            >
              <Card className={cardHover}>
                <CardContent className="flex items-center gap-3 py-3">
                  <Poster
                    poster={m.poster}
                    size="thumb"
                    alt={`${m.title} poster`}
                    className="w-10 shrink-0"
                  />
                  <span className="flex-1 font-semibold">{m.title}</span>
                  {m.year ? (
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {m.year}
                    </span>
                  ) : null}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </PageShell>
  );
}

export const askRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ask",
  component: AskPage,
});
