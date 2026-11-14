// Types and loading of the files copied by scripts/sync-data.mjs.
// The types describe only the keys the app uses; they were confirmed in the real files.
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
  ndvi_bare_threshold: number
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

// One of the 46 study counties (data/processed/counties.geojson), with its centre point.
export type County = { fips: string; name: string; lon: number; lat: number }

export type AppData = {
  fields: FieldFeature[]
  countyNames: Record<string, string>
  counties: County[]
  manifest: Manifest
}

// URL of a file in the static folder, independent of the path the app is served from.
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
    getJson<{ features: { properties: { county_fips: string; name: string; lon: number; lat: number } }[] }>('counties.geojson'),
    getJson<Manifest>('manifest.json'),
  ])
  const countyNames: Record<string, string> = {}
  for (const county of counties.features) {
    countyNames[county.properties.county_fips] = county.properties.name
  }
  const countyList: County[] = counties.features.map(({ properties }) => ({
    fips: properties.county_fips,
    name: properties.name,
    lon: properties.lon,
    lat: properties.lat,
  }))
  return { fields: fields.features, countyNames, counties: countyList, manifest }
}

export type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: AppData }

// Data shared by all views, loaded once at start.
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

// Short field name for the bar and the list: "ks071-001" at Tribune -> "Tribune 001".
// The number alone is not enough, because 001 exists at three sites.
export function fieldShortName(properties: Pick<FieldProperties, 'field_id' | 'site'>) {
  const number = properties.field_id.split('-')[1] ?? properties.field_id
  return `${properties.site} ${number}`
}
