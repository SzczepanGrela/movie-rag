import { createRootRoute, Outlet, useRouter } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { ErrorState } from "@/components/ErrorState";

export const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFound,
  errorComponent: RouteError,
});

function RootLayout() {
  return (
    <>
      <Outlet />
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  );
}

function NotFound() {
  return (
    <ErrorState
      title="Page not found"
      message="We couldn't find that page. It may have moved, or the link is wrong."
    />
  );
}

function RouteError() {
  const router = useRouter();
  return (
    <ErrorState
      title="Something went wrong"
      message="An unexpected error occurred while loading this page."
      action={{ label: "Try again", onClick: () => router.invalidate() }}
    />
  );
}
