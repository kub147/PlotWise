// County layer of the study area: 46 western Kansas counties, what farmers grow on 31,660 fields
// (workstream B) and what the engine replays per county (workstream D).
// Types cover only the keys the app uses; confirmed in the real files.
import type { FeatureCollection, Polygon } from 'geojson'
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'
import type { Scenario } from '@/lib/results'

export type CountyProperties = {
  county_id: string
  name: string
  fallow_share_2008: number
  fallow_share_latest: number
}

export type CountyCollection = FeatureCollection<Polygon, CountyProperties>

// Rotation classes read from the 2018-2025 crop sequence of each field (pipelines/fields/county_rotations.py).
export const ROTATION_CLASSES = ['W-F', 'W-S-F', 'W-C-F', 'W-F to 3-year', 'no fallow', 'other with fallow'] as const
export type RotationClass = (typeof ROTATION_CLASSES)[number]

export const ROTATION_CLASS_STYLE: Record<RotationClass, { label: string; color: string }> = {
  'W-F': { label: 'Wheat – fallow', color: '#f2c94c' },
  'W-S-F': { label: 'Wheat – sorghum – fallow', color: '#8f2f1b' },
  'W-C-F': { label: 'Wheat – corn – fallow', color: '#2a8a57' },
  'W-F to 3-year': { label: 'Moved from wheat – fallow to a 3-year rotation', color: '#b5179e' },
  'no fallow': { label: 'No fallow at all', color: '#1479a8' },
  'other with fallow': { label: 'Other pattern with fallow', color: '#7f8a96' },
}

export type FieldRotations = {
  years: string
  note: string
  fields: number
  area_ha: number
  share_of_area: Record<RotationClass, number>
  counties: Record<
    string,
    {
      fields: number
      area_ha: number
      rotations: Record<RotationClass, { fields: number; share_of_area: number }>
    }
  >
}

type CountyModel = {
  best_rotation: string
  gain_replacing_fallow_usd_acre: number
  // Average net return per acre a year after land rent, per rotation id (WF, WSF, ...).
  rotations: Record<string, { mean: number }>
}

export type CountyResult = CountyModel & {
  budget_region: string
  precip_mm_per_year: number
  well_managed?: CountyModel
  practice?: { most_common_of_three: string | null; share_of_area: Record<string, number> }
}

export type CountyResults = {
  caution: string
  counties: Record<string, CountyResult>
}

export type CountyFieldCollection = FeatureCollection<
  Polygon,
  { county_id: string; rotation: RotationClass; sequence: string; area_ha: number }
>

export type RegionData = {
  counties: CountyCollection
  rotations: FieldRotations
  results: CountyResults
}

export type RegionState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: RegionData }

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(dataUrl(path))
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`)
  return (await response.json()) as T
}

// Loaded when the Region page opens, not at start-up: the other pages do not need these files.
export function useRegionData(): RegionState {
  const [state, setState] = useState<RegionState>({ status: 'loading' })
  useEffect(() => {
    let cancelled = false
    Promise.all([
      getJson<CountyCollection>('counties.geojson'),
      getJson<FieldRotations>('county_field_rotations.json'),
      getJson<CountyResults>('county_results.json'),
    ])
      .then(([counties, rotations, results]) => {
        if (!cancelled) setState({ status: 'ready', data: { counties, rotations, results } })
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

// Field outlines of the three demo counties (about 2 MB). null while loading or when the file is missing:
// the county map works without them.
export function useCountyFields(): CountyFieldCollection | null {
  const [fields, setFields] = useState<CountyFieldCollection | null>(null)
  useEffect(() => {
    let cancelled = false
    getJson<CountyFieldCollection>('county_fields.geojson')
      .then((collection) => {
        if (!cancelled) setFields(collection)
      })
      .catch(() => {
        // Optional layer: the page says outlines are unavailable instead of failing.
      })
    return () => {
      cancelled = true
    }
  }, [])
  return fields
}

// The model's numbers of a county at the chosen yield level.
export function countyModel(result: CountyResult | undefined, scenario: Scenario): CountyModel | undefined {
  if (!result) return undefined
  return scenario === 'well_managed' ? result.well_managed : result
}

// --- Map layers -------------------------------------------------------------------------------

export type RegionLayer = 'fallow' | 'left' | 'model'

export type LegendClass = { color: string; label: string }

// Share of cropland in fallow today, 5 classes (sequential, light to dark).
const FALLOW_STEPS = [0.05, 0.1, 0.2, 0.3]
const SEQUENTIAL = ['#e6f2f4', '#b3d9df', '#77b9c6', '#3690a2', '#0b5c6d']

// Percentage points of fallow given up since 2008; a rise gets its own neutral class.
const LEFT_STEPS = [0, 0.05, 0.1]
const LEFT_COLORS = ['#c9ced3', '#b3d9df', '#77b9c6', '#3690a2', '#0b5c6d']

// Model's gain of wheat-sorghum-fallow over wheat-fallow, USD/acre/yr (diverging around zero).
const GAIN_STEPS = [-15, 0, 15, 40]
const DIVERGING = ['#c65a1e', '#efc19f', '#a9d3e6', '#4a9cc7', '#145f85']

const NO_DATA = '#eef0f2'

function classIndex(value: number, steps: number[]): number {
  let index = 0
  while (index < steps.length && value >= steps[index]) index += 1
  return index
}

export function countyColor(
  layer: RegionLayer,
  properties: CountyProperties,
  result: CountyResult | undefined,
  scenario: Scenario,
): string {
  if (layer === 'fallow') return SEQUENTIAL[classIndex(properties.fallow_share_latest, FALLOW_STEPS)]
  if (layer === 'left') {
    const drop = properties.fallow_share_2008 - properties.fallow_share_latest
    return drop < 0 ? LEFT_COLORS[0] : LEFT_COLORS[1 + classIndex(drop, LEFT_STEPS.slice(1))] ?? LEFT_COLORS[4]
  }
  const model = countyModel(result, scenario)
  return model ? DIVERGING[classIndex(model.gain_replacing_fallow_usd_acre, GAIN_STEPS)] : NO_DATA
}

export const LAYER_INFO: Record<RegionLayer, { title: string; source: string; legend: LegendClass[] }> = {
  fallow: {
    title: 'Share of cropland left fallow today',
    source: 'USDA Cropland Data Layer, latest year, cropland of the whole county.',
    legend: [
      { color: SEQUENTIAL[0], label: 'under 5%' },
      { color: SEQUENTIAL[1], label: '5–10%' },
      { color: SEQUENTIAL[2], label: '10–20%' },
      { color: SEQUENTIAL[3], label: '20–30%' },
      { color: SEQUENTIAL[4], label: '30% or more' },
    ],
  },
  left: {
    title: 'Fallow given up since 2008',
    source: 'USDA Cropland Data Layer, 2008 against the latest year, in points of cropland share.',
    legend: [
      { color: LEFT_COLORS[0], label: 'fallow grew' },
      { color: LEFT_COLORS[1], label: '0–5 points less' },
      { color: LEFT_COLORS[2], label: '5–10 points less' },
      { color: LEFT_COLORS[3], label: '10 or more points less' },
    ],
  },
  model: {
    title: 'Model: net return of sorghum in place of fallow, $/acre a year',
    source:
      'Model run for 1996–2025 at the county center: wheat – sorghum – fallow minus wheat – fallow.',
    legend: [
      { color: DIVERGING[0], label: 'wheat – fallow ahead by $15/acre or more' },
      { color: DIVERGING[1], label: 'wheat – fallow ahead by up to $15/acre' },
      { color: DIVERGING[2], label: 'wheat – sorghum – fallow ahead by up to $15/acre' },
      { color: DIVERGING[3], label: 'wheat – sorghum – fallow ahead by $15–40/acre' },
      { color: DIVERGING[4], label: 'wheat – sorghum – fallow ahead by $40/acre or more' },
    ],
  },
}
