// Card in the shadcn/ui style: a glass sheet with soft corners, no coloured stripes.
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

// A section inside a card, separated from the previous one by a line.
export function CardSection({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={cn('mx-6 border-t border-border py-5 first:border-t-0', className)} {...props} />
}

// Small section heading (label above the content).
export function SectionLabel({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('mb-3 text-[15px] font-medium text-foreground', className)}
      {...props}
    />
  )
}
