// Górny pasek wspólny dla wszystkich stron: logo, cztery zakładki, wybrane pole, link „How we know".
// Zakładki zaadaptowane z 21st.dev („Animated Navigation Tabs", autor ln-dev7): podkreślenie aktywnej
// zakładki i tło przy najechaniu, ale jako prawdziwe linki routera i bez biblioteki animacji.
import { NavLink, useLocation } from 'react-router-dom'
import { fieldShortName, type FieldFeature } from '@/lib/data'
import { rotationLabel } from '@/lib/rotation'
import { cn } from '@/lib/utils'

const TABS = [
  { to: '/', label: 'My field' },
  { to: '/changed', label: 'What has changed' },
  { to: '/replay', label: 'Rotation replay' },
  { to: '/season', label: 'This season' },
]

type TopBarProps = {
  selected: FieldFeature | undefined
}

export function TopBar({ selected }: TopBarProps) {
  // Zachowujemy ?field=... przy przechodzeniu między zakładkami.
  const { search } = useLocation()
  const rotation = selected
    ? (rotationLabel(selected.properties.current_rotation) ?? selected.properties.current_rotation)
    : null

  return (
    <header className="border-b-2 border-bar-border bg-bar text-bar-foreground">
      <div className="mx-auto flex max-w-[1680px] flex-wrap items-center gap-x-6 gap-y-1 px-4 lg:px-6">
        <NavLink
          to={{ pathname: '/', search }}
          className="flex min-h-11 items-center gap-2.5 py-2 font-heading text-[19px] font-semibold tracking-tight"
        >
          <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden>
            <rect width="32" height="32" rx="6" className="fill-bar-foreground" />
            <path d="M6 22l7-4 6 3 7-5v8H6z" className="fill-bar" opacity="0.35" />
            <path
              d="M6 15l7-4 6 3 7-5"
              fill="none"
              className="stroke-bar"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          PlotWise
        </NavLink>

        <nav aria-label="Main" className="order-last -mx-4 w-[calc(100%+2rem)] overflow-x-auto px-4 lg:order-none lg:mx-0 lg:w-auto lg:px-0">
          <ul className="flex">
            {TABS.map((tab) => (
              <li key={tab.to}>
                <NavLink
                  to={{ pathname: tab.to, search }}
                  end={tab.to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'relative flex min-h-[52px] items-center whitespace-nowrap px-4 text-[15px] transition-colors',
                      'after:absolute after:inset-x-3 after:bottom-0 after:h-[3px] after:rounded-t-sm after:transition-colors',
                      isActive
                        ? 'font-semibold text-bar-foreground after:bg-bar-active'
                        : 'font-medium text-bar-muted after:bg-transparent hover:text-bar-foreground',
                    )
                  }
                >
                  {tab.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="ml-auto flex flex-wrap items-center gap-x-5 gap-y-1">
          {selected && (
            <p className="flex items-center gap-2 text-[13px] text-bar-muted">
              <span className="sr-only">Selected field:</span>
              <span className="rounded-sm border border-bar-border px-2.5 py-1.5 font-mono text-[13px] font-medium text-bar-foreground">
                {fieldShortName(selected.properties)} · {rotation}
              </span>
            </p>
          )}
          <NavLink
            to={{ pathname: '/how', search }}
            className={({ isActive }) =>
              cn(
                'flex min-h-11 items-center text-[15px] underline decoration-1 underline-offset-4',
                isActive ? 'font-semibold text-bar-foreground decoration-bar-active decoration-2' : 'text-bar-muted hover:text-bar-foreground',
              )
            }
          >
            How we know
          </NavLink>
        </div>
      </div>
    </header>
  )
}
