import type { PosterData } from "@/lib/api";

export type ExplainToolCall = { tool: string; args: Record<string, unknown> };
export type CitedMovie = {
  movie_id: number;
  title: string;
  year: number | null;
  poster: PosterData | null;
};
export type ExplainDone = { took_ms: number; iterations: number };

export type ExplainHandlers = {
  onToolCall: (t: ExplainToolCall) => void;
  onChunk: (text: string) => void;
  onCitedMovie: (m: CitedMovie) => void;
  onError: (code: string, message?: string) => void;
  onDone: (d: ExplainDone) => void;
};

function dispatchEvent(block: string, handlers: ExplainHandlers): void {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return;
  const data = JSON.parse(dataLines.join("\n"));
  switch (event) {
    case "tool_call":
      handlers.onToolCall(data);
      break;
    case "chunk":
      handlers.onChunk(data.text ?? "");
      break;
    case "cited_movie":
      handlers.onCitedMovie(data);
      break;
    case "error":
      handlers.onError(data.code, data.message);
      break;
    case "done":
      handlers.onDone(data);
      break;
  }
}

export async function explainStream(
  query: string,
  handlers: ExplainHandlers,
  signal?: AbortSignal,
  turnstileToken?: string | null,
): Promise<void> {
  const res = await fetch("/api/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, turnstile_token: turnstileToken ?? null }),
    signal,
  });
  if (res.status === 403) {
    handlers.onError(
      "turnstile_failed",
      "Please verify you're human and retry.",
    );
    return;
  }
  if (res.status === 429) {
    handlers.onError("rate_limited", "Too many requests — try again shortly.");
    return;
  }
  if (res.status === 503) {
    let detail = "";
    try {
      detail = (await res.json()).detail ?? "";
    } catch {
      detail = "";
    }
    if (detail === "service_busy") {
      handlers.onError(
        "service_busy",
        "The assistant is busy right now — try again later.",
      );
    } else {
      handlers.onError("unavailable", "AI explain is not configured.");
    }
    return;
  }
  if (!res.ok || !res.body) {
    handlers.onError("http_error", `Request failed: ${res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep = buffer.indexOf("\n\n");
    while (sep !== -1) {
      const block = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      if (block.trim()) dispatchEvent(block, handlers);
      sep = buffer.indexOf("\n\n");
    }
  }
  if (buffer.trim()) dispatchEvent(buffer, handlers);
}
