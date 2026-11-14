// Wykres zieloności pola (NDVI z Landsata) od 2008 r. Jedna seria, więc bez legendy: tytuł mówi, co widać.
// Szary pas na dole to wartości poniżej progu gołej ziemi z fields.geojson (ndvi_bare_threshold).
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
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-[13px] shadow-md">
      <p className="font-semibold">{new Date(point.time).toLocaleDateString('en-US', DAY_FORMAT)}</p>
      <p>
        Greenness <span className="font-mono font-semibold">{point.ndvi.toFixed(2)}</span>
      </p>
      {point.ndvi < threshold && <p className="text-muted-foreground">Counted as bare ground</p>}
    </div>
  )
}

type GreennessChartProps = {
  fieldId: string
  state: NdviState
  // Próg gołej ziemi z fields.geojson (ndvi_bare_threshold).
  threshold: number
}

export function GreennessChart({ fieldId, state, threshold }: GreennessChartProps) {
  if (state.status === 'loading') {
    return <p className="text-[13px] text-muted-foreground">Loading the greenness record…</p>
  }
  if (state.status === 'missing' || state.points.length === 0) {
    return <p className="text-[13px] text-muted-foreground">No greenness record for this field yet.</p>
  }

  const points = state.points
  const firstYear = new Date(points[0].time).getUTCFullYear()
  const lastYear = new Date(points[points.length - 1].time).getUTCFullYear()
  // Oś czasu od 1 stycznia pierwszego roku do 1 stycznia roku po ostatnim; podpis co dwa lata.
  const domain: [number, number] = [Date.UTC(firstYear, 0, 1), Date.UTC(lastYear + 1, 0, 1)]
  const ticks: number[] = []
  for (let year = firstYear; year <= lastYear + 1; year += 2) ticks.push(Date.UTC(year, 0, 1))

  return (
    <div>
      {/* Wykres jest szerszy niż karta i przewija się w poziomie, żeby 18 lat było czytelne */}
      <div className="overflow-x-auto rounded-md border border-border">
        <div
          className="h-[220px] min-w-[760px] pr-2 pt-3"
          role="img"
          aria-label={`Line chart of field greenness from ${firstYear} to ${lastYear}. Green peaks are growing crops; the low stretches are bare ground.`}
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
        Greenness (NDVI) seen by Landsat satellites, {points.length} clear days. Near 0 is bare soil; higher means more
        green plants. In the grey band (below {threshold}) the field counts as bare ground. Scroll sideways to see all
        years.{' '}
        <a
          href={dataUrl(`ndvi/${fieldId}.csv`)}
          download
          className="font-medium text-primary underline underline-offset-2"
        >
          Download the numbers (CSV)
        </a>
      </p>
    </div>
  )
}
