import { Link } from "@tanstack/react-router";
import { MovieRagLogo } from "@/components/MovieRagLogo";
import { Button } from "@/components/ui/button";

type Props = {
  title: string;
  message: string;
  action?: { label: string; onClick: () => void };
};

export function ErrorState({ title, message, action }: Props) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <main className="max-w-md text-center space-y-6">
        <div className="flex justify-center">
          <MovieRagLogo className="text-4xl sm:text-5xl text-foreground" />
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-semibold text-foreground">{title}</h1>
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
        <div className="flex justify-center gap-3">
          {action ? (
            <Button variant="outline" size="lg" onClick={action.onClick}>
              {action.label}
            </Button>
          ) : null}
          <Button asChild size="lg">
            <Link to="/">Back to search</Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
