// "Year by year" chart: net return per acre of the selected rotation, year after year.
// Bars from zero: blue = year above zero, orange = year below zero (pair checked for colour blindness).
// Failure years are marked with a grey band and the year label, not by colour alone.
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useT } from '@/lib/i18n'
import type { RotationResult } from '@/lib/results'
import { rotationDisplayName } from '@/lib/rotation'
import { formatUsd } from '@/lib/units'

// Years in which the K-State trials at Tribune lost a whole crop:
// wheat 2002 and 2013 (evidence.md, E01), sorghum 2002 and 2012 (E02).
const FAILURE_YEARS = [2002, 2012, 2013]

// Neighbouring years are merged into one band so the labels do not overlap: 2012 and 2013 -> "2012–13".
const FAILURE_SPANS = FAILURE_YEARS.reduce<{ from: number; to: number }[]>((spans, year) => {
  const last = spans[spans.length - 1]
  if (last && year === last.to + 1) last.to = year
  else spans.push({ from: year, to: year })
  return spans
}, [])

type Point = { year: number; value: number }

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return <TooltipBody point={point} />
}

function TooltipBody({ point }: { point: Point }) {
  const t = useT()
  return (
    <div className="pw-glass rounded-2xl px-3.5 py-2.5 text-[13px]">
      <p className="font-mono font-semibold">{point.year}</p>
      <p>
        <span className="font-mono font-semibold">{formatUsd(point.value)}</span> {t('per acre')}
      </p>
      {FAILURE_YEARS.includes(point.year) && <p className="text-muted-foreground">{t('Crop failure year at Tribune')}</p>}
    </div>
  )
}

type YearChartProps = {
  rotation: RotationResult
  // Site of the field (results `site`). The failure years were observed at Tribune only.
  site?: string
}

export function YearChart({ rotation, site }: YearChartProps) {
  const data: Point[] = rotation.net_return_usd_acre.map(([year, value]) => ({ year, value }))
  const firstYear = data[0]?.year
  const lastYear = data[data.length - 1]?.year
  const t = useT()
  const name = rotationDisplayName(t(rotation.name))

  return (
    <section aria-labelledby="year-chart-heading">
      <h2 id="year-chart-heading" className="text-[19px] font-semibold">
        {t('Year by year')}
      </h2>
      <p className="mt-1 text-[13px] text-muted-foreground">
        {t('{name}: return per acre in each year, {from}–{to}, in 2025 dollars. Hover or tap a bar for the number.', {
          name,
          from: firstYear ?? '',
          to: lastYear ?? '',
        })}
      </p>

      {/* On a narrow screen the chart scrolls sideways instead of shrinking */}
      <div className="mt-3 overflow-x-auto pw-sheet rounded-3xl p-4">
        <div className="h-[300px] min-w-[600px]" role="img" aria-label={t('Bar chart of yearly net return per acre for {name}. The table below has the same numbers.', { name })}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 22, right: 8, bottom: 0, left: 0 }} barCategoryGap={2}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              {FAILURE_SPANS.map((span) => (
                <ReferenceArea
                  key={span.from}
                  x1={span.from}
                  x2={span.to}
                  fill="var(--muted-foreground)"
                  fillOpacity={0.16}
                  strokeOpacity={0}
                  label={{
                    value: span.from === span.to ? String(span.from) : `${span.from}–${String(span.to).slice(2)}`,
                    position: 'top', fontSize: 12,
                    fontWeight: 600,
                    fill: 'var(--foreground)',
                  }}
                />
              ))}
              <XAxis
                dataKey="year"
                tickLine={false}
                axisLine={false}
                interval={1}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
              />
              <YAxis
                width={52}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value: number) => formatUsd(value)}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
              />
              <ReferenceLine y={0} stroke="var(--foreground)" strokeWidth={1} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--muted)', opacity: 0.6 }} />
              <Bar dataKey="value" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                {data.map((point) => (
                  <Cell key={point.year} fill={point.value >= 0 ? 'var(--chart-gain)' : 'var(--chart-loss)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-[13px] text-muted-foreground">
          <li className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-chart-gain" aria-hidden /> {t('Year above zero')}
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-chart-loss" aria-hidden /> {t('Year below zero')}
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-muted-foreground/25 ring-1 ring-inset ring-input" aria-hidden />
            {t('Shaded: {years}, years the K-State field trials at Tribune lost a whole crop', { years: FAILURE_YEARS.join(', ') })}
            {site && site !== 'Tribune' && t('. Shown for reference: {site} had its own weather in those years', { site })}
          </li>
        </ul>
      </div>

      <details className="mt-2">
        <summary className="flex min-h-11 cursor-pointer items-center text-[15px] font-medium text-primary underline underline-offset-4">
          {t('Show the numbers as a table')}
        </summary>
        <div className="pw-sheet pw-scroll max-h-72 overflow-auto rounded-3xl">
          <table className="w-full text-left text-[13px]">
            <thead className="sticky top-0 bg-muted">
              <tr>
                <th scope="col" className="px-3 py-2 font-semibold">
                  {t('Year')}
                </th>
                <th scope="col" className="px-3 py-2 text-right font-semibold">
                  {t('Return per acre')}
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((point) => (
                <tr key={point.year} className="border-t border-border">
                  <td className="px-3 py-1.5 font-mono">
                    {point.year}
                    {FAILURE_YEARS.includes(point.year) && (
                      <span className="ml-2 font-sans text-muted-foreground">
                        <span className="sr-only">, </span>
                        {t('crop failure year at Tribune')}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">{formatUsd(point.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  )
}
