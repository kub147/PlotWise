// Middle column of Rotation replay: rotations ranked by the farmer's priorities.
import { CropTile } from '@/components/CropTile'
import { useT } from '@/lib/i18n'
import type { RankedRotation } from '@/lib/results'
import { rotationDisplayName, rotationPhases } from '@/lib/rotation'
import { formatUsd } from '@/lib/units'
import { cn } from '@/lib/utils'

type RankingListProps = {
  ranked: RankedRotation[]
  selectedId: string
  onSelect: (rotationId: string) => void
}

export function RankingList({ ranked, selectedId, onSelect }: RankingListProps) {
  const t = useT()
  return (
    <ol className="flex flex-col gap-2">
      {ranked.map(({ rotation, fit, place, tied }) => {
        const selected = rotation.id === selectedId
        const phases = rotationPhases(rotation.id) ?? []
        const fitPercent = Math.round(fit * 100)
        return (
          <li key={rotation.id}>
            <button
              type="button"
              aria-pressed={selected}
              onClick={() => onSelect(rotation.id)}
              className={cn(
                'pw-press grid w-full grid-cols-[2rem_minmax(0,1fr)] items-center gap-x-3 gap-y-2.5 pw-sheet rounded-3xl px-5 py-4 text-left sm:grid-cols-[2rem_minmax(0,1fr)_auto]',
                selected && 'pw-selected',
              )}
            >
              <span
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full font-mono text-[15px] font-medium',
                  place === 1 ? 'pw-brand shadow-[0_4px_12px_rgb(15_154_76/0.35)]' : 'bg-foreground/[0.06] text-muted-foreground',
                )}
              >
                <span aria-hidden>{place}</span>
                <span className="sr-only">{tied ? t('Tied for place {place}:', { place }) : t('Place {place}:', { place })}</span>
              </span>

              <span className="flex min-w-0 flex-col gap-1.5">
                <span className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
                  <span className="flex gap-0.5" aria-hidden>
                    {phases.map((letter, i) => (
                      <CropTile key={i} letter={letter} className="h-7 w-7" />
                    ))}
                  </span>
                  <span className="text-[15px] font-semibold">{rotationDisplayName(t(rotation.name))}</span>
                </span>
                {(rotation.is_current || rotation.status === 'optional' || tied) && (
                  <span className="flex flex-wrap gap-1.5">
                    {rotation.is_current && (
                      <span className="rounded-full bg-leaf-soft px-2.5 py-0.5 text-[13px] font-medium text-accent-foreground">
                        {t('Your rotation today')}
                      </span>
                    )}
                    {tied && (
                      <span className="rounded-full bg-foreground/[0.06] px-2.5 py-0.5 text-[13px] text-muted-foreground">
                        {t('Tied')}
                      </span>
                    )}
                    {rotation.status === 'optional' && (
                      <span className="rounded-full bg-foreground/[0.06] px-2.5 py-0.5 text-[13px] text-muted-foreground">
                        {t('Optional')}
                      </span>
                    )}
                  </span>
                )}
              </span>

              <span className="col-start-2 flex flex-col sm:col-start-3 sm:items-end">
                <span className="font-mono text-[19px] font-semibold">{formatUsd(rotation.summary.mean)}</span>
                <span className="text-[13px] text-muted-foreground">{t('average per acre a year')}</span>
              </span>

              {/* Fit bar: length and number; colour carries no meaning */}
              <span className="col-span-full flex items-center gap-3">
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-foreground/[0.07]" aria-hidden>
                  <span
                    className="pw-brand block h-full rounded-full transition-[width] duration-500 ease-[var(--ease-out)]"
                    style={{ width: `${fitPercent}%` }}
                  />
                </span>
                <span className="w-[5.5rem] text-right text-[13px] text-muted-foreground">
                  {t('Fit')} <span className="font-mono font-semibold text-foreground">{fitPercent}</span> {t('of 100')}
                </span>
              </span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
