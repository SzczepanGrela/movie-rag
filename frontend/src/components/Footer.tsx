import { Link } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";

const REPO_URL = "https://github.com/SzczepanGrela/movie-rag";
const LIVE_URL = "https://movierag.grela.dev";

export function Footer() {
  return (
    <footer className="mx-auto max-w-3xl px-4 pb-10">
      <div className="flex items-center justify-center gap-5 border-t border-border/60 pt-6 text-xs text-muted-foreground">
        <Link to="/about" className="hover:text-primary transition-colors">
          About
        </Link>
        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 hover:text-primary transition-colors"
        >
          GitHub
          <ExternalLink className="size-3" aria-hidden="true" />
        </a>
        <a
          href={LIVE_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 hover:text-primary transition-colors"
        >
          Live
          <ExternalLink className="size-3" aria-hidden="true" />
        </a>
      </div>
    </footer>
  );
}
