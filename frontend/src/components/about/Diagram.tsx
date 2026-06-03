import type { LucideIcon } from "lucide-react";
import {
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

type Role = "source" | "compute" | "store";

const ROLE_BOX: Record<Role, string> = {
  source: "border-border bg-card/80",
  compute: "border-primary/60 bg-primary/5",
  store: "border-primary bg-primary/10",
};
const ROLE_ICON: Record<Role, string> = {
  source: "text-muted-foreground",
  compute: "text-primary",
  store: "text-primary",
};

type NodeProps = {
  icon?: LucideIcon;
  label: string;
  sub?: string;
  kind?: Role;
};

function DiagramNode({ icon: Icon, label, sub, kind = "source" }: NodeProps) {
  return (
    <div
      className={`flex flex-1 flex-col items-center gap-1 rounded-xl border px-3 py-2.5 text-center backdrop-blur-sm transition-all motion-safe:hover:-translate-y-0.5 ${ROLE_BOX[kind]}`}
    >
      {Icon ? (
        <Icon className={`size-4 ${ROLE_ICON[kind]}`} aria-hidden="true" />
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

function Rail() {
  return <div className="mx-auto h-5 w-px bg-border" aria-hidden="true" />;
}

function BranchLabel({ children }: { children: ReactNode }) {
  return (
    <p className="mb-2 text-center font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
      {children}
    </p>
  );
}

function LegendItem({ box, label }: { box: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`size-2.5 rounded border ${box}`} aria-hidden="true" />
      {label}
    </span>
  );
}

function Legend() {
  return (
    <div className="mt-4 flex flex-wrap justify-center gap-x-5 gap-y-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
      <LegendItem box={ROLE_BOX.source} label="source" />
      <LegendItem box={ROLE_BOX.compute} label="compute" />
      <LegendItem box={ROLE_BOX.store} label="store" />
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
      <Rail />
      <div className="flex">
        <DiagramNode label="React SPA" sub="TanStack" />
      </div>
      <Rail />
      <div className="flex">
        <DiagramNode icon={Server} label="nginx → FastAPI" />
      </div>
      <Rail />
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <BranchLabel>/api/search · vector</BranchLabel>
          <DiagramNode kind="compute" label="/api/search" sub="instant" />
          <Rail />
          <DiagramNode
            icon={Cpu}
            kind="compute"
            label="EmbeddingGemma"
            sub="768-dim"
          />
          <Rail />
          <DiagramNode
            icon={Boxes}
            kind="store"
            label="pgvector"
            sub="HNSW · cosine"
          />
          <Rail />
          <DiagramNode kind="store" label="Ranked films" sub="results" />
        </div>
        <div>
          <BranchLabel>/api/explain · agentic</BranchLabel>
          <DiagramNode
            icon={Sparkles}
            kind="compute"
            label="/api/explain"
            sub="SSE"
          />
          <Rail />
          <DiagramNode
            icon={Brain}
            kind="compute"
            label="Groq llama-3.3-70b"
            sub="tool-calling"
          />
          <Rail />
          <DiagramNode label="schema C tools" sub="search · scenes · quotes" />
          <Rail />
          <DiagramNode kind="store" label="Streamed answer" sub="SSE · cited" />
        </div>
      </div>
      <Legend />
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
      <Rail />
      <div className="flex">
        <DiagramNode label="Raw metadata" />
      </div>
      <Rail />
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <BranchLabel>structure · embed</BranchLabel>
          <DiagramNode
            icon={Brain}
            kind="compute"
            label="Gemini"
            sub="schema C · 6 tables"
          />
          <Rail />
          <DiagramNode
            icon={Cpu}
            kind="compute"
            label="EmbeddingGemma"
            sub="768-dim"
          />
          <Rail />
          <DiagramNode
            icon={Boxes}
            kind="store"
            label="pgvector"
            sub="13,556 chunks · HNSW"
          />
        </div>
        <div>
          <BranchLabel>posters</BranchLabel>
          <DiagramNode icon={ImageIcon} label="Posters" />
          <Rail />
          <DiagramNode kind="store" label="Cloudflare R2" sub="BlurHash LQIP" />
        </div>
      </div>
      <Legend />
    </DiagramFrame>
  );
}
