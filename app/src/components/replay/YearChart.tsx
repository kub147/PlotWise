// Wykres „Year by year": zwrot netto na akr dla wybranego płodozmianu, rok po roku.
// Słupki od zera: niebieski = rok na plusie, pomarańczowy = rok na minusie (para sprawdzona pod kątem daltonizmu).
// Lata klęsk są zaznaczone szarym pasem i podpisem roku, nie samym kolorem.
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
import type { RotationResult } from '@/lib/results'
import { rotationDisplayName } from '@/lib/rotation'
import { formatUsd } from '@/lib/units'

// Lata, w których doświadczenia K-State w Tribune straciły cały plon:
// pszenica 2002 i 2013 (evidence.md, E01), sorgo 2002 i 2012 (E02).
const FAILURE_YEARS = [2002, 2012, 2013]

// Sąsiednie lata łączymy w jeden pas, żeby podpisy nie nachodziły na siebie: 2012 i 2013 -> "2012–13".
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
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-[13px] shadow-md">
      <p className="font-mono font-semibold">{point.year}</p>
      <p>
        <span className="font-mono font-semibold">{formatUsd(point.value)}</span> per acre
      </p>
      {FAILURE_YEARS.includes(point.year) && <p className="text-muted-foreground">Crop failure year at Tribune</p>}
    </div>
  )
}

export function YearChart({ rotation }: { rotation: RotationResult }) {
  const data: Point[] = rotation.net_return_usd_acre.map(([year, value]) => ({ year, value }))
  const firstYear = data[0]?.year
  const lastYear = data[data.length - 1]?.year
  const name = rotationDisplayName(rotation.name)

  return (
    <section aria-labelledby="year-chart-heading">
      <h2 id="year-chart-heading" className="text-[19px] font-semibold">
        Year by year
      </h2>
      <p className="mt-1 text-[13px] text-muted-foreground">
        {name}: return per acre in each year, {firstYear}–{lastYear}, in 2025 dollars. Hover or tap a bar for the
        number.
      </p>

      {/* Na wąskim ekranie wykres przewija się w poziomie zamiast się ściskać */}
      <div className="mt-3 overflow-x-auto rounded-lg border border-border bg-card p-3">
        <div className="h-[300px] min-w-[640px]" role="img" aria-label={`Bar chart of yearly net return per acre for ${name}. The table below has the same numbers.`}>
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
            <span className="h-3 w-3 rounded-sm bg-chart-gain" aria-hidden /> Year above zero
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-chart-loss" aria-hidden /> Year below zero
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-muted-foreground/25 ring-1 ring-inset ring-input" aria-hidden />
            Shaded: {FAILURE_YEARS.join(', ')}, years the Tribune field trials lost a whole crop
          </li>
        </ul>
      </div>

      <details className="mt-2">
        <summary className="flex min-h-11 cursor-pointer items-center text-[15px] font-medium text-primary underline underline-offset-4">
          Show the numbers as a table
        </summary>
        <div className="max-h-72 overflow-auto rounded-lg border border-border bg-card">
          <table className="w-full text-left text-[13px]">
            <thead className="sticky top-0 bg-muted">
              <tr>
                <th scope="col" className="px-3 py-2 font-semibold">
                  Year
                </th>
                <th scope="col" className="px-3 py-2 text-right font-semibold">
                  Return per acre
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((point) => (
                <tr key={point.year} className="border-t border-border">
                  <td className="px-3 py-1.5 font-mono">
                    {point.year}
                    {FAILURE_YEARS.includes(point.year) && (
                      <span className="ml-2 font-sans text-muted-foreground">crop failure year at Tribune</span>
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
