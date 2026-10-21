import { useEffect, type ReactNode } from "react";
import { screenById, type ScreenId } from "@/routes";

/** The one h1. */
export function ScreenTitle({ id, children }: { id: ScreenId; children: ReactNode }) {
  useEffect(() => {
    document.title = `${id} · ${screenById(id).title} · Meridian`;
  }, [id]);
  return (
    <h1 className="t-title">{children}</h1>
  );
}
