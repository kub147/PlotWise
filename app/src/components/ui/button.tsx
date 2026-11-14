// Przycisk w stylu shadcn/ui, przepięty na zmienne motywu. Każdy rozmiar ma co najmniej 44 px wysokości.
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-4 text-[15px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        outline: 'border border-input bg-card text-foreground hover:bg-muted',
        ghost: 'text-foreground hover:bg-muted',
      },
      width: {
        auto: '',
        full: 'w-full',
      },
    },
    defaultVariants: { variant: 'primary', width: 'auto' },
  },
)

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    // asChild: nadaje wygląd przycisku elementowi potomnemu, np. linkowi <a>.
    asChild?: boolean
  }

export function Button({ className, variant, width, asChild = false, ...props }: ButtonProps) {
  const Component = asChild ? Slot : 'button'
  return <Component className={cn(buttonVariants({ variant, width }), className)} {...props} />
}
