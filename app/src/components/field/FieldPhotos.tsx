// "From above" in the field card: three small tiles (aerial photo, greenness, surface heat). A tile opens the popup
// (FieldViewer) on that view, so the card stays short and the images get the room they need.
// When the repo has no image for a field we say so instead of showing a stand-in.
import { Maximize2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { imageUrl, VIEWER_TAB_LABEL, type HeatScene, type NdviPoint, type NdviState, type ViewerTab } from '@/lib/fieldMedia'
import { useT } from '@/lib/i18n'

// Years of the greenness record drawn in the tile; the popup shows all of them.
const SPARK_YEARS = 6

// Small preview of the greenness chart: the last few years as one line, no axes. Decorative: the label names it.
function GreennessSpark({ points }: { points: NdviPoint[] }) {
  const end = points[points.length - 1].time
  const start = end - SPARK_YEARS * 365.25 * 24 * 3600 * 1000
  const recent = points.filter((point) => point.time >= start)
  const path = recent
    .map((point) => {
      const x = ((point.time - start) / (end - start)) * 100
      // NDVI 0–1 mapped into the tile with a little room above and below.
      const y = 88 - Math.min(1, Math.max(0, point.ndvi)) * 76
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden className="h-full w-full">
      <polyline
        points={path}
        fill="none"
        stroke="var(--chart-green)"
        strokeWidth={1.5}
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

function Tile({
  label,
  hint,
  onOpen,
  background,
  children,
}: {
  label: string
  // Read out after the label: what happens on click.
  hint: string
  onOpen: () => void
  background?: string
  children: ReactNode
}) {
  return (
    <button type="button" onClick={onOpen} className="pw-press group flex min-w-0 flex-col gap-1.5 text-left">
      <span
        className="relative block aspect-square w-full overflow-hidden rounded-2xl bg-foreground/[0.05] ring-1 ring-inset ring-foreground/[0.06]"
        style={background ? { background } : undefined}
      >
        {children}
        <span
          aria-hidden
          className="absolute bottom-1.5 right-1.5 flex h-7 w-7 items-center justify-center rounded-full bg-card/90 text-foreground shadow-soft transition-transform duration-200 ease-[var(--ease-out)] group-hover:scale-110"
        >
          <Maximize2 className="h-3.5 w-3.5" strokeWidth={2} />
        </span>
      </span>
      <span className="text-[13px] font-medium leading-snug">
        {label}
        <span className="sr-only">. {hint}</span>
      </span>
    </button>
  )
}

function Missing({ label, note }: { label: string; note: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex aspect-square items-center justify-center rounded-2xl bg-foreground/[0.04] px-2 text-center text-[12px] leading-snug text-muted-foreground">
        {note}
      </div>
      <span className="text-[13px] font-medium leading-snug text-muted-foreground">{label}</span>
    </div>
  )
}

type FieldPhotosProps = {
  fieldId: string
  fieldLabel: string
  hasAerial: boolean
  ndvi: NdviState
  // Heat scenes that contain this field, newest first.
  heatScenes: HeatScene[]
  onOpen: (tab: ViewerTab) => void
}

export function FieldPhotos({ fieldId, fieldLabel, hasAerial, ndvi, heatScenes, onOpen }: FieldPhotosProps) {
  const t = useT()
  const label = (tab: ViewerTab) => t(VIEWER_TAB_LABEL[tab])
  const hint = t('Opens larger')
  const heatScene = heatScenes[0]

  return (
    <div className="grid grid-cols-3 gap-3">
      {hasAerial ? (
        <Tile label={label('aerial')} hint={hint} onOpen={() => onOpen('aerial')}>
          <img
            src={imageUrl(`field_${fieldId}_naip.png`)}
            alt={t('Aerial photo of {field}', { field: fieldLabel })}
            loading="lazy"
            className="h-full w-full object-cover"
          />
        </Tile>
      ) : (
        <Missing label={label('aerial')} note={t('No record for this field')} />
      )}

      {ndvi.status === 'missing' || (ndvi.status === 'ready' && ndvi.points.length < 2) ? (
        <Missing label={label('greenness')} note={t('No record for this field')} />
      ) : (
        <Tile label={label('greenness')} hint={hint} onOpen={() => onOpen('greenness')} background="var(--tint-life)">
          {ndvi.status === 'ready' && <GreennessSpark points={ndvi.points} />}
        </Tile>
      )}

      {heatScene ? (
        <Tile label={label('heat')} hint={hint} onOpen={() => onOpen('heat')}>
          <img
            src={imageUrl(heatScene.image.split('/').pop() ?? heatScene.image)}
            alt={t('Surface heat map around {site}; blue is cooler, red is hotter', { site: heatScene.site })}
            loading="lazy"
            className="h-full w-full object-cover"
          />
        </Tile>
      ) : (
        <Missing label={label('heat')} note={t('No record for this field')} />
      )}
    </div>
  )
}
