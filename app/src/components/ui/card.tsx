// Karta w stylu shadcn/ui: powierzchnia z cienką ramką, bez cienia i bez kolorowych pasków.
import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-lg border border-border bg-card text-card-foreground', className)}
      {...props}
    />
  )
}

// Sekcja wewnątrz karty, oddzielona linią od poprzedniej.
export function CardSection({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={cn('border-t border-border px-5 py-4 first:border-t-0', className)} {...props} />
}

// Mały nagłówek sekcji (etykieta nad treścią).
export function SectionLabel({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('mb-2 font-sans text-[13px] font-semibold uppercase tracking-[0.06em] text-muted-foreground', className)}
      {...props}
    />
  )
}
