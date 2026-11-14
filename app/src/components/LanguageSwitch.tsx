// Language switch: two flag buttons, Polish and American English. The flags are small inline drawings, not emoji,
// and each button has a text name for screen readers. The flag of the language just chosen waves for a moment.
import { useState } from 'react'
import { useLang, type Lang } from '@/lib/i18n'
import { cn } from '@/lib/utils'

function PolishFlag() {
  return (
    <svg viewBox="0 0 24 16" aria-hidden>
      <rect width="24" height="8" fill="#ffffff" />
      <rect y="8" width="24" height="8" fill="#dc143c" />
    </svg>
  )
}

// 13 stripes and a blue canton with a simplified field of stars (at 24 px the 50 stars cannot be told apart).
const STRIPE = 16 / 13
const STARS: [number, number][] = []
for (let row = 0; row < 5; row++) {
  for (let col = 0; col < (row % 2 === 0 ? 6 : 5); col++) {
    STARS.push([0.8 + col * 1.6 + (row % 2 === 0 ? 0 : 0.8), 0.9 + row * 1.7])
  }
}

function UsFlag() {
  return (
    <svg viewBox="0 0 24 16" aria-hidden>
      <rect width="24" height="16" fill="#ffffff" />
      {Array.from({ length: 7 }, (_, index) => (
        <rect key={index} y={index * 2 * STRIPE} width="24" height={STRIPE} fill="#b22234" />
      ))}
      <rect width="9.6" height={7 * STRIPE} fill="#3c3b6e" />
      {STARS.map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r="0.38" fill="#ffffff" />
      ))}
    </svg>
  )
}

const SLICES = 12

// The flag in thin slices; while waving, each slice starts its rise a little later than the one before.
function WavingFlag({ Flag, waving }: { Flag: () => React.JSX.Element; waving: boolean }) {
  return (
    <span className={cn('pw-flag', waving && 'pw-flag-waving')} aria-hidden>
      {Array.from({ length: SLICES }, (_, index) => (
        <span key={index} className="pw-flag-slice" style={{ animationDelay: `${index * 45}ms` }}>
          <span style={{ position: 'absolute', left: `${-index * 2}px`, top: 0, display: 'block', width: 24, height: 16 }}>
            <Flag />
          </span>
        </span>
      ))}
      <span className="pw-flag-shade" />
    </span>
  )
}

const OPTIONS: { lang: Lang; name: string; Flag: () => React.JSX.Element }[] = [
  { lang: 'pl', name: 'Polski', Flag: PolishFlag },
  { lang: 'en', name: 'English (US)', Flag: UsFlag },
]

export function LanguageSwitch() {
  const { lang, setLang } = useLang()
  // Counts the switches, so that choosing a language again restarts the wave.
  const [waveCount, setWaveCount] = useState(0)

  return (
    <div role="group" aria-label="Language / Język" className="flex items-center gap-0.5">
      {OPTIONS.map(({ lang: option, name, Flag }) => {
        const waving = waveCount > 0 && lang === option
        return (
          <button
            key={option}
            type="button"
            lang={option}
            aria-label={name}
            aria-pressed={lang === option}
            title={name}
            onClick={() => {
              setLang(option)
              setWaveCount((count) => count + 1)
            }}
            className={cn(
              'pw-press flex min-h-10 min-w-9 items-center justify-center rounded-full px-1.5 sm:min-w-10',
              lang === option ? 'bg-card shadow-soft' : 'opacity-60 hover:bg-foreground/5 hover:opacity-100',
            )}
          >
            <WavingFlag key={waving ? waveCount : 'still'} Flag={Flag} waving={waving} />
          </button>
        )
      })}
    </div>
  )
}
