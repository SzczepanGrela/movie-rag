import { useEffect, useImperativeHandle, useRef } from "react";

const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY;

export type TurnstileHandle = { execute: () => Promise<string | null> };

type Props = { ref?: React.Ref<TurnstileHandle> };

type Pending = {
  resolve: (token: string | null) => void;
  reject: (err: Error) => void;
};

export function Turnstile({ ref }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);
  const hasRunRef = useRef(false);
  const pendingRef = useRef<Pending | null>(null);

  useImperativeHandle(ref, () => ({
    // Resolves null when Turnstile is unconfigured (local dev): the backend
    // secret-gate skips verification, so an empty token is accepted there.
    execute: () =>
      new Promise<string | null>((resolve, reject) => {
        if (!SITE_KEY) {
          resolve(null);
          return;
        }
        const id = widgetIdRef.current;
        const el = containerRef.current;
        if (!id || !el || !window.turnstile) {
          reject(new Error("turnstile_not_ready"));
          return;
        }
        pendingRef.current = { resolve, reject };
        if (hasRunRef.current) window.turnstile.reset(id);
        hasRunRef.current = true;
        window.turnstile.execute(el);
      }),
  }));

  useEffect(() => {
    if (!SITE_KEY) return;
    const el = containerRef.current;
    if (!el) return;

    let cancelled = false;
    const tryRender = () => {
      if (cancelled) return;
      if (!window.turnstile) {
        window.setTimeout(tryRender, 200);
        return;
      }
      if (widgetIdRef.current) return;
      widgetIdRef.current = window.turnstile.render(el, {
        sitekey: SITE_KEY,
        execution: "execute",
        appearance: "interaction-only",
        callback: (token) => {
          pendingRef.current?.resolve(token);
          pendingRef.current = null;
        },
        "error-callback": () => {
          pendingRef.current?.reject(new Error("turnstile_error"));
          pendingRef.current = null;
        },
        "expired-callback": () => {
          pendingRef.current?.reject(new Error("turnstile_expired"));
          pendingRef.current = null;
        },
      });
    };
    tryRender();

    return () => {
      cancelled = true;
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, []);

  if (!SITE_KEY) return null;
  return <div ref={containerRef} />;
}
