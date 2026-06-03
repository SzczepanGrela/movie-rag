import type { ReactNode } from "react";
import { Footer } from "@/components/Footer";
import { SiteHeader } from "@/components/SiteHeader";
import { cn } from "@/lib/utils";

type Props = {
  children: ReactNode;
  mainClassName?: string;
};

export function PageShell({ children, mainClassName }: Props) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main
        className={cn(
          "mx-auto w-full max-w-3xl flex-1 px-4 py-12 sm:py-16",
          mainClassName,
        )}
      >
        {children}
      </main>
      <Footer />
    </div>
  );
}
