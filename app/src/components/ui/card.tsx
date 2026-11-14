// Karta w stylu shadcn/ui: powierzchnia z cienką ramką, bez cienia i bez kolorowych pasków.
import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('pw-sheet rounded-[28px] text-card-foreground', className)}
      {...props}
    />
  )
}

// Sekcja wewnątrz karty, oddzielona linią od poprzedniej.
export function CardSection({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={cn('mx-6 border-t border-border py-5 first:border-t-0', className)} {...props} />
}

// Mały nagłówek sekcji (etykieta nad treścią).
export function SectionLabel({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('mb-3 text-[15px] font-medium text-foreground', className)}
      {...props}
    />
  )
}
