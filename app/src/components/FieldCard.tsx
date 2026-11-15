// Right column of the "My field" view: the card of the selected field.
// The order of the sections is fixed: name and area, rotation, three tiles "from above" (they open the popup with
// the aerial photo, the greenness chart and the heat images), crop history, soil and bare ground.
// The tiles sit high so that they are in view without scrolling, on a small laptop screen too.
// The button to Rotation replay is pinned to the bottom of the card on a wide screen, so it is always in view.
import { ArrowRight, Droplets, Sprout, Sun, TrendingUp, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CropLegend, CropTile } from '@/components/CropTile'
import { Button } from '@/components/ui/button'
import { Card, CardSection, SectionLabel } from '@/components/ui/card'
import { FieldPhotos } from '@/components/field/FieldPhotos'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import type { HeatScene, NdviState, ViewerTab } from '@/lib/fieldMedia'
import { useT, type Translate } from '@/lib/i18n'
import { rotationPhases, toCropLetter, type CropLetter } from '@/lib/rotation'
import { formatNumber, haToAcres, mmToInches } from '@/lib/units'

// CDL crop name for the caption. Two classes have no name in the file ("CDL 60", "CDL 224"): named here.
const CDL_NAMES: Record<string, string> = { '60': 'switchgrass', '224': 'vetch' }
function historyName(name: string, t: Translate) {
  const code = /^CDL (\d+)$/.exec(name)
  if (!code) return t(name)
  return CDL_NAMES[code[1]] ? t(CDL_NAMES[code[1]]) : t('other crop')
}

// Tile with one number: icon, number, unit and label on a lightly tinted background.
function StatTile({
  icon: Icon,
  tint,
  label,
  unit,
  children,
}: {
  icon: LucideIcon
  tint: string
  label: string
  unit?: string
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-1 rounded-[20px] p-3.5" style={{ background: tint }}>
      <Icon aria-hidden className="h-5 w-5 opacity-70" strokeWidth={1.75} />
      <dd className="order-2 font-mono text-[22px] font-medium leading-tight">
        {children}
        {unit && <span className="block font-sans text-[13px] font-normal leading-snug text-muted-foreground">{unit}</span>}
      </dd>
      <dt className="order-3 text-[13px] leading-snug text-muted-foreground">{label}</dt>
    </div>
  )
}

type FieldCardProps = {
  data: AppData
  field: FieldFeature
  ndvi: NdviState
  // Heat scenes that contain this field, newest first.
  heatScenes: HeatScene[]
  // Opens the popup with the views from above on the given view.
  onOpenViewer: (tab: ViewerTab) => void
}

export function FieldCard({ data, field, ndvi, heatScenes, onOpenViewer }: FieldCardProps) {
  const p = field.properties
  const county = data.countyNames[p.county_fips]
  const phases = rotationPhases(p.current_rotation)
  const hasReplay = data.manifest.results.includes(p.field_id)
  const hasAerial = data.manifest.naip.includes(p.field_id)
  const t = useT()

  // Crop history: one letter per year, starting at crop_sequence_first_year.
  const history = [...p.crop_sequence].map((letter, i) => {
    const year = p.crop_sequence_first_year + i
    return { year, letter: toCropLetter(letter), name: historyName(p.crop_history_names[String(year)] ?? 'no data', t) }
  })
  const firstYear = history[0]?.year
  const lastYear = history[history.length - 1]?.year
  const lettersUsed = (['W', 'S', 'C', 'F', 'O'] as CropLetter[]).filter((letter) =>
    history.some((entry) => entry.letter === letter),
  )
  const otherYears = history.filter((entry) => entry.letter === 'O')

  return (
    <Card>
      {/* 1. Name and area */}
      <CardSection>
        <p className="font-mono text-[13px] font-medium text-muted-foreground">{fieldShortName(p)}</p>
        <h2 className="mt-0.5 text-[21px] font-semibold leading-tight">{t(p.name)}</h2>
        <p className="mt-1.5 text-[15px] text-muted-foreground">
          <span className="font-mono font-semibold text-foreground">{formatNumber(haToAcres(p.area_ha))}</span>{' '}
          {county
            ? t('acres in {name} County, Kansas', { name: county, n: Math.round(haToAcres(p.area_ha)) })
            : t('acres in Kansas', { n: Math.round(haToAcres(p.area_ha)) })}
        </p>
      </CardSection>

      {/* 2. Rotation today */}
      <CardSection>
        <SectionLabel>{t('Rotation today')}</SectionLabel>
        {phases ? (
          <div className="flex items-center gap-3">
            <span className="flex gap-1">
              {phases.map((letter, i) => (
                <CropTile key={i} letter={letter} />
              ))}
            </span>
            <span className="text-[15px] font-medium">{t(phases.join('-'))}</span>
          </div>
        ) : (
          <p className="text-[15px]">{t('No fallow – not one of the modeled rotations.')}</p>
        )}
      </CardSection>

      {/* 3. From above: aerial photo, greenness, surface heat. Each tile opens the popup on that view. */}
      <CardSection>
        <SectionLabel>{t('From above')}</SectionLabel>
        <FieldPhotos
          fieldId={p.field_id}
          fieldLabel={fieldShortName(p)}
          hasAerial={hasAerial}
          ndvi={ndvi}
          heatScenes={heatScenes}
          onOpen={onOpenViewer}
        />
      </CardSection>

      {/* 4. Crop history */}
      <CardSection>
        <SectionLabel>
          {t('What grew here, {from}–{to}', { from: firstYear ?? '', to: lastYear ?? '' })}
        </SectionLabel>
        <ol
          className="grid gap-[2px]"
          style={{ gridTemplateColumns: `repeat(${history.length}, minmax(0, 1fr))` }}
        >
          {history.map((entry) => (
            <li key={entry.year} title={`${entry.year}: ${entry.name}`} className="flex flex-col items-center gap-1">
              <CropTile letter={entry.letter} size="strip" />
              <span aria-hidden className="font-mono text-[11px] leading-none text-muted-foreground">
                {String(entry.year).slice(2)}
              </span>
              <span className="sr-only">
                {entry.year}: {entry.name}
              </span>
            </li>
          ))}
        </ol>
        <div className="mt-3">
          <CropLegend letters={lettersUsed} />
        </div>
        {otherYears.length > 0 && (
          <p className="mt-2 text-[13px] text-muted-foreground">
            {otherYears.map((entry) => `${entry.year}: ${entry.name}`).join('; ')}.
          </p>
        )}
        <p className="mt-2 text-[13px] text-muted-foreground">{t('Read from the USDA Cropland Data Layer, one crop per year.')}</p>
      </CardSection>

      {/* 5. Soil and bare-ground days */}
      <CardSection>
        <SectionLabel>{t('Soil and ground cover')}</SectionLabel>
        <p className="text-[15px] font-medium">{p.soil_map_unit}</p>
        {p.soil_map_unit_share < 0.95 && (
          <p className="text-[13px] text-muted-foreground">
            {t('Main soil, about {n}% of the field', { n: Math.round(p.soil_map_unit_share * 100) })}
          </p>
        )}
        {/* Four numbers as tinted tiles: the tint says what the number is about (water, soil, organic matter, slope) */}
        <dl className="mt-3 grid grid-cols-2 gap-2.5">
          <StatTile icon={Droplets} tint="var(--tint-water)" label={t('Water the soil can hold for plants')} unit={t('in, top 5 ft')}>
            {formatNumber(mmToInches(p.awc_mm), 1)}
          </StatTile>
          <StatTile icon={Sun} tint="var(--tint-soil)" label={t('Days a year without green cover')} unit={t('seen from satellite')}>
            {formatNumber(p.bare_days_per_year)}
          </StatTile>
          <StatTile icon={Sprout} tint="var(--tint-life)" label={t('Organic matter')}>
            {formatNumber(p.organic_matter_pct, 1)}%
          </StatTile>
          <StatTile icon={TrendingUp} tint="var(--tint-slope)" label={t('Average slope')} unit={t('from satellite elevation')}>
            {formatNumber(p.slope_pct, 1)}%
          </StatTile>
        </dl>
        <p className="mt-3 text-[13px] text-muted-foreground">
          {t('Days when satellite greenness is below 0.25, averaged over the last 8 years. This includes winter dormancy and standing stubble: the satellite cannot see stubble, although it still protects the soil. Soil from the USDA soil survey (SSURGO).')}
        </p>
      </CardSection>

      {/* 6. Link to Rotation replay. On a wide screen the card scrolls inside its panel and this stays at the bottom. */}
      <div className="border-t border-border px-6 py-4 lg:sticky lg:bottom-0 lg:z-10 lg:rounded-b-[28px] lg:bg-card/90 lg:backdrop-blur-xl">
        {hasReplay ? (
          <Button asChild width="full">
            <Link to={{ pathname: '/replay', search: `?field=${p.field_id}` }} className="py-2 text-center leading-snug">
              {t('Replay 30 years of weather on this field')}
              <ArrowRight aria-hidden className="h-4 w-4" />
            </Link>
          </Button>
        ) : (
          <>
            <Button width="full" disabled>
              {t('Replay 30 years of weather on this field')}
            </Button>
            <p className="mt-2 text-[13px] text-muted-foreground">
              {t('The replay is not ready for this field yet.')}
            </p>
          </>
        )}
      </div>
    </Card>
  )
}
