import { type ReactNode } from "react";
import { cn } from "@/lib/cx";

const MAX: Record<"chat" | "console" | "page" | "auth", string> = {
  chat: "max-w-[1200px]", console: "max-w-[1440px]", page: "max-w-[960px]", auth: "max-w-[440px]",
};
/** Canvas + app frame. The skip link is the first focusable thing on every screen. */
export function AppFrame({ variant, children }: { variant: "chat" | "console" | "page" | "auth"; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas p-0 min-[700px]:p-6">
      <a href="#main" className="skip-link">Skip to main content</a>
      <div
        data-frame={variant}
        className={cn("mx-auto overflow-hidden bg-[var(--app-bg)] shadow-[var(--elev-frame)] min-[700px]:rounded-frame", MAX[variant])}
      >
        {children}
      </div>
    </div>
  );
}
