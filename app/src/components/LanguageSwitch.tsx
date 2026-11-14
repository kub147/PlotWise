// Language switch: two flag buttons, Polish and English. The flags are small inline drawings, not emoji,
// and each button has a text name for screen readers.
import { useLang, type Lang } from '@/lib/i18n'
import { cn } from '@/lib/utils'

function PolishFlag() {
  return (
    <svg viewBox="0 0 24 16" className="h-4 w-6 rounded-[3px] ring-1 ring-foreground/15" aria-hidden>
      <rect width="24" height="8" fill="#ffffff" />
      <rect y="8" width="24" height="8" fill="#dc143c" />
    </svg>
  )
}

function EnglishFlag() {
  return (
    <svg viewBox="0 0 24 16" className="h-4 w-6 rounded-[3px] ring-1 ring-foreground/15" aria-hidden>
      <rect width="24" height="16" fill="#012169" />
      <path d="M0 0l24 16M24 0L0 16" stroke="#ffffff" strokeWidth="3.2" />
      <path d="M0 0l24 16M24 0L0 16" stroke="#c8102e" strokeWidth="1.3" />
      <path d="M12 0v16M0 8h24" stroke="#ffffff" strokeWidth="5.4" />
      <path d="M12 0v16M0 8h24" stroke="#c8102e" strokeWidth="3.2" />
    </svg>
  )
}

const OPTIONS: { lang: Lang; name: string; Flag: () => React.JSX.Element }[] = [
  { lang: 'pl', name: 'Polski', Flag: PolishFlag },
  { lang: 'en', name: 'English', Flag: EnglishFlag },
]

export function LanguageSwitch() {
  const { lang, setLang } = useLang()
  return (
    <div role="group" aria-label="Language / Język" className="flex items-center gap-0.5">
      {OPTIONS.map(({ lang: option, name, Flag }) => (
        <button
          key={option}
          type="button"
          lang={option}
          aria-label={name}
          aria-pressed={lang === option}
          title={name}
          onClick={() => setLang(option)}
          className={cn(
            'pw-press flex min-h-10 min-w-9 items-center justify-center rounded-full px-1.5 sm:min-w-10',
            lang === option ? 'bg-card shadow-soft' : 'opacity-60 hover:bg-foreground/5 hover:opacity-100',
          )}
        >
          <Flag />
        </button>
      ))}
    </div>
  )
}
