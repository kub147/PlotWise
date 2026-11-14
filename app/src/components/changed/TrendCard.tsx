// One climate trend: change per decade, a reliability label and a small year-by-year chart.
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '@/components/ui/card'
import { INDICATORS, indicatorValue, slopeText, type Climate, type Trend } from '@/lib/climate'
import { cn } from '@/lib/utils'

type Point = { year: number; value: number }

// Etykieta wiarygodności: tekst, nie sam kolor.
export function ReliabilityBadge({ reliable }: { reliable: boolean }) {
  return (
    <span
      className={cn(
        'inline-block rounded-full px-2.5 py-0.5 text-[13px] font-medium',
        reliable ? 'bg-leaf-soft text-accent-foreground' : 'bg-foreground/[0.06] text-muted-foreground',
      )}
    >
      {reliable ? 'Reliable trend' : 'Not a reliable trend'}
    </span>
  )
}

type TrendCardProps = {
  trend: Trend
  yearly: Climate['yearly']
  // Jedno zdanie prostym językiem o tym, co ten wskaźnik znaczy dla pola.
  meaning: string
}

export function TrendCard({ trend, yearly, meaning }: TrendCardProps) {
  const info = INDICATORS[trend.indicator]
  const kind = info?.kind ?? 'days'
  const data: Point[] = Object.entries(yearly)
    .map(([year, values]) => ({ year: Number(year), value: values[trend.indicator] }))
    .filter((point) => point.year >= trend.first_year && point.year <= trend.last_year && point.value !== undefined)
    .sort((a, b) => a.year - b.year)

  return (
    <Card className="flex flex-col gap-3 p-6">
      <div>
        <h3 className="text-[17px] font-semibold leading-snug">{info?.title ?? trend.label}</h3>
        <p className="mt-1 text-[13px] leading-snug text-muted-foreground">{meaning}</p>
      </div>

      <div>
        <p className="text-[24px] font-semibold leading-tight">{slopeText(kind, trend.slope_per_decade)}</p>
        <div className="mt-1.5">
          <ReliabilityBadge reliable={trend.reliable} />
        </div>
      </div>

      <div
        className="h-[110px]"
        role="img"
        aria-label={`Yearly values of ${info?.title ?? trend.label}, ${trend.first_year} to ${trend.last_year}`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 6, right: 6, bottom: 0, left: 6 }}>
            <XAxis
              dataKey="year"
              ticks={[trend.first_year, trend.last_year]}
              interval={0}
              padding={{ left: 14, right: 14 }}
              tickLine={false}
              axisLine={{ stroke: 'var(--input)' }}
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip
              cursor={{ stroke: 'var(--input)' }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const point = payload[0].payload as Point
                return (
                  <div className="pw-glass rounded-2xl px-3 py-2 text-[13px]">
                    <span className="font-mono font-semibold">{point.year}</span>: {indicatorValue(kind, point.value)}
                  </div>
                )
              }}
            />
            <Line
              dataKey="value"
              type="linear"
              stroke="var(--chart-gain)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, stroke: 'var(--card)', strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="text-[13px] leading-snug text-muted-foreground">
        Average in the first half of the record:{' '}
        <span className="font-mono font-medium text-foreground">{indicatorValue(kind, trend.mean_first_half)}</span>.
        Second half:{' '}
        <span className="font-mono font-medium text-foreground">{indicatorValue(kind, trend.mean_second_half)}</span>.
        Source: {trend.source}.
      </p>
    </Card>
  )
}
