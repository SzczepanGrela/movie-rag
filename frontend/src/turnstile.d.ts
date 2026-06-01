export {};

declare global {
  interface TurnstileRenderOptions {
    sitekey: string;
    callback?: (token: string) => void;
    "error-callback"?: () => void;
    "expired-callback"?: () => void;
    size?: "normal" | "flexible" | "invisible";
    appearance?: "always" | "execute" | "interaction-only";
  }
  interface Turnstile {
    render: (el: HTMLElement, opts: TurnstileRenderOptions) => string;
    reset: (widgetId?: string) => void;
    remove: (widgetId?: string) => void;
  }
  interface Window {
    turnstile?: Turnstile;
  }
}
