// "How we know": measured yield at the K-State Tribune trials against the engine, year by year, for one series.
// Two series, so identity never rests on colour alone: measured is a solid dark line with round points,
// the engine a dashed blue line with square points, and a legend names both.
// Years in which the trials harvested nothing are shaded and labelled, as on the "Year by year" chart.
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useT } from '@/lib/i18n'
import { CROP_WORD, CROP_WORD_GENITIVE, percent, yearList, type ValidationSeries } from '@/lib/validation'

type Point = { year: number; measured: number; engine: number }

const MEASURED_COLOR = 'var(--foreground)'
const ENGINE_COLOR = 'var(--chart-gain)'

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
  const t = useT()
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="pw-glass rounded-2xl px-3.5 py-2.5 text-[13px]">
      <p className="font-mono font-semibold">{point.year}</p>
      <p>
        {t('Measured')} <span className="font-mono font-semibold">{Math.round(point.measured)}</span> {t('bu/acre')}
      </p>
      <p>
        {t('Engine')} <span className="font-mono font-semibold">{Math.round(point.engine)}</span> {t('bu/acre')}
      </p>
      {point.measured === 0 && <p className="text-muted-foreground">{t('The trial harvested nothing')}</p>}
    </div>
  )
}

// Square point for the engine line (recharts passes the centre of the point).
function SquareDot({ cx, cy }: { cx?: number; cy?: number }) {
  if (cx === undefined || cy === undefined) return null
  return <rect x={cx - 3} y={cy - 3} width={6} height={6} fill={ENGINE_COLOR} stroke="var(--card)" strokeWidth={1} />
}

type ValidationChartProps = {
  series: ValidationSeries
  // Years in which the trial harvested nothing for this series.
  zeroYears: number[]
}

export function ValidationChart({ series, zeroYears }: ValidationChartProps) {
  const t = useT()
  const data: Point[] = series.years.map((year, i) => ({
    year,
    measured: series.measured_bu_acre[i],
    engine: series.modelled_bu_acre[i],
  }))
  const firstYear = series.years[0]
  const lastYear = series.years[series.years.length - 1]
  // A label every four years, starting on a year divisible by four (1996, 2000, …).
  const ticks: number[] = []
  for (let year = Math.ceil(firstYear / 4) * 4; year <= lastYear; year += 4) ticks.push(year)
  const crop = t(CROP_WORD[series.crop] ?? series.crop)
  const cropGenitive = t(CROP_WORD_GENITIVE[series.crop] ?? CROP_WORD[series.crop] ?? series.crop)
  // "Wheat after fallow (WSSF)" -> "Wheat after fallow"
  const title = t(series.label.replace(/\s*\(.*\)$/, ''))
  const headingId = `validation-${series.id}`

  return (
    <section aria-labelledby={headingId} className="pw-sheet rounded-[28px] p-4 lg:p-6">
      <h3 id={headingId} className="text-[19px] font-semibold leading-snug">
        {title}
      </h3>
      <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
        {t('Yield in bushels per acre, {from} to {to}. The engine follows {percent}% of the measured year-to-year swings.', {
          from: firstYear,
          to: lastYear,
          percent: percent(series.r2),
        })}
      </p>

      <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[13px]">
        <li className="flex items-center gap-2">
          <svg width="28" height="10" aria-hidden>
            <line x1="0" y1="5" x2="28" y2="5" stroke={MEASURED_COLOR} strokeWidth="2" />
            <circle cx="14" cy="5" r="3.5" fill={MEASURED_COLOR} />
          </svg>
          {t('Measured at the Tribune trials')}
        </li>
        <li className="flex items-center gap-2">
          <svg width="28" height="10" aria-hidden>
            <line x1="0" y1="5" x2="28" y2="5" stroke={ENGINE_COLOR} strokeWidth="2" strokeDasharray="5 4" />
            <rect x="11" y="2" width="6" height="6" fill={ENGINE_COLOR} />
          </svg>
          {t('Engine, from gridded weather')}
        </li>
      </ul>

      <div
        className="mt-2 h-[260px]"
        role="img"
        aria-label={t('Line chart of measured and modeled {crop} yield at Tribune, {from} to {to}. The table below has the same numbers.', {
          crop: cropGenitive,
          from: firstYear,
          to: lastYear,
        })}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 22, right: 10, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" />
            {zeroYears.map((year) => (
              <ReferenceArea
                key={year}
                x1={year - 0.5}
                x2={year + 0.5}
                fill="var(--muted-foreground)"
                fillOpacity={0.16}
                strokeOpacity={0}
                label={{ value: String(year), position: 'top', fontSize: 12, fontWeight: 600, fill: 'var(--foreground)' }}
              />
            ))}
            <XAxis
              dataKey="year"
              type="number"
              domain={[firstYear - 0.5, lastYear + 0.5]}
              ticks={ticks}
              tickLine={false}
              axisLine={{ stroke: 'var(--input)' }}
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <YAxis
              width={36}
              domain={[0, 'auto']}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--input)' }} />
            <Line
              dataKey="engine"
              type="linear"
              stroke={ENGINE_COLOR}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={<SquareDot />}
              activeDot={false}
              isAnimationActive={false}
            />
            <Line
              dataKey="measured"
              type="linear"
              stroke={MEASURED_COLOR}
              strokeWidth={2}
              dot={{ r: 3, fill: MEASURED_COLOR, stroke: 'var(--card)', strokeWidth: 1 }}
              activeDot={{ r: 5, stroke: 'var(--card)', strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {zeroYears.length > 0 && (
        <p className="mt-2 flex items-start gap-1.5 text-[13px] leading-snug text-muted-foreground">
          <span className="mt-0.5 h-3 w-3 shrink-0 rounded-sm bg-muted-foreground/25 ring-1 ring-inset ring-input" aria-hidden />
          {t('Shaded: {years}, when the trial lost the whole {crop} crop.', {
            years: yearList(zeroYears).replace(' and ', ` ${t('and')} `),
            crop: cropGenitive,
          })}
        </p>
      )}

      <details className="mt-1">
        <summary className="flex min-h-11 cursor-pointer items-center text-[15px] font-medium text-primary underline underline-offset-4">
          {t('Show the numbers as a table')}
        </summary>
        <div className="pw-scroll max-h-72 overflow-auto rounded-2xl bg-foreground/[0.03]">
          <table className="w-full text-left text-[13px]">
            <thead className="sticky top-0 bg-muted">
              <tr>
                <th scope="col" className="px-3 py-2 font-semibold">
                  {t('Year')}
                </th>
                <th scope="col" className="px-3 py-2 text-right font-semibold">
                  {t('Measured, bu/acre')}
                </th>
                <th scope="col" className="px-3 py-2 text-right font-semibold">
                  {t('Engine, bu/acre')}
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((point) => (
                <tr key={point.year} className="border-t border-border">
                  <td className="px-3 py-1.5 font-mono">{point.year}</td>
                  <td className="px-3 py-1.5 text-right font-mono">{Math.round(point.measured)}</td>
                  <td className="px-3 py-1.5 text-right font-mono">{Math.round(point.engine)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  )
}
