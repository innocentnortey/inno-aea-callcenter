import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// The type scale tokens (theme.css --text-*) are font sizes, not colours: tell tailwind-merge so
// `text-body` does not swallow a `text-[color:...]` class.
const SIZES = ["caption", "section", "small", "ui", "body", "card-title", "name", "lead", "title", "signal", "code", "ref", "time-hero", "time-due", "time-row", "time-meta"];
const twMerge = extendTailwindMerge({
  extend: { classGroups: { "font-size": [{ text: SIZES }] } },
});

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
