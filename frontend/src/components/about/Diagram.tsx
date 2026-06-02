import type { LucideIcon } from "lucide-react";
import {
  ArrowDown,
  Boxes,
  Brain,
  Cpu,
  Database,
  Image as ImageIcon,
  Search,
  Server,
  Sparkles,
} from "lucide-react";
import type { ReactNode } from "react";

type NodeProps = {
  icon?: LucideIcon;
  label: string;
  sub?: string;
  accent?: boolean;
};

function DiagramNode({ icon: Icon, label, sub, accent }: NodeProps) {
  return (
    <div
      className={`flex flex-1 flex-col items-center gap-1 rounded-xl border bg-card/80 px-3 py-2.5 text-center backdrop-blur-sm ${
        accent ? "border-primary/60" : "border-border"
      }`}
    >
      {Icon ? (
        <Icon
          className={
            accent ? "size-4 text-primary" : "size-4 text-muted-foreground"
          }
          aria-hidden="true"
        />
      ) : null}
      <span className="text-xs font-semibold leading-tight text-foreground">
        {label}
      </span>
      {sub ? (
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          {sub}
        </span>
      ) : null}
    </div>
  );
}

function Connector() {
  return (
    <div className="flex justify-center py-1.5" aria-hidden="true">
      <ArrowDown className="size-4 text-muted-foreground/40" />
    </div>
  );
}

function DiagramFrame({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-background/40 p-4 sm:p-6">
      {children}
    </div>
  );
}

export function ServingDiagram() {
  return (
    <DiagramFrame>
      <div className="flex">
        <DiagramNode icon={Search} label="User query" />
      </div>
      <Connector />
      <div className="flex">
        <DiagramNode label="React SPA" sub="TanStack" />
      </div>
      <Connector />
      <div className="flex">
        <DiagramNode icon={Server} label="nginx → FastAPI" />
      </div>
      <Connector />
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <DiagramNode accent label="/api/search" sub="vector · instant" />
          <Connector />
          <DiagramNode icon={Cpu} label="EmbeddingGemma" sub="768-dim" />
          <Connector />
          <DiagramNode icon={Boxes} label="pgvector" sub="HNSW · cosine" />
          <Connector />
          <DiagramNode accent label="Ranked films" sub="results" />
        </div>
        <div>
          <DiagramNode
            accent
            icon={Sparkles}
            label="/api/explain"
            sub="agentic · SSE"
          />
          <Connector />
          <DiagramNode
            icon={Brain}
            label="Groq llama-3.3-70b"
            sub="tool-calling"
          />
          <Connector />
          <DiagramNode label="schema C tools" sub="search · scenes · quotes" />
          <Connector />
          <DiagramNode accent label="Streamed answer" sub="SSE · cited" />
        </div>
      </div>
    </DiagramFrame>
  );
}

export function EtlDiagram() {
  return (
    <DiagramFrame>
      <div className="grid gap-3 sm:grid-cols-3">
        <DiagramNode icon={Database} label="TMDB" />
        <DiagramNode icon={Database} label="IMDb" />
        <DiagramNode icon={Database} label="Wikipedia" />
      </div>
      <Connector />
      <div className="flex">
        <DiagramNode label="Raw metadata" />
      </div>
      <Connector />
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <DiagramNode
            accent
            icon={Brain}
            label="Gemini"
            sub="schema C · 6 tables"
          />
          <Connector />
          <DiagramNode icon={Cpu} label="EmbeddingGemma" sub="768-dim" />
          <Connector />
          <DiagramNode
            accent
            icon={Boxes}
            label="pgvector"
            sub="13,556 chunks · HNSW"
          />
        </div>
        <div>
          <DiagramNode icon={ImageIcon} label="Posters" />
          <Connector />
          <DiagramNode label="Cloudflare R2" sub="BlurHash LQIP" />
        </div>
      </div>
    </DiagramFrame>
  );
}
