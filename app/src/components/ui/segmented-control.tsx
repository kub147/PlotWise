// Przełącznik segmentowy (grupa radio z przesuwanym znacznikiem).
// Zaadaptowany z 21st.dev („Segmented Control", autor ddoemonn): zachowana obsługa klawiatury
// i semantyka radiogroup, animacja zrobiona w CSS zamiast biblioteki motion, kolory z motywu.
import { useRef, type KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'

export type SegmentedOption<T extends string> = { value: T; label: string }

type SegmentedControlProps<T extends string> = {
  options: SegmentedOption<T>[]
  // Opis grupy dla czytników ekranu.
  label: string
  value: T
  onValueChange: (value: T) => void
  // 'bar' = wersja na górny pasek (kolory paska), 'surface' = na karcie lub mapie.
  tone?: 'surface' | 'bar'
  className?: string
}

export function SegmentedControl<T extends string>({
  options,
  label,
  value,
  onValueChange,
  tone = 'surface',
  className,
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
    <div
      role="radiogroup"
      aria-label={label}
      className={cn(
        'relative inline-grid rounded-md border p-[3px]',
        tone === 'bar' ? 'border-bar-border bg-bar' : 'border-border bg-muted',
        className,
      )}
      style={{ gridTemplateColumns: `repeat(${count}, minmax(0, 1fr))` }}
    >
      {/* Przesuwany znacznik wybranej opcji */}
      <span
        aria-hidden
        className={cn(
          'pointer-events-none absolute inset-y-[3px] left-[3px] rounded-sm transition-transform duration-200 ease-out',
          tone === 'bar' ? 'bg-bar-foreground' : 'bg-foreground',
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
              'relative z-10 min-h-[38px] whitespace-nowrap rounded-sm px-3 text-[13px] font-semibold transition-colors',
              tone === 'bar'
                ? checked
                  ? 'text-bar'
                  : 'text-bar-muted hover:text-bar-foreground'
                : checked
                  ? 'text-card'
                  : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
