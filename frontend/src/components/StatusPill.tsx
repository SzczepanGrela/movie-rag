import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = { children: ReactNode; dot?: boolean; className?: string };

export function StatusPill({ children, dot = false, className }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3.5 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground backdrop-blur-sm",
        className,
      )}
    >
      {dot ? (
        <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
      ) : null}
      {children}
    </span>
  );
}
