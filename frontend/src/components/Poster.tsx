import { Film } from "lucide-react";
import { useState } from "react";
import { Blurhash } from "react-blurhash";
import type { PosterData } from "@/lib/api";
import { cn } from "@/lib/utils";

type PosterProps = {
  poster: PosterData | null;
  size: "thumb" | "full";
  alt: string;
  className?: string;
};

const imgLayer = "absolute inset-0 size-full object-cover transition-opacity";

export function Poster({ poster, size, alt, className }: PosterProps) {
  const [mainLoaded, setMainLoaded] = useState(false);
  const [thumbLoaded, setThumbLoaded] = useState(false);
  const base = "relative aspect-[2/3] overflow-hidden rounded-lg bg-card";

  if (!poster) {
    return (
      <div className={cn(base, "flex items-center justify-center", className)}>
        <Film
          className="h-1/3 w-1/3 text-muted-foreground/35"
          aria-hidden="true"
        />
      </div>
    );
  }

  // On the detail (full), layer the smaller thumb under the full image: it is
  // already cached from the list, so it paints instantly and the full poster
  // sharpens in on top. Blurhash stays as the base for direct navigation.
  const isFull = size === "full";
  const mainSrc = isFull ? poster.url : poster.thumb_url;

  return (
    <div className={cn(base, className)}>
      {poster.blurhash && (
        <Blurhash
          hash={poster.blurhash}
          width="100%"
          height="100%"
          resolutionX={32}
          resolutionY={48}
          punch={1}
          className="absolute inset-0"
        />
      )}
      {isFull && (
        <img
          src={poster.thumb_url}
          alt=""
          aria-hidden="true"
          onLoad={() => setThumbLoaded(true)}
          className={cn(
            imgLayer,
            "duration-200",
            thumbLoaded ? "opacity-100" : "opacity-0",
          )}
        />
      )}
      <img
        src={mainSrc}
        alt={alt}
        loading={isFull ? "eager" : "lazy"}
        fetchPriority={isFull ? "high" : "auto"}
        onLoad={() => setMainLoaded(true)}
        className={cn(
          imgLayer,
          "duration-500",
          mainLoaded ? "opacity-100" : "opacity-0",
        )}
      />
    </div>
  );
}
