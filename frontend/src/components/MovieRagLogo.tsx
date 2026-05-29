import { Clapperboard } from "lucide-react";

type Props = { className?: string };

export function MovieRagLogo({ className }: Props) {
  return (
    <span
      aria-label="movie-rag"
      role="img"
      className={`inline-flex items-center font-bold tracking-[-0.04em] whitespace-nowrap ${className ?? ""}`}
    >
      <Clapperboard
        aria-hidden="true"
        strokeWidth={2}
        className="shrink-0 text-primary mr-[0.25em] mt-[0.05em]"
        style={{ width: "1.1em", height: "1.1em" }}
      />
      <span>
        movie-rag<span className="text-primary">.</span>
      </span>
    </span>
  );
}
