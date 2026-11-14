// Prawa kolumna widoku „My field": karta wybranego pola.
// Kolejność sekcji jest wiążąca: nazwa i powierzchnia, płodozmian, historia upraw, gleba i goła ziemia,
// wykres zieloności, dwa obrazy z góry, przycisk przejścia do Rotation replay.
import { ArrowRight, Droplets, Sprout, Sun, TrendingUp, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CropLegend, CropTile } from '@/components/CropTile'
import { Button } from '@/components/ui/button'
import { Card, CardSection, SectionLabel } from '@/components/ui/card'
import { FieldPhotos } from '@/components/field/FieldPhotos'
import { GreennessChart } from '@/components/field/GreennessChart'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { useHeatSummary, useNdvi } from '@/lib/fieldMedia'
import { rotationPhases, toCropLetter, type CropLetter } from '@/lib/rotation'
import { formatNumber, haToAcres, mmToInches } from '@/lib/units'

// Nazwa uprawy z CDL do podpisu: "CDL 60" to klasa bez nazwy w pliku.
function historyName(name: string) {
  const code = /^CDL (\d+)$/.exec(name)
  return code ? `other crop (CDL class ${code[1]})` : name
}

// Kafelek z jedną liczbą: ikona, liczba, jednostka i opis, na lekko zabarwionym tle.
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
}

export function FieldCard({ data, field }: FieldCardProps) {
  const p = field.properties
  const county = data.countyNames[p.county_fips]
  const phases = rotationPhases(p.current_rotation)
  const hasReplay = data.manifest.results.includes(p.field_id)
  const hasAerial = data.manifest.naip.includes(p.field_id)
  const ndvi = useNdvi(p.field_id, data.manifest.ndvi.includes(p.field_id))
  const heat = useHeatSummary()

  // Historia upraw: jedna litera na rok, od crop_sequence_first_year.
  const history = [...p.crop_sequence].map((letter, i) => {
    const year = p.crop_sequence_first_year + i
    return { year, letter: toCropLetter(letter), name: historyName(p.crop_history_names[String(year)] ?? 'no data') }
  })
  const firstYear = history[0]?.year
  const lastYear = history[history.length - 1]?.year
  const lettersUsed = (['W', 'S', 'C', 'F', 'O'] as CropLetter[]).filter((letter) =>
    history.some((entry) => entry.letter === letter),
  )
  const otherYears = history.filter((entry) => entry.letter === 'O')

  return (
    <Card>
      {/* 1. Nazwa i powierzchnia */}
      <CardSection>
        <p className="font-mono text-[13px] font-medium text-muted-foreground">{fieldShortName(p)}</p>
        <h2 className="mt-0.5 text-[21px] font-semibold leading-tight">{p.name}</h2>
        <p className="mt-1.5 text-[15px] text-muted-foreground">
          <span className="font-mono font-semibold text-foreground">{formatNumber(haToAcres(p.area_ha))}</span> acres in{' '}
          {county ? `${county} County, Kansas` : 'Kansas'}
        </p>
      </CardSection>

      {/* 2. Aktualny płodozmian */}
      <CardSection>
        <SectionLabel>Rotation today</SectionLabel>
        {phases ? (
          <div className="flex items-center gap-3">
            <span className="flex gap-1">
              {phases.map((letter, i) => (
                <CropTile key={i} letter={letter} />
              ))}
            </span>
            <span className="font-mono text-[15px] font-medium">{phases.join('-')}</span>
          </div>
        ) : (
          <p className="text-[15px]">No fallow – not one of the modeled rotations.</p>
        )}
      </CardSection>

      {/* 3. Historia upraw */}
      <CardSection>
        <SectionLabel>
          What grew here, {firstYear}–{lastYear}
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
        <p className="mt-2 text-[13px] text-muted-foreground">Read from the USDA Cropland Data Layer, one crop per year.</p>
      </CardSection>

      {/* 4. Gleba i dni z gołą ziemią */}
      <CardSection>
        <SectionLabel>Soil and bare ground</SectionLabel>
        <p className="text-[15px] font-medium">{p.soil_map_unit}</p>
        {/* Cztery liczby jako kolorowe kafelki: kolor mówi, czego dotyczy liczba (woda, ziemia, próchnica, nachylenie) */}
        <dl className="mt-3 grid grid-cols-2 gap-2.5">
          <StatTile icon={Droplets} tint="var(--tint-water)" label="Water the soil can hold for plants" unit="in, top 5 ft">
            {formatNumber(mmToInches(p.awc_mm), 1)}
          </StatTile>
          <StatTile icon={Sun} tint="var(--tint-soil)" label="Days a year with bare ground" unit="seen from satellite">
            {formatNumber(p.bare_days_per_year)}
          </StatTile>
          <StatTile icon={Sprout} tint="var(--tint-life)" label="Organic matter">
            {formatNumber(p.organic_matter_pct, 1)}%
          </StatTile>
          <StatTile icon={TrendingUp} tint="var(--tint-slope)" label="Slope">
            {formatNumber(p.slope_pct, 1)}%
          </StatTile>
        </dl>
        <p className="mt-3 text-[13px] text-muted-foreground">
          Bare ground means no green cover, averaged over the last 8 years. Standing stubble still protects the soil and
          is not counted. Soil from the USDA soil survey (SSURGO).
        </p>
      </CardSection>

      {/* 5. Wykres zieloności (NDVI) */}
      <CardSection>
        <SectionLabel>Greenness over the years</SectionLabel>
        <GreennessChart fieldId={p.field_id} state={ndvi} threshold={p.ndvi_bare_threshold} />
      </CardSection>

      {/* 6. Zdjęcie lotnicze i temperatura powierzchni */}
      <CardSection>
        <SectionLabel>From above</SectionLabel>
        <FieldPhotos fieldId={p.field_id} fieldLabel={fieldShortName(p)} hasAerial={hasAerial} heat={heat} />
      </CardSection>

      {/* 7. Przejście do Rotation replay */}
      <CardSection>
        {hasReplay ? (
          <Button asChild width="full">
            <Link to={{ pathname: '/replay', search: `?field=${p.field_id}` }}>
              Replay the last 30 years on this field
              <ArrowRight aria-hidden className="h-4 w-4" />
            </Link>
          </Button>
        ) : (
          <>
            <Button width="full" disabled>
              Replay the last 30 years on this field
            </Button>
            <p className="mt-2 text-[13px] text-muted-foreground">
              The replay is not ready for this field yet.
            </p>
          </>
        )}
      </CardSection>
    </Card>
  )
}
