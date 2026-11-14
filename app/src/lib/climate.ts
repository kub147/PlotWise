// Pliki klimatu (climate/<field_id>.json) i podsumowanie płodozmianów w hrabstwach.
// Typy opisują tylko klucze używane w aplikacji; potwierdzone w prawdziwych plikach.
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'
import { mmToInches } from '@/lib/units'

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
  // true, gdy test Manna-Kendalla daje p < 0.05 (reguła zapisana w pliku jako trend_rule).
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
  // rok -> wskaźnik -> wartość (te same nazwy wskaźników co w trends)
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

// Pobrane pliki trzymamy w pamięci: te same dane czyta kilka widoków.
const jsonCache = new Map<string, Promise<unknown>>()

// Wczytuje plik JSON z public data. `path` równe null oznacza, że pliku nie ma w manifeście.
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
        // Brak pliku pokazujemy jako brak danych.
        if (!cancelled) setLoaded({ path, state: { status: 'missing' } })
      })
    return () => {
      cancelled = true
    }
  }, [path])

  if (path === null) return { status: 'missing' }
  return loaded?.path === path ? loaded.state : { status: 'loading' }
}

// Jak pokazać wskaźnik farmerowi: nazwa prostym językiem i przeliczenie na jednostki amerykańskie.
// kind: 'gdd' stopniodni (°C·dzień -> °F·dzień), 'days' liczba dni, 'doy' dzień roku (data), 'mm' milimetry -> cale.
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

const number = (value: number, digits: number) =>
  value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })

// Dzień roku -> "Oct 20" (rok nieprzestępny jako wzorzec).
export function dayOfYearLabel(doy: number) {
  const date = new Date(Date.UTC(2001, 0, Math.round(doy)))
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
}

// Wartość wskaźnika w jednostkach amerykańskich, do osi i podpowiedzi.
export function indicatorValue(kind: IndicatorKind, value: number): string {
  if (kind === 'gdd') return `${number(value * 1.8, 0)} °F·days`
  if (kind === 'doy') return dayOfYearLabel(value)
  if (kind === 'mm') return `${number(mmToInches(value), 1)} in`
  return `${number(value, 0)} days`
}

// Zmiana na dekadę słowami: "+138 °F·days per decade", "4.6 days later per decade".
export function slopeText(kind: IndicatorKind, slope: number): string {
  const sign = slope > 0 ? '+' : slope < 0 ? '−' : ''
  const size = Math.abs(slope)
  if (kind === 'gdd') return `${sign}${number(size * 1.8, 0)} °F·days per decade`
  if (kind === 'doy') return `${number(size, 1)} days ${slope >= 0 ? 'later' : 'earlier'} per decade`
  if (kind === 'mm') return `${sign}${number(mmToInches(size), 1)} in per decade`
  return `${sign}${number(size, 1)} days per decade`
}
