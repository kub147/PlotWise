// Climate files (climate/<field_id>.json) and the county rotation summary.
// The types describe only the keys the app uses; confirmed in the real files.
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'
import type { Translate } from '@/lib/i18n'
import { formatNumber, mmToInches, type TempUnit } from '@/lib/units'

export type Trend = {
  indicator: string
  label: string
  unit: string
  source: string
  first_year: number
  last_year: number
  mean_first_half: number
  mean_second_half: number
  slope_per_decade: number
  mk_p: number
  // true when the Mann-Kendall test gives p < 0.05 (the rule is stored in the file as trend_rule).
  reliable: boolean
}

export type PrecipRow = {
  product: string
  own_period: [number, number]
  own_slope_mm_per_decade: number
  own_mk_p: number
}

export type Climate = {
  field_id: string
  trends: Trend[]
  // year -> measure -> value (same measure names as in trends)
  yearly: Record<string, Record<string, number>>
  precip_crosscheck: { windows: { annual: { rows: PrecipRow[] } } }
  grace: {
    period: [string, string]
    trend_cm_per_year: number
    total_change_cm: number
    reliable: boolean
    note: string
    series: { date: string; lwe_cm: number }[]
  }
  smap: {
    period: [string, string]
    latest: { date: string; value: number; percentile_for_calendar_date: number; n_years: number }
    note: string
  }
}

export type CountyRotations = {
  years: string
  note: string
  counties: Record<
    string,
    { name: string; fields: number; rotations: Record<string, { fields: number; share_of_area: number }> }
  >
}

export type JsonState<T> = { status: 'loading' } | { status: 'missing' } | { status: 'ready'; data: T }

// Fetched files are kept in memory: several views read the same data.
const jsonCache = new Map<string, Promise<unknown>>()

// Loads a JSON file from the data folder. `path` equal to null means the manifest has no such file.
export function useJson<T>(path: string | null): JsonState<T> {
  const [loaded, setLoaded] = useState<{ path: string; state: JsonState<T> } | null>(null)
  useEffect(() => {
    if (path === null) return
    let cancelled = false
    let request = jsonCache.get(path)
    if (!request) {
      request = fetch(dataUrl(path)).then((response) => {
        if (!response.ok) throw new Error(String(response.status))
        return response.json() as Promise<unknown>
      })
      jsonCache.set(path, request)
    }
    request
      .then((data) => {
        if (!cancelled) setLoaded({ path, state: { status: 'ready', data: data as T } })
      })
      .catch(() => {
        // A missing file is shown as missing data.
        if (!cancelled) setLoaded({ path, state: { status: 'missing' } })
      })
    return () => {
      cancelled = true
    }
  }, [path])

  if (path === null) return { status: 'missing' }
  return loaded?.path === path ? loaded.state : { status: 'loading' }
}

// How to show a measure to a farmer: a plain-language name and the conversion to US units.
// kind: 'gdd' degree days (°C·day -> °F·day), 'days' a count of days, 'doy' day of year (a date), 'mm' millimetres -> inches.
export type IndicatorKind = 'gdd' | 'days' | 'doy' | 'mm'

export const INDICATORS: Record<string, { title: string; kind: IndicatorKind }> = {
  gdd10_apr_oct: { title: 'Growing-season heat (growing degree days, April–October)', kind: 'gdd' },
  hot_days_35c: { title: 'Days at 95°F or hotter', kind: 'days' },
  last_spring_frost_doy: { title: 'Last spring frost', kind: 'doy' },
  first_fall_frost_doy: { title: 'First fall frost', kind: 'doy' },
  frost_free_days: { title: 'Frost-free season', kind: 'days' },
  precip_mm: { title: 'Rain and snow, whole year', kind: 'mm' },
  precip_apr_sep_mm: { title: 'Rain, April–September', kind: 'mm' },
  heavy_rain_days_25mm: { title: 'Days with an inch of rain or more', kind: 'days' },
  eto_mm: { title: 'Thirst of the air, whole year (reference evapotranspiration)', kind: 'mm' },
  eto_apr_sep_mm: { title: 'Thirst of the air, April–September (reference evapotranspiration)', kind: 'mm' },
  balance_apr_sep_mm: { title: 'Rain minus thirst of the air, April–September', kind: 'mm' },
  longest_dry_spell_apr_sep: { title: 'Longest dry spell, April–September', kind: 'days' },
}

const number = (value: number, digits: number) => formatNumber(value, digits)

// Day of year -> "Oct 20" (a non-leap year as the pattern).
export function dayOfYearLabel(doy: number, locale: string) {
  const date = new Date(Date.UTC(2001, 0, Math.round(doy)))
  return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', timeZone: 'UTC' })
}

// Value of a measure in US units, for axes and tooltips.
// Degree days are in °F·days in English and °C·days in Polish (unit from useTempUnit).
export function indicatorValue(kind: IndicatorKind, value: number, t: Translate, locale: string, unit: TempUnit = 'F'): string {
  if (kind === 'gdd') {
    return unit === 'F'
      ? t('{n} degree days (base 50°F)', { n: number(value * 1.8, 0) })
      : t('{n} degree days (base 10°C)', { n: number(value, 0) })
  }
  if (kind === 'doy') return dayOfYearLabel(value, locale)
  if (kind === 'mm') return t('{n} in', { n: number(mmToInches(value), 1) })
  return t('{n} days', { n: number(value, 0) })
}

// Change per decade in words: "+138 °F·days per decade", "4.6 days later per decade".
// Sign taken after rounding, so a tiny negative slope shows as "0.0", never "−0.0".
const signedNumber = (value: number, digits: number) => {
  const rounded = Number(value.toFixed(digits)) || 0
  return `${rounded > 0 ? '+' : rounded < 0 ? '−' : ''}${number(Math.abs(rounded), digits)}`
}

export function slopeText(kind: IndicatorKind, slope: number, t: Translate, unit: TempUnit = 'F'): string {
  const size = Math.abs(slope)
  if (kind === 'gdd') {
    return unit === 'F'
      ? t('{n} degree days (base 50°F) per decade', { n: signedNumber(slope * 1.8, 0) })
      : t('{n} degree days (base 10°C) per decade', { n: signedNumber(slope, 0) })
  }
  if (kind === 'doy') {
    return slope >= 0
      ? t('{n} days later per decade', { n: number(size, 1) })
      : t('{n} days earlier per decade', { n: number(size, 1) })
  }
  if (kind === 'mm') return t('{n} in per decade', { n: signedNumber(mmToInches(slope), 1) })
  return t('{n} days per decade', { n: signedNumber(slope, 1) })
}
