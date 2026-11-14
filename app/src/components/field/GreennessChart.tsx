// Field greenness chart (Landsat NDVI) since 2008. One series, so no legend: the title says what is shown.
// The grey band at the bottom marks values below the bare-ground threshold from fields.geojson (ndvi_bare_threshold).
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { dataUrl } from '@/lib/data'
import type { NdviPoint, NdviState } from '@/lib/fieldMedia'
import { useDateLocale, useT } from '@/lib/i18n'

const DAY_FORMAT: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' }

function ChartTooltip({
  active,
  payload,
  threshold,
}: {
  active?: boolean
  payload?: { payload: NdviPoint }[]
  threshold: number
}) {
  const t = useT()
  const locale = useDateLocale()
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="pw-glass rounded-2xl px-3.5 py-2.5 text-[13px]">
      <p className="font-semibold">{new Date(point.time).toLocaleDateString(locale, DAY_FORMAT)}</p>
      <p>
        {t('Greenness')} <span className="font-mono font-semibold">{point.ndvi.toFixed(2)}</span>
      </p>
      {point.ndvi < threshold && <p className="text-muted-foreground">{t('Counted as bare ground')}</p>}
    </div>
  )
}

type GreennessChartProps = {
  fieldId: string
  state: NdviState
  // Bare-ground threshold from fields.geojson (ndvi_bare_threshold).
  threshold: number
}

export function GreennessChart({ fieldId, state, threshold }: GreennessChartProps) {
  const t = useT()
  if (state.status === 'loading') {
    return <p className="text-[13px] text-muted-foreground">{t('Loading the greenness record…')}</p>
  }
  if (state.status === 'missing' || state.points.length === 0) {
    return <p className="text-[13px] text-muted-foreground">{t('No greenness record for this field yet.')}</p>
  }

  const points = state.points
  const firstYear = new Date(points[0].time).getUTCFullYear()
  const lastYear = new Date(points[points.length - 1].time).getUTCFullYear()
  // Time axis from 1 January of the first year to 1 January after the last year; a label every two years.
  const domain: [number, number] = [Date.UTC(firstYear, 0, 1), Date.UTC(lastYear + 1, 0, 1)]
  const ticks: number[] = []
  for (let year = firstYear; year <= lastYear + 1; year += 2) ticks.push(Date.UTC(year, 0, 1))

  return (
    <div>
      {/* The chart is wider than the card and scrolls sideways so that 18 years stay readable */}
      <div className="pw-scroll overflow-x-auto rounded-2xl bg-foreground/[0.03]">
        <div
          className="h-[220px] min-w-[760px] pr-2 pt-3"
          role="img"
          aria-label={t('Line chart of field greenness from {from} to {to}. Green peaks are growing crops; the low stretches are bare ground.', { from: firstYear, to: lastYear })}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <ReferenceArea y1={0} y2={threshold} fill="var(--muted-foreground)" fillOpacity={0.14} strokeOpacity={0} />
              <ReferenceLine y={threshold} stroke="var(--muted-foreground)" strokeDasharray="4 3" />
              <XAxis
                dataKey="time"
                type="number"
                scale="time"
                domain={domain}
                ticks={ticks}
                tickFormatter={(time: number) => String(new Date(time).getUTCFullYear())}
                tickLine={false}
                axisLine={{ stroke: 'var(--input)' }}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
              />
              <YAxis
                width={36}
                domain={[0, 1]}
                ticks={[0, 0.25, 0.5, 0.75, 1]}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
              />
              <Tooltip content={<ChartTooltip threshold={threshold} />} cursor={{ stroke: 'var(--input)' }} />
              <Line
                dataKey="ndvi"
                type="linear"
                stroke="var(--chart-green)"
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 4, stroke: 'var(--card)', strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
        {t('Greenness (NDVI) seen by Landsat satellites, {days} clear days. Near 0 is bare soil; higher means more green plants. In the grey band (below {threshold}) the field counts as bare ground. Scroll sideways to see all years.', { days: points.length, threshold })}{' '}
        <a
          href={dataUrl(`ndvi/${fieldId}.csv`)}
          download
          className="font-medium text-primary underline underline-offset-2"
        >
          {t('Download the numbers (CSV)')}
        </a>
      </p>
    </div>
  )
}
