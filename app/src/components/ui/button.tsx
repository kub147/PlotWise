// Button in the shadcn/ui style, wired to the theme variables. Every size is at least 44 px high.
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'pw-press inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-5 text-[15px] font-medium disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'pw-brand shadow-[0_8px_22px_rgb(15_154_76/0.38)] hover:brightness-110',
        outline: 'bg-foreground/[0.06] text-foreground hover:bg-foreground/10',
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
    // asChild: gives the button look to the child element, e.g. an <a> link.
    asChild?: boolean
  }

export function Button({ className, variant, width, asChild = false, ...props }: ButtonProps) {
  const Component = asChild ? Slot : 'button'
  return <Component className={cn(buttonVariants({ variant, width }), className)} {...props} />
}
