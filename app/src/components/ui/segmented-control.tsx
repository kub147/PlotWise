// Segmented control (radio group with a sliding thumb).
// Adapted from 21st.dev ("Segmented Control" by ddoemonn): keyboard handling kept,
// and the radiogroup semantics; the animation is done in CSS instead of the motion library; colours come from the theme.
import { useRef, type KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'

export type SegmentedOption<T extends string> = { value: T; label: string }

type SegmentedControlProps<T extends string> = {
  options: SegmentedOption<T>[]
  // Group description for screen readers.
  label: string
  value: T
  onValueChange: (value: T) => void
  // 'surface' = on a card, 'glass' = over the map (translucent background), 'bar' = on the navigation bar.
  tone?: 'surface' | 'glass' | 'bar'
  className?: string
  // Class of the frame around the control (see below), e.g. to make it span the full width.
  frameClassName?: string
}

export function SegmentedControl<T extends string>({
  options,
  label,
  value,
  onValueChange,
  tone = 'surface',
  className,
  frameClassName,
}: SegmentedControlProps<T>) {
  const buttons = useRef<(HTMLButtonElement | null)[]>([])
  const count = Math.max(1, options.length)
  const index = Math.max(0, options.findIndex((option) => option.value === value))

  const go = (next: number) => {
    const option = options[(next + count) % count]
    buttons.current[(next + count) % count]?.focus()
    onValueChange(option.value)
  }

  const onKeyDown = (event: KeyboardEvent, i: number) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault()
      go(i + 1)
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault()
      go(i - 1)
    } else if (event.key === 'Home') {
      event.preventDefault()
      go(0)
    } else if (event.key === 'End') {
      event.preventDefault()
      go(count - 1)
    }
  }

  return (
    // Frame: as wide as the control, but never wider than the place it sits in. The control itself always takes the
    // room its labels need (equal columns as wide as the longest label), so with long labels in a tight spot
    // (Polish, a narrow screen) it scrolls sideways inside the frame instead of printing the labels over each other.
    <div className={cn('pw-scroll-none inline-block max-w-full overflow-x-auto rounded-full align-middle', frameClassName)}>
      <div
        role="radiogroup"
        aria-label={label}
        className={cn(
          'relative grid w-max rounded-full p-[3px]',
          tone === 'glass' ? 'pw-glass' : 'bg-foreground/[0.06]',
          className,
        )}
        style={{ gridTemplateColumns: `repeat(${count}, minmax(0, 1fr))` }}
      >
        {/* Sliding thumb of the selected option */}
        <span
          aria-hidden
          className={cn(
            // White, slightly raised thumb that springs to the selected option.
            'pointer-events-none absolute inset-y-[3px] left-[3px] rounded-full bg-card shadow-soft transition-transform duration-300 ease-[var(--ease-spring)]',
          )}
          style={{ width: `calc((100% - 6px) / ${count})`, transform: `translateX(${index * 100}%)` }}
        />
        {options.map((option, i) => {
          const checked = i === index
          return (
            <button
              key={option.value}
              ref={(node) => {
                buttons.current[i] = node
              }}
              type="button"
              role="radio"
              aria-checked={checked}
              tabIndex={checked ? 0 : -1}
              onClick={() => onValueChange(option.value)}
              onKeyDown={(event) => onKeyDown(event, i)}
              className={cn(
                // The focus ring stays inside the control's own padding, so the frame does not clip it.
                'relative z-10 min-h-[38px] whitespace-nowrap rounded-full px-4 text-[13px] transition-colors focus-visible:outline-offset-0',
                checked ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
