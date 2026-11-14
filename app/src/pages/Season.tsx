// "This season" view: where soil moisture stands today (NASA SMAP), as a percentile for this calendar date.
// The engine has no forward run yet, so this page states that plainly and gives no forecast or advice.
import { Droplets } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useJson, type Climate } from '@/lib/climate'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { useDateLocale, useT } from '@/lib/i18n'

// 96 -> "96th", 1 -> "1st", 22 -> "22nd"
function ordinal(value: number) {
  const tens = value % 100
  if (tens >= 11 && tens <= 13) return `${value}th`
  return `${value}${['th', 'st', 'nd', 'rd'][value % 10] ?? 'th'}`
}

function longDate(isoDate: string, locale: string) {
  return new Date(`${isoDate}T00:00:00Z`).toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  })
}

type SeasonProps = {
  data: AppData
  selected: FieldFeature
}

export function Season({ data, selected }: SeasonProps) {
  const t = useT()
  const locale = useDateLocale()
  const p = selected.properties
  const hasClimate = data.manifest.climate.includes(p.field_id)
  const state = useJson<Climate>(hasClimate ? `climate/${p.field_id}.json` : null)

  if (state.status === 'loading') {
    return <p className="p-6 text-muted-foreground">{t('Loading soil moisture…')}</p>
  }
  if (state.status === 'missing') {
    return (
      <div className="mx-auto max-w-[1680px] p-4 lg:p-6">
        <h1 className="text-[34px] font-semibold leading-tight">{t('This season')}</h1>
        <p className="mt-2 text-muted-foreground">{t('There is no soil moisture record for this field yet.')}</p>
      </div>
    )
  }

  const { latest, note, period } = state.data.smap
  const percentile = latest.percentile_for_calendar_date
  const firstYear = period[0].slice(0, 4)

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-6 p-4 lg:p-6">
      <header>
        <h1 className="text-[34px] font-semibold leading-tight">{t('This season')}</h1>
        <p className="mt-1 text-[15px] text-muted-foreground">
          {t('{field} · soil moisture on {date}', { field: fieldShortName(p), date: longDate(latest.date, locale) })}
        </p>
      </header>

      <Card className="p-6 lg:p-8">
        <div className="flex items-start gap-4">
          <span
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl"
            style={{ background: 'var(--tint-water)' }}
            aria-hidden
          >
            <Droplets className="h-6 w-6" />
          </span>
          <div>
            <p className="text-[64px] font-semibold leading-none tracking-tight">{ordinal(percentile)}</p>
            <p className="mt-1 text-[19px] font-medium">{t('percentile for this date')}</p>
          </div>
        </div>

        <p className="mt-5 max-w-[62ch] text-[15px] leading-snug">
          {t('The soil around this field is wetter than on {percentile}% of the same dates since {year}.', { percentile, year: firstYear })}
        </p>

        {/* Scale: the marker sits at the percentile; the ends are labelled in words */}
        <div className="mt-6">
          <div
            className="relative h-3 rounded-full bg-foreground/[0.08]"
            role="img"
            aria-label={t('Scale from driest on record to wettest on record. Today is at the {rank} percentile.', { rank: ordinal(percentile) })}
          >
            <span
              className="absolute top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-card pw-brand shadow-[0_4px_12px_rgb(15_154_76/0.35)]"
              style={{ left: `${percentile}%` }}
            />
          </div>
          <div className="mt-3 flex justify-between text-[13px] text-muted-foreground">
            <span>{t('Driest on record')}</span>
            <span>{t('Middle')}</span>
            <span>{t('Wettest on record')}</span>
          </div>
        </div>

        <p className="mt-6 max-w-[70ch] text-[13px] leading-snug text-muted-foreground">
          {t('From NASA’s SMAP satellite: moisture in the top 3 feet of soil, compared with the same week of the year in {years} years of record. It covers a square about 5.5 miles wide, so read it as the neighborhood, not as a probe in this field. Use the percentile, not the raw reading.', { years: latest.n_years })}
        </p>
      </Card>

      <Card className="p-6 lg:p-8">
        <h2 className="text-[22px] font-semibold leading-tight">{t('What it means for next season')}</h2>
        <p className="mt-3 max-w-[62ch] text-[17px] leading-snug">
          {t('We can show where the soil stands today. We cannot yet project the season from it.')}
        </p>
        <p className="mt-3 max-w-[70ch] text-[15px] leading-snug text-muted-foreground">
          {t('The replay runs each rotation through past years. It does not yet start from today’s soil moisture and run forward, so this page gives no yield range and no planting advice.')}
        </p>
      </Card>

      {/* Note stored in the data file by workstream A, shown unchanged */}
      <p className="px-2 text-[13px] leading-snug text-muted-foreground">{t('Note from the data:')} {t(note)}</p>
    </div>
  )
}
