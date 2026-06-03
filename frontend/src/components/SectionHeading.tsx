import type { ReactNode } from "react";

type Props = { children: ReactNode; index?: string };

export function SectionHeading({ children, index }: Props) {
  return (
    <div className="mb-4 flex items-center gap-3">
      {index ? (
        <span className="font-mono text-[11px] font-semibold text-primary">
          {index}
        </span>
      ) : null}
      <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        {children}
      </h2>
      <span className="h-px flex-1 bg-border/60" aria-hidden="true" />
    </div>
  );
}
