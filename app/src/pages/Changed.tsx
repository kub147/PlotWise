// "What has changed" view: climate trends for the field, rainfall, water storage (GRACE),
// rotations in the county and a surface temperature comparison (ECOSTRESS).
// All numbers and "reliable" labels come from climate/<field_id>.json; nothing is hard-coded.
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ReliabilityBadge, TrendCard } from '@/components/changed/TrendCard'
import { Card } from '@/components/ui/card'
import {
  INDICATORS,
  slopeText,
  useJson,
  type Climate,
  type CountyRotations,
  type PrecipRow,
  type Trend,
} from '@/lib/climate'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { imageUrl, useHeatSummary, type HeatSummary } from '@/lib/fieldMedia'
import { useDateLocale, useT } from '@/lib/i18n'
import { cmToInches, cToF, formatNumber, mmToInches } from '@/lib/units'

// The four trends on the main screen (spec 5.2) and what each means for the field.
const MAIN_TRENDS: { indicator: string; meaning: string }[] = [
  { indicator: 'gdd10_apr_oct', meaning: 'How much warmth the crop gets from April to October.' },
  { indicator: 'first_fall_frost_doy', meaning: 'When the first freezing night of fall arrives.' },
  { indicator: 'heavy_rain_days_25mm', meaning: 'Days when an inch or more falls at once.' },
  { indicator: 'eto_mm', meaning: 'How much water the air can pull from soil and plants in a year.' },
]

const signed = (value: number, digits: number) =>
  `${value > 0 ? '+' : value < 0 ? '−' : ''}${formatNumber(Math.abs(value), digits)}`

// Rainfall card: highlighted, because it is the most important caveat of the whole view.
function RainfallCard({ trend, rows }: { trend: Trend | undefined; rows: PrecipRow[] }) {
  const t = useT()
  const reliable = trend?.reliable ?? false
  const power = rows.find((row) => row.product === 'POWER')
  const others = rows.filter((row) => row.product !== 'POWER')
  // The sentence about the disagreement is written only when the field's data really shows it.
  const powerDries = power !== undefined && power.own_slope_mm_per_decade < 0
  const othersDoNot = others.length > 0 && others.every((row) => row.own_slope_mm_per_decade >= 0)

  return (
    <section
      aria-labelledby="rain-heading"
      className="rounded-[28px] bg-warning p-6"
    >
      <h2 id="rain-heading" className="text-[24px] font-semibold leading-tight">
        {t('Total rainfall')}: {reliable && trend ? slopeText('mm', trend.slope_per_decade, t) : t('No reliable trend')}
      </h2>
      <p className="mt-2 max-w-[70ch] text-[15px] leading-snug">
        {powerDries && othersDoNot
          ? t('One record, NASA POWER, shows this place getting drier. The other rainfall records for the same place do not show that. So we do not say that rain is declining here.')
          : t('The rainfall records for this place do not agree on a clear change. So we do not say that rain is declining or increasing here.')}{' '}
        {t('Rain here swings a lot from year to year, and that swing is larger than any change we can measure.')}
      </p>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[420px] text-left text-[13px]">
          <caption className="sr-only">{t('Yearly rainfall trend in each rainfall record')}</caption>
          <thead>
            <tr className="border-b border-foreground/15">
              <th scope="col" className="py-1.5 pr-3 font-semibold">
                {t('Rainfall record')}
              </th>
              <th scope="col" className="py-1.5 pr-3 font-semibold">
                {t('Years')}
              </th>
              <th scope="col" className="py-1.5 pr-3 text-right font-semibold">
                {t('Change per decade')}
              </th>
              <th scope="col" className="py-1.5 font-semibold">
                {t('Reliable?')}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.product} className="border-b border-foreground/10">
                <th scope="row" className="py-1.5 pr-3 font-medium">
                  {row.product === 'POWER' ? 'NASA POWER' : row.product === 'IMERG' ? 'NASA GPM IMERG' : row.product}
                </th>
                <td className="py-1.5 pr-3 font-mono">
                  {row.own_period[0]}–{row.own_period[1]}
                </td>
                <td className="py-1.5 pr-3 text-right font-mono">
                  {t('{n} in per decade', { n: signed(mmToInches(row.own_slope_mm_per_decade), 1) })}
                </td>
                {/* Same rule as in the file: reliable when p < 0.05 */}
                <td className="py-1.5">{row.own_mk_p < 0.05 ? t('Yes') : t('No')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// GRACE: change in regional water storage since 2002.
function WaterStorage({ grace }: { grace: Climate['grace'] }) {
  const t = useT()
  const locale = useDateLocale()
  const data = grace.series.map((point) => ({
    time: Date.parse(`${point.date}T00:00:00Z`),
    inches: cmToInches(point.lwe_cm),
  }))
  const firstYear = Number(grace.period[0].slice(0, 4))
  const lastYear = Number(grace.period[1].slice(0, 4))
  const ticks: number[] = []
  for (let year = Math.ceil(firstYear / 4) * 4; year <= lastYear; year += 4) ticks.push(Date.UTC(year, 0, 1))

  return (
    <Card className="p-6">
      <h2 className="text-[19px] font-semibold">{t('Water stored in the region')}</h2>
      <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
        {t('Groundwater, soil water and surface water together, weighed from orbit by NASA’s GRACE satellites.')}
      </p>
      <p className="mt-3 font-mono text-[24px] font-semibold leading-tight">
        {t('{n} in', { n: signed(cmToInches(grace.total_change_cm), 1) })}
        <span className="font-sans text-[15px] font-medium text-muted-foreground">
          {' '}
          {t('of water since {year} ({rate} in a year)', { year: firstYear, rate: signed(cmToInches(grace.trend_cm_per_year), 2) })}
        </span>
      </p>
      <div className="mt-1.5">
        <ReliabilityBadge reliable={grace.reliable} />
      </div>

      <div className="mt-3 overflow-x-auto">
        <div
          className="h-[220px] min-w-[520px]"
          role="img"
          aria-label={t('Area chart of regional water storage from {from} to {to}, in inches of water compared with the 2004 to 2009 average', { from: firstYear, to: lastYear })}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey="time"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                ticks={ticks}
                tickFormatter={(time: number) => String(new Date(time).getUTCFullYear())}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
              />
              <YAxis
                width={56}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value: number) => t('{n} in (axis)', { n: value })}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
              />
              <ReferenceLine y={0} stroke="var(--foreground)" strokeWidth={1} />
              <Tooltip
                cursor={{ stroke: 'var(--input)' }}
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null
                  const point = payload[0].payload as { time: number; inches: number }
                  return (
                    <div className="pw-glass rounded-2xl px-3 py-2 text-[13px]">
                      <p className="font-semibold">
                        {new Date(point.time).toLocaleDateString(locale, { year: 'numeric', month: 'short', timeZone: 'UTC' })}
                      </p>
                      <p>
                        <span className="font-mono font-semibold">{t('{n} in', { n: signed(point.inches, 1) })}</span>{' '}
                        {t('vs the 2004–2009 average')}
                      </p>
                    </div>
                  )
                }}
              />
              <Area
                dataKey="inches"
                type="linear"
                stroke="var(--chart-gain)"
                strokeWidth={2}
                fill="var(--chart-gain)"
                fillOpacity={0.12}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
        {t('Inches of water compared with the 2004–2009 average. This is one value for an area about 190 miles across, never a value for one field.')}
      </p>
    </Card>
  )
}

// Rotations in the county: horizontal bars with a label and a percentage (no axis; the numbers sit by the bars).
function CountyRotationBars({ county, years, note }: { county: CountyRotations['counties'][string]; years: string; note: string }) {
  const t = useT()
  const labels: Record<string, string> = {
    'W-F': 'Wheat – fallow',
    'W-S-F': 'Wheat – sorghum – fallow',
    'W-C-F': 'Wheat – corn – fallow',
    'W-F to 3-year': 'Moved from wheat – fallow to a 3-year rotation',
    'no fallow': 'No fallow in 8 years',
    'other with fallow': 'Other sequences with fallow',
  }
  const rows = Object.entries(county.rotations)
  const largest = Math.max(...rows.map(([, value]) => value.share_of_area), 0.01)

  return (
    <Card className="p-6">
      <h2 className="text-[19px] font-semibold">{t('How fields in {name} County are farmed', { name: county.name })}</h2>
      <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
        {t('Share of the area of {count} fields, read from the crop maps of {years}.', { count: formatNumber(county.fields), years })}
      </p>
      <ul className="mt-4 flex flex-col gap-2.5">
        {rows.map(([id, value]) => (
          <li key={id}>
            <div className="flex items-baseline justify-between gap-3 text-[15px]">
              <span>{t(labels[id] ?? id)}</span>
              <span className="font-mono font-semibold">{formatNumber(value.share_of_area * 100)}%</span>
            </div>
            <div className="mt-1 h-1.5 rounded-full bg-foreground/[0.07]" aria-hidden>
              <div
                className="pw-brand h-full rounded-full"
                style={{ width: `${(value.share_of_area / largest) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[13px] leading-snug text-muted-foreground">{t(note)}</p>
    </Card>
  )
}

// ECOSTRESS: the same moment, fallow against sorghum. The scenes cover the Tribune area only.
function HeatComparison({ heat }: { heat: HeatSummary }) {
  const t = useT()
  const locale = useDateLocale()
  const rows = heat.scenes
    .map((scene) => ({
      scene,
      fallow: scene.by_crop_class.fallow?.mean_c,
      sorghum: scene.by_crop_class.sorghum?.mean_c,
    }))
    .filter((row): row is typeof row & { fallow: number; sorghum: number } => row.fallow !== undefined && row.sorghum !== undefined)
    .sort((a, b) => b.scene.time_utc.localeCompare(a.scene.time_utc))
  if (rows.length === 0) return null
  // The image is shown for the scene with the largest difference, so that the point is visible.
  const widest = rows.reduce((best, row) => (row.fallow - row.sorghum > best.fallow - best.sorghum ? row : best))
  const day = (timeUtc: string) =>
    new Date(`${timeUtc.slice(0, 10)}T00:00:00Z`).toLocaleDateString(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    })
  const file = widest.scene.image.split('/').pop() ?? widest.scene.image
  // Sorghum is planted in Kansas in early June (evidence.md, answer 2), so the June scene shows no difference.
  const hasJuneScene = rows.some((row) => row.scene.time_utc.slice(5, 7) === '06')

  return (
    <Card className="p-6">
      <h2 className="text-[19px] font-semibold">{t('Same moment, bare fallow against sorghum')}</h2>
      <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
        {t('Ground surface temperature around Tribune from NASA’s ECOSTRESS instrument, averaged over all fields of each kind.')}
      </p>
      <div className="mt-4 grid gap-4 sm:grid-cols-[180px_minmax(0,1fr)]">
        <a href={imageUrl(file)} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-2xl">
          <img
            src={imageUrl(file)}
            alt={t('Surface heat map around Tribune on {date}; blue is cooler, red is hotter', { date: day(widest.scene.time_utc) })}
            loading="lazy"
            className="aspect-square w-full object-cover"
          />
        </a>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-1.5 pr-3 font-semibold">
                  {t('Day')}
                </th>
                <th scope="col" className="py-1.5 pr-3 text-right font-semibold">
                  {t('Fallow')}
                </th>
                <th scope="col" className="py-1.5 pr-3 text-right font-semibold">
                  {t('Sorghum')}
                </th>
                <th scope="col" className="py-1.5 text-right font-semibold">
                  {t('Fallow is hotter by')}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.scene.scene} className="border-b border-border">
                  <th scope="row" className="py-1.5 pr-3 font-medium">
                    {day(row.scene.time_utc)}
                  </th>
                  <td className="py-1.5 pr-3 text-right font-mono">{formatNumber(cToF(row.fallow))}°F</td>
                  <td className="py-1.5 pr-3 text-right font-mono">{formatNumber(cToF(row.sorghum))}°F</td>
                  <td className="py-1.5 text-right font-mono font-semibold">
                    {/* Temperature difference: no offset of 32 */}
                    {signed((row.fallow - row.sorghum) * 1.8, 0)}°F
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
            {t('The picture is from {date}. This is the temperature of the ground surface, not of the air, at one moment in each day.', { date: day(widest.scene.time_utc) })}
            {hasJuneScene && ` ${t('Sorghum is planted in early June, so on the June day it has barely come up and the two look the same.')}`}
          </p>
        </div>
      </div>
    </Card>
  )
}

type ChangedProps = {
  data: AppData
  selected: FieldFeature
}

export function Changed({ data, selected }: ChangedProps) {
  const t = useT()
  const p = selected.properties
  const hasClimate = data.manifest.climate.includes(p.field_id)
  const climateState = useJson<Climate>(hasClimate ? `climate/${p.field_id}.json` : null)
  const countyState = useJson<CountyRotations>('county_field_rotations.json')
  const heat = useHeatSummary()

  if (climateState.status === 'loading') {
    return <p className="p-6 text-muted-foreground">{t('Loading the climate record…')}</p>
  }
  if (climateState.status === 'missing') {
    return (
      <div className="mx-auto max-w-[1680px] p-4 lg:p-6">
        <h1 className="text-[34px] font-semibold leading-tight">{t('What has changed')}</h1>
        <p className="mt-2 text-muted-foreground">{t('There is no climate record for this field yet.')}</p>
      </div>
    )
  }

  const climate = climateState.data
  const byName = new Map(climate.trends.map((trend) => [trend.indicator, trend]))
  const warmth = byName.get('gdd10_apr_oct')
  const rain = byName.get('precip_mm')
  const mainNames = new Set(MAIN_TRENDS.map((entry) => entry.indicator))
  const otherTrends = climate.trends.filter((trend) => !mainNames.has(trend.indicator))
  // County key in the file: "ks" + the last three digits of the FIPS code (20071 -> ks071).
  const county =
    countyState.status === 'ready' ? countyState.data.counties[`ks${p.county_fips.slice(2)}`] : undefined

  // The headline says only what this field's data confirms.
  const warmer = warmth !== undefined && warmth.reliable && warmth.slope_per_decade > 0
  const headline = [
    warmer ? t('It is warmer here than when you started.') : t('The warming here is not clear in this record.'),
    rain !== undefined && !rain.reliable ? t('Rain has not clearly changed.') : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="mx-auto flex max-w-[1680px] flex-col gap-6 p-4 lg:p-6">
      <header>
        <p className="text-[15px] text-muted-foreground">
          {t('{field} · weather record {period}', { field: fieldShortName(p), period: warmth ? `${warmth.first_year}–${warmth.last_year}` : '' })}
        </p>
        <h1 className="mt-1 max-w-[28ch] text-[34px] font-semibold leading-tight">{headline}</h1>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {MAIN_TRENDS.map(({ indicator, meaning }) => {
          const trend = byName.get(indicator)
          return trend ? <TrendCard key={indicator} trend={trend} yearly={climate.yearly} meaning={meaning} /> : null
        })}
      </div>

      <RainfallCard trend={rain} rows={climate.precip_crosscheck.windows.annual.rows} />

      <div className="grid gap-4 lg:grid-cols-2">
        <WaterStorage grace={climate.grace} />
        {county && countyState.status === 'ready' && (
          <CountyRotationBars county={county} years={countyState.data.years} note={countyState.data.note} />
        )}
      </div>

      {heat && <HeatComparison heat={heat} />}

      <details className="pw-sheet rounded-[28px]">
        <summary className="flex min-h-14 cursor-pointer items-center px-6 text-[15px] font-medium">
          {t('The other {count} measures we checked', { count: otherTrends.length })}
        </summary>
        <div className="overflow-x-auto px-6 pb-5">
          <table className="w-full min-w-[520px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-1.5 pr-3 font-semibold">
                  {t('Measure')}
                </th>
                <th scope="col" className="py-1.5 pr-3 font-semibold">
                  {t('Change')}
                </th>
                <th scope="col" className="py-1.5 pr-3 font-semibold">
                  {t('Reliable?')}
                </th>
                <th scope="col" className="py-1.5 font-semibold">
                  {t('Source')}
                </th>
              </tr>
            </thead>
            <tbody>
              {otherTrends.map((trend) => {
                const info = INDICATORS[trend.indicator]
                return (
                  <tr key={trend.indicator} className="border-b border-border">
                    <th scope="row" className="py-1.5 pr-3 font-medium">
                      {t(info?.title ?? trend.label)}
                    </th>
                    <td className="py-1.5 pr-3 font-mono">{slopeText(info?.kind ?? 'days', trend.slope_per_decade, t)}</td>
                    <td className="py-1.5 pr-3">{trend.reliable ? t('Yes') : t('No')}</td>
                    <td className="py-1.5">{trend.source}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="mt-2 text-[13px] text-muted-foreground">
            {t('“Reliable” means a standard trend test (Mann-Kendall) gives less than a 5% chance that the change is just year-to-year noise. Weather comes from grids 2.5 to 30 miles wide: it describes the area, not the single field.')}
          </p>
        </div>
      </details>
    </div>
  )
}
