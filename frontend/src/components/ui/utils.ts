import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  // Merge conditional class names while resolving Tailwind utility conflicts.
  return twMerge(clsx(inputs));
}
