// Navigation shared by all pages, in two forms:
// – wide screen: one floating "glass" pill at the top (logo, tabs, selected field, "How we know"),
// – phone: logo and selected field at the top, and the tabs as a bar at the bottom of the screen, under the thumb.
// Page content and the map scroll underneath and show through the glass.
import { CalendarDays, History, Info, Map, MapPinned, TrendingUp, type LucideIcon } from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import { LanguageSwitch } from '@/components/LanguageSwitch'
import { fieldShortName, type FieldFeature } from '@/lib/data'
import { useT } from '@/lib/i18n'
import { CROP_FILL_CLASS, toCropLetter } from '@/lib/rotation'
import { cn } from '@/lib/utils'

const TABS: { to: string; label: string; short: string; icon: LucideIcon }[] = [
  { to: '/', label: 'My field', short: 'Field', icon: MapPinned },
  { to: '/changed', label: 'What has changed', short: 'Changes', icon: TrendingUp },
  { to: '/replay', label: 'Rotation replay', short: 'Replay', icon: History },
  { to: '/season', label: 'This season', short: 'Season', icon: CalendarDays },
  { to: '/region', label: 'Region', short: 'Region', icon: Map },
]

type TopBarProps = {
  selected: FieldFeature | undefined
}

// Mark: a sprout with two leaves in a circle, drawn with the green gradient.
function Logo() {
  return (
    <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0 sm:h-9 sm:w-9" fill="none" aria-hidden>
      <defs>
        <linearGradient id="pw-logo-gradient" x1="4" y1="28" x2="28" y2="4" gradientUnits="userSpaceOnUse">
          <stop stopColor="#2fd67b" />
          <stop offset="1" stopColor="#06733a" />
        </linearGradient>
      </defs>
      <g stroke="url(#pw-logo-gradient)" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="16" cy="16" r="14" />
        <path d="M16 30V10.5" />
        <path d="M16 20.5c-5 0-8.2-3-8.2-7.8 5 0 8.2 3 8.2 7.8Z" />
        <path d="M16 20.5c5 0 8.2-3 8.2-7.8-5 0-8.2 3-8.2 7.8Z" />
      </g>
    </svg>
  )
}

// Field history in miniature: one bar per year in the crop colour. Decorative (the full history with
// captions is in the field card), so hidden from screen readers. Changes smoothly when another field is selected.
function HistoryStrip({ field }: { field: FieldFeature }) {
  const p = field.properties
  const first = p.crop_sequence_first_year
  const letters = [...p.crop_sequence]
  const t = useT()
  return (
    <span
      aria-hidden
      title={t('What grew on {field}, {from}–{to}', { field: fieldShortName(p), from: first, to: first + letters.length - 1 })}
      className="flex h-3 w-9 shrink-0 overflow-hidden rounded-full sm:w-28"
    >
      {letters.map((letter, i) => (
        <span key={i} className={cn('flex-1 transition-colors duration-500', CROP_FILL_CLASS[toCropLetter(letter)])} />
      ))}
    </span>
  )
}

export function TopBar({ selected }: TopBarProps) {
  // Keep ?field=... when moving between tabs.
  const { search } = useLocation()
  const t = useT()

  return (
    <>
      <header className="pointer-events-none fixed inset-x-0 top-0 z-[1100] p-3 lg:p-4">
        <div className="pw-glass pointer-events-auto mx-auto flex h-14 max-w-[1680px] items-center gap-2 rounded-full pl-3 pr-2 lg:pl-4">
          <NavLink
            to={{ pathname: '/', search }}
            className="flex min-h-11 items-center gap-2 pr-2 font-heading text-[16px] font-extrabold tracking-[0.01em] text-leaf-deep sm:text-[18px]"
          >
            <Logo />
            <span className="max-[380px]:sr-only">PLOTWISE</span>
          </NavLink>

          <nav aria-label={t('Main')} className="hidden lg:block">
            <ul className="flex gap-0.5">
              {TABS.map((tab) => (
                <li key={tab.to}>
                  <NavLink
                    to={{ pathname: tab.to, search }}
                    end={tab.to === '/'}
                    className={({ isActive }) =>
                      cn(
                        'pw-press flex min-h-10 items-center whitespace-nowrap rounded-full px-3 text-[15px] xl:px-4',
                        isActive
                          ? 'bg-card font-medium text-foreground shadow-soft'
                          : 'text-muted-foreground hover:bg-foreground/5 hover:text-foreground',
                      )
                    }
                  >
                    {t(tab.label)}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <div className="ml-auto flex items-center gap-1.5">
            {selected && (
              <p className="flex min-h-10 items-center gap-2.5 rounded-full bg-foreground/5 px-3 text-[14px] font-medium sm:px-3.5 sm:text-[15px]">
                <span className="sr-only">{t('Selected field:')}</span>
                <span className="whitespace-nowrap font-mono">{fieldShortName(selected.properties)}</span>
                <HistoryStrip field={selected} />
              </p>
            )}
            <LanguageSwitch />
            <NavLink
              to={{ pathname: '/how', search }}
              aria-label={t('How we know')}
              className={({ isActive }) =>
                cn(
                  'pw-press flex min-h-10 min-w-10 items-center justify-center gap-2 whitespace-nowrap rounded-full px-2.5 text-[15px] xl:px-4',
                  isActive
                    ? 'bg-card font-medium text-foreground shadow-soft'
                    : 'text-muted-foreground hover:bg-foreground/5 hover:text-foreground',
                )
              }
            >
              <Info aria-hidden className="h-5 w-5 xl:hidden" />
              <span className="hidden xl:inline">{t('How we know')}</span>
            </NavLink>
          </div>
        </div>
      </header>

      {/* Phone: tab bar at the bottom of the screen */}
      <nav aria-label={t('Main')} className="pointer-events-none fixed inset-x-0 bottom-0 z-[1100] p-3 lg:hidden">
        <ul
          className="pw-glass pointer-events-auto mx-auto grid max-w-md gap-1 rounded-[28px] p-1.5"
          style={{ gridTemplateColumns: `repeat(${TABS.length}, minmax(0, 1fr))` }}
        >
          {TABS.map((tab) => (
            <li key={tab.to}>
              <NavLink
                to={{ pathname: tab.to, search }}
                end={tab.to === '/'}
                aria-label={t(tab.label)}
                className={({ isActive }) =>
                  cn(
                    'pw-press flex min-h-[52px] flex-col items-center justify-center gap-0.5 rounded-[22px] text-[11px]',
                    isActive ? 'bg-card font-medium text-foreground shadow-soft' : 'text-muted-foreground',
                  )
                }
              >
                <tab.icon aria-hidden className="h-[22px] w-[22px] [[aria-current=page]_&]:text-leaf" strokeWidth={1.75} />
                {t(tab.short)}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}
