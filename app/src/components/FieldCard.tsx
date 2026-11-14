// Prawa kolumna widoku „My field": karta wybranego pola.
// Kolejność sekcji jest wiążąca: nazwa i powierzchnia, płodozmian, historia upraw, gleba i goła ziemia,
// wykres zieloności, dwa zdjęcia, przycisk przejścia do Rotation replay.
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { CropLegend, CropTile } from '@/components/CropTile'
import { Button } from '@/components/ui/button'
import { Card, CardSection, SectionLabel } from '@/components/ui/card'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { rotationPhases, toCropLetter, type CropLetter } from '@/lib/rotation'
import { formatNumber, haToAcres, mmToInches } from '@/lib/units'

// Miejsce na element, który powstanie w kolejnym kroku (wykres, zdjęcie).
function Slot({ title, note, className }: { title: string; note: string; className?: string }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-md border border-dashed border-input bg-muted px-3 text-center ${className ?? ''}`}
    >
      <p className="text-[13px] font-semibold">{title}</p>
      <p className="text-[13px] text-muted-foreground">{note}</p>
    </div>
  )
}

// Nazwa uprawy z CDL do podpisu: "CDL 60" to klasa bez nazwy w pliku.
function historyName(name: string) {
  const code = /^CDL (\d+)$/.exec(name)
  return code ? `other crop (CDL class ${code[1]})` : name
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
          {county ? `${county} County, Kansas` : 'Kansas'} ·{' '}
          <span className="font-mono font-medium text-foreground">{formatNumber(haToAcres(p.area_ha))}</span> acres
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
        <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3">
          <div>
            <dt className="text-[13px] text-muted-foreground">Water the soil can hold for plants</dt>
            <dd className="font-mono text-[19px] font-semibold">
              {formatNumber(mmToInches(p.awc_mm), 1)} <span className="font-sans text-[13px] font-medium text-muted-foreground">in, top 5 ft</span>
            </dd>
          </div>
          <div>
            <dt className="text-[13px] text-muted-foreground">Days a year with bare ground</dt>
            <dd className="font-mono text-[19px] font-semibold">
              {formatNumber(p.bare_days_per_year)} <span className="font-sans text-[13px] font-medium text-muted-foreground">seen from satellite</span>
            </dd>
          </div>
          <div>
            <dt className="text-[13px] text-muted-foreground">Organic matter</dt>
            <dd className="font-mono text-[15px] font-medium">{formatNumber(p.organic_matter_pct, 1)}%</dd>
          </div>
          <div>
            <dt className="text-[13px] text-muted-foreground">Slope</dt>
            <dd className="font-mono text-[15px] font-medium">{formatNumber(p.slope_pct, 1)}%</dd>
          </div>
        </dl>
        <p className="mt-3 text-[13px] text-muted-foreground">
          Bare ground means no green cover, averaged over the last 8 years. Standing stubble still protects the soil and
          is not counted. Soil from the USDA soil survey (SSURGO).
        </p>
      </CardSection>

      {/* 5. Miejsce na wykres zieloności (NDVI) */}
      <CardSection>
        <SectionLabel>Greenness over the years</SectionLabel>
        <Slot title="Greenness chart" note="Not built yet." className="h-36" />
      </CardSection>

      {/* 6. Dwa miejsca na zdjęcia */}
      <CardSection>
        <SectionLabel>From above</SectionLabel>
        <div className="grid grid-cols-2 gap-3">
          <Slot
            title="Aerial photo"
            note={hasAerial ? 'Not built yet.' : 'No aerial photo for this field yet.'}
            className="aspect-square"
          />
          <Slot title="Surface heat" note="Not built yet." className="aspect-square" />
        </div>
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
              The replay is not ready for this field yet. It is ready for the Tribune fields.
            </p>
          </>
        )}
      </CardSection>
    </Card>
  )
}
