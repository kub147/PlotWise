import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Joins Tailwind classes and removes conflicts (shadcn/ui standard).
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
