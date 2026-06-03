import { Link, useRouterState } from "@tanstack/react-router";
import { MovieRagLogo } from "@/components/MovieRagLogo";

type NavItem = {
  to: "/" | "/ask" | "/about";
  label: string;
  match: (path: string) => boolean;
};

const NAV: NavItem[] = [
  {
    to: "/",
    label: "Search",
    match: (p) => p === "/" || p.startsWith("/movies"),
  },
  { to: "/ask", label: "Ask", match: (p) => p.startsWith("/ask") },
  { to: "/about", label: "About", match: (p) => p.startsWith("/about") },
];

export function SiteHeader() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link to="/" className="transition-opacity hover:opacity-80">
          <MovieRagLogo className="text-lg text-foreground" />
        </Link>
        <nav aria-label="Main" className="flex items-center gap-5 text-sm">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`transition-colors ${
                item.match(pathname)
                  ? "text-primary"
                  : "text-muted-foreground hover:text-primary"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
