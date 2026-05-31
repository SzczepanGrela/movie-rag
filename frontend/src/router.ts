import { createRouter } from "@tanstack/react-router";
import { rootRoute } from "@/routes/__root";
import { askRoute } from "@/routes/ask";
import { movieDetailRoute } from "@/routes/movie-detail";
import { searchRoute } from "@/routes/search";

const routeTree = rootRoute.addChildren([
  searchRoute,
  movieDetailRoute,
  askRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
