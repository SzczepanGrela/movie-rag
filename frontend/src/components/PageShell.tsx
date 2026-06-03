import type { ReactNode } from "react";
import { Footer } from "@/components/Footer";
import { SiteHeader } from "@/components/SiteHeader";
import { cn } from "@/lib/utils";

type Props = {
  children: ReactNode;
  width?: "default" | "wide";
  mainClassName?: string;
};

export function PageShell({
  children,
  width = "default",
  mainClassName,
}: Props) {
  const maxW = width === "wide" ? "max-w-5xl" : "max-w-3xl";
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main
        className={cn(
          "mx-auto w-full flex-1 px-4 py-12 sm:py-16",
          maxW,
          mainClassName,
        )}
      >
        {children}
      </main>
      <Footer />
    </div>
  );
}
