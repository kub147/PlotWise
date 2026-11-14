// Typy i wczytywanie plików skopiowanych przez scripts/sync-data.mjs.
// Typy opisują tylko klucze, których aplikacja używa; zostały potwierdzone w prawdziwych plikach.
import { useEffect, useState } from 'react'

export type FieldProperties = {
  field_id: string
  name: string
  site: string
  county_fips: string
  area_ha: number
  lon: number
  lat: number
  crop_history_names: Record<string, string>
  crop_sequence: string
  crop_sequence_first_year: number
  current_rotation: string
  fallow_share: number
  slope_pct: number
  bare_days_per_year: number
  bare_days_note: string
  boundary_source: string
  awc_mm: number
  texture: string
  organic_matter_pct: number
  hydrologic_group: string
  soil_series: string
  soil_map_unit: string
  soil_source: string
}

export type FieldFeature = {
  type: 'Feature'
  properties: FieldProperties
  geometry: { type: 'Polygon'; coordinates: number[][][] }
}

export type Manifest = {
  climate: string[]
  results: string[]
  ndvi: string[]
  naip: string[]
  ecostress: string[]
}

export type AppData = {
  fields: FieldFeature[]
  countyNames: Record<string, string>
  manifest: Manifest
}

// Adres pliku w public/, niezależny od tego, pod jaką ścieżką stoi aplikacja.
export function dataUrl(path: string) {
  return `${import.meta.env.BASE_URL}data/${path}`
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(dataUrl(path))
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`)
  return (await response.json()) as T
}

async function loadAppData(): Promise<AppData> {
  const [fields, counties, manifest] = await Promise.all([
    getJson<{ features: FieldFeature[] }>('fields.geojson'),
    getJson<{ features: { properties: { county_fips: string; name: string } }[] }>('counties.geojson'),
    getJson<Manifest>('manifest.json'),
  ])
  const countyNames: Record<string, string> = {}
  for (const county of counties.features) {
    countyNames[county.properties.county_fips] = county.properties.name
  }
  return { fields: fields.features, countyNames, manifest }
}

export type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: AppData }

// Dane wspólne dla wszystkich widoków, wczytywane raz przy starcie.
export function useAppData(): LoadState {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  useEffect(() => {
    let cancelled = false
    loadAppData()
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: error instanceof Error ? error.message : String(error) })
      })
    return () => {
      cancelled = true
    }
  }, [])
  return state
}

// Krótka nazwa pola do paska i listy: "ks071-001" w Tribune -> "Tribune 001".
// Sam numer nie wystarcza, bo 001 występuje w trzech miejscowościach.
export function fieldShortName(properties: Pick<FieldProperties, 'field_id' | 'site'>) {
  const number = properties.field_id.split('-')[1] ?? properties.field_id
  return `${properties.site} ${number}`
}
