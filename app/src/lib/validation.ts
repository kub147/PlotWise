// Engine validation against the K-State Tribune trials (data/processed/results/validation.json,
// written by `python -m engine.validate`). Types cover only the keys the app uses; confirmed in the real file.

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

// 0.61 -> 61
export const percent = (share: number) => Math.round(share * 100)

// 2002, 2013 -> "2002 and 2013"
export function yearList(years: number[]): string {
  if (years.length <= 1) return years.join('')
  return `${years.slice(0, -1).join(', ')} and ${years[years.length - 1]}`
}

export type Tile = { title: string; text: string }

// The three tiles under the charts, written from the file so no number is copied by hand.
export function validationTiles(validation: Validation): Tile[] {
  const { grain_sorghum: sorghum, winter_wheat: wheat } = validation.headline
  // Headline to the nearest 5 ("about 60%"); the sentence gives the exact figure.
  const about = (share: number) => Math.round(share * 20) * 5
  const tiles: Tile[] = [
    {
      title: `Sorghum: about ${about(sorghum.explained)}%`,
      text: `Modeled water use explains about ${percent(sorghum.explained)}% of the year-to-year swings in sorghum yield measured at the K-State trials in Tribune. It is ${percent(sorghum.leave_one_out)}% when each year is predicted without the model having seen it.`,
    },
    {
      title: `Wheat: about ${about(wheat.explained)}%`,
      text: `With hot days counted, the model explains about ${percent(wheat.explained)}% of the swings in measured wheat yield. Predicting a year it has not seen, only about ${percent(wheat.leave_one_out)}%. Treat any single wheat year as a rough estimate.`,
    },
  ]
  const lost = validation.failures
    .filter((failure) => failure.measured_zero_years.length > 0)
    .map((failure) => `the whole ${CROP_WORD[failure.crop] ?? failure.crop} crop in ${yearList(failure.measured_zero_years)}`)
  if (lost.length > 0) {
    const allFound = validation.failures.every((failure) => failure.zero_years_are_model_lowest)
    const lowest = validation.failures
      .map(
        (failure) =>
          `${CROP_WORD[failure.crop] ?? failure.crop} ${yearList(failure.model_lowest_years.map(([year]) => year))}`,
      )
      .join('; ')
    // What the model gives in the years the trials harvested nothing (bu/acre).
    const inLostYears = validation.failures.flatMap((failure) =>
      failure.model_lowest_years
        .filter(([year]) => failure.measured_zero_years.includes(year))
        .map(([, yieldBu]) => Math.round(yieldBu)),
    )
    const milder =
      inLostYears.length > 0 && Math.max(...inLostYears) > 0
        ? ` It still gives ${Math.min(...inLostYears)} to ${Math.max(...inLostYears)} bu/acre in those years, where the trials harvested nothing, so the worst years in the replay are milder than the real ones.`
        : ''
    tiles.push({
      title: allFound ? 'It finds the failure years' : 'It misses some failure years',
      text: allFound
        ? `The trials lost ${lost.join(' and ')}. Those are the lowest years the model gives for each crop.${milder}`
        : `The trials lost ${lost.join(' and ')}. The model’s lowest years are: ${lowest}.${milder}`,
    })
  }
  return tiles
}
