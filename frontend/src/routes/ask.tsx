import { createRoute, Link } from "@tanstack/react-router";
import { type FormEvent, useRef, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Turnstile, type TurnstileHandle } from "@/components/Turnstile";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  type CitedMovie,
  type ExplainToolCall,
  explainStream,
} from "@/lib/explain";
import { rootRoute } from "@/routes/__root";

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
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const turnstileRef = useRef<TurnstileHandle | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const q = draft.trim();
    if (!q || running) return;
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setAnswer("");
    setToolCalls([]);
    seqRef.current = 0;
    setCited([]);
    setError(null);
    setRunning(true);
    try {
      await explainStream(
        q,
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
        turnstileToken,
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError" && abortRef.current === ctrl) {
        setError("Something went wrong.");
      }
    } finally {
      if (abortRef.current === ctrl) setRunning(false);
      turnstileRef.current?.reset();
    }
  }

  return (
    <PageShell mainClassName="py-16 sm:py-24">
      <form
        onSubmit={handleSubmit}
        className="mb-8 flex gap-2 rounded-2xl border border-border bg-card/80 p-2 backdrop-blur-sm focus-within:border-primary/60"
      >
        <Input
          type="text"
          placeholder="What's that movie where a guy jumps from a plane…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="border-0 bg-transparent shadow-none focus-visible:ring-0 text-base"
          autoFocus
        />
        <Button
          type="submit"
          disabled={!draft.trim() || running}
          className="px-5 font-semibold"
        >
          {running ? "Thinking…" : "Ask"}
        </Button>
      </form>

      <Turnstile ref={turnstileRef} onToken={setTurnstileToken} />

      {toolCalls.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {toolCalls.map(({ call, seq }) => (
            <span
              key={seq}
              className="rounded-full border border-border bg-card/60 px-3 py-1 font-mono text-[11px] text-muted-foreground"
            >
              {call.tool}
            </span>
          ))}
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
              <Card className="transition-colors hover:border-primary/50">
                <CardContent className="flex items-baseline justify-between py-3">
                  <span className="font-semibold">{m.title}</span>
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
