export {};

declare global {
  interface TurnstileRenderOptions {
    sitekey: string;
    callback?: (token: string) => void;
    "error-callback"?: () => void;
    "expired-callback"?: () => void;
    size?: "normal" | "flexible" | "compact";
    appearance?: "always" | "execute" | "interaction-only";
    execution?: "render" | "execute";
  }
  interface Turnstile {
    render: (el: HTMLElement, opts: TurnstileRenderOptions) => string;
    execute: (
      container: string | HTMLElement,
      opts?: Partial<TurnstileRenderOptions>,
    ) => void;
    reset: (widgetId?: string) => void;
    remove: (widgetId?: string) => void;
  }
  interface Window {
    turnstile?: Turnstile;
  }
}
