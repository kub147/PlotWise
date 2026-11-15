// Engine validation against the K-State Tribune trials (data/processed/results/validation.json,
// written by `python -m engine.validate`). Types cover only the keys the app uses; confirmed in the real file.
import type { Translate } from '@/lib/i18n'

export type ValidationSeries = {
  id: string
  label: string
  crop: string
  n: number
  years: number[]
  measured_bu_acre: number[]
  modelled_bu_acre: number[]
  measured_mean: number
  modelled_mean: number
  // Squared correlation between the measured and the modelled series.
  r2: number
  rmse_bu_acre: number
}

// Share of the measured year-to-year variation explained, in sample and when the year was left out of the fit.
export type ValidationHeadline = { series: string; explained: number; leave_one_out: number }

export type ValidationFailure = {
  series: string
  crop: string
  measured_zero_years: number[]
  // [year, bu/acre], lowest first
  model_lowest_years: [number, number][]
  zero_years_are_model_lowest: boolean
}

export type Validation = {
  generated: string
  site: string
  period: [number, number]
  headline: { grain_sorghum: ValidationHeadline; winter_wheat: ValidationHeadline }
  series: ValidationSeries[]
  failures: ValidationFailure[]
}

// The two series the yield models were fitted on: each crop in its usual place in the rotation.
export const REFERENCE_SERIES = ['wheat_wssf', 'sorghum_wssf_first'] as const

export const CROP_WORD: Record<string, string> = { winter_wheat: 'wheat', grain_sorghum: 'sorghum' }
export const CROP_WORD_GENITIVE: Record<string, string> = {
  winter_wheat: 'wheat in genitive',
  grain_sorghum: 'sorghum in genitive',
}

// 0.61 -> 61
export const percent = (share: number) => Math.round(share * 100)

// 2002, 2013 -> "2002 and 2013"
export function yearList(years: number[]): string {
  if (years.length <= 1) return years.join('')
  return `${years.slice(0, -1).join(', ')} and ${years[years.length - 1]}`
}

export type Tile = { title: string; text: string }

// The three tiles under the charts, written from the file so no number is copied by hand.
export function validationTiles(validation: Validation, t: Translate): Tile[] {
  const { grain_sorghum: sorghum, winter_wheat: wheat } = validation.headline
  const years = (values: number[]) => yearList(values).replace(' and ', ` ${t('and')} `)
  const tiles: Tile[] = [
    {
      title: t('Sorghum: about {percent}%', { percent: percent(sorghum.explained) }),
      text: t('Modeled water use explains about {explained}% of the year-to-year swings in sorghum yield measured at the K-State trials in Tribune. It is {leave_one_out}% when each year is predicted without the model having seen it.', {
        explained: percent(sorghum.explained),
        leave_one_out: percent(sorghum.leave_one_out),
      }),
    },
    {
      title: t('Wheat: about {percent}%', { percent: percent(wheat.explained) }),
      text: t('With hot days counted, the model explains about {explained}% of the swings in measured wheat yield. Predicting a year it has not seen, only about {leave_one_out}%. Treat any single wheat year as a rough estimate.', {
        explained: percent(wheat.explained),
        leave_one_out: percent(wheat.leave_one_out),
      }),
    },
  ]
  const lost = validation.failures
    .filter((failure) => failure.measured_zero_years.length > 0)
    .map((failure) =>
      t('the whole {crop} crop in {years}', {
        crop: t(CROP_WORD_GENITIVE[failure.crop] ?? CROP_WORD[failure.crop] ?? failure.crop),
        years: years(failure.measured_zero_years),
      }),
    )
  if (lost.length > 0) {
    const allFound = validation.failures.every((failure) => failure.zero_years_are_model_lowest)
    const lowest = validation.failures
      .map(
        (failure) =>
          t('{crop} {years}', {
            crop: t(CROP_WORD[failure.crop] ?? failure.crop),
            years: years(failure.model_lowest_years.map(([year]) => year)),
          }),
      )
      .join('; ')
    // What the model gives in the years the trials harvested nothing (bu/acre), per crop: "wheat 5–10 and sorghum 28–38".
    const ranges = validation.failures
      .map((failure) => {
        const values = failure.model_lowest_years
          .filter(([year]) => failure.measured_zero_years.includes(year))
          .map(([, yieldBu]) => Math.round(yieldBu))
        if (values.length === 0 || Math.max(...values) <= 0) return ''
        const low = Math.min(...values)
        const high = Math.max(...values)
        return `${t(CROP_WORD[failure.crop] ?? failure.crop)} ${low === high ? low : `${low}–${high}`}`
      })
      .filter(Boolean)
    const milder =
      ranges.length > 0
        ? t('It still gives {ranges} bu/acre in those years, where the trials harvested nothing, so the worst years in the replay are milder than the real ones.', {
            ranges: ranges.join(` ${t('and')} `),
          })
        : ''
    tiles.push({
      title: t(allFound ? 'It finds the failure years' : 'It misses some failure years'),
      text: allFound
        ? t('The trials lost {lost}. Those are the lowest years the model gives for each crop.{milder}', {
            lost: lost.join(` ${t('and')} `),
            milder: milder ? ` ${milder}` : '',
          })
        : t("The trials lost {lost}. The model's lowest years are: {lowest}.{milder}", {
            lost: lost.join(` ${t('and')} `),
            lowest,
            milder: milder ? ` ${milder}` : '',
          }),
    })
  }
  return tiles
}
