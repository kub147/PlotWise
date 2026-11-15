// Data for the field card: greenness series (Landsat NDVI) and surface temperature scenes (ECOSTRESS).
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'

// URL of an image copied from docs/img by sync-data.
export function imageUrl(fileName: string) {
  return `${import.meta.env.BASE_URL}img/${fileName}`
}

export type NdviPoint = { time: number; ndvi: number }

// The CSV file has the columns: date,ndvi,sensor.
export function parseNdviCsv(csv: string): NdviPoint[] {
  const points: NdviPoint[] = []
  for (const line of csv.trim().split(/\r?\n/).slice(1)) {
    const [date, value] = line.split(',')
    const time = Date.parse(`${date}T00:00:00Z`)
    const ndvi = Number(value)
    if (!Number.isNaN(time) && !Number.isNaN(ndvi)) points.push({ time, ndvi })
  }
  return points
}

export type NdviState = { status: 'loading' } | { status: 'missing' } | { status: 'ready'; points: NdviPoint[] }

export function useNdvi(fieldId: string, available: boolean): NdviState {
  // The series is kept with its field id so that an old one never shows after the field changes.
  const [loaded, setLoaded] = useState<{ fieldId: string; state: NdviState } | null>(null)
  useEffect(() => {
    if (!available) return
    let cancelled = false
    fetch(dataUrl(`ndvi/${fieldId}.csv`))
      .then((response) => {
        if (!response.ok) throw new Error(String(response.status))
        return response.text()
      })
      .then((csv) => {
        if (!cancelled) setLoaded({ fieldId, state: { status: 'ready', points: parseNdviCsv(csv) } })
      })
      .catch(() => {
        // A missing file is shown as missing data; nothing is put in its place.
        if (!cancelled) setLoaded({ fieldId, state: { status: 'missing' } })
      })
    return () => {
      cancelled = true
    }
  }, [fieldId, available])

  if (!available) return { status: 'missing' }
  return loaded?.fieldId === fieldId ? loaded.state : { status: 'loading' }
}

// West, south, east, north in degrees: the area an image covers, so the map can lay it over the base map.
export type ImageBounds = [number, number, number, number]

// One ECOSTRESS scene: one moment, surface temperature (not air temperature) in °C, around one of the three sites.
export type HeatScene = {
  scene: string
  site: string
  time_utc: string
  local_solar_time: string
  fields: Record<string, { lst_c: number; crop: string }>
  by_crop_class: Record<string, { mean_c: number; pixels: number }>
  image: string
  colour_scale_c: [number, number]
  bounds: ImageBounds
}

export type HeatSummary = { source: string; note: string; scenes: HeatScene[] }

// Scenes that contain a field, newest first.
export function heatScenesFor(heat: HeatSummary | null, fieldId: string): HeatScene[] {
  return (heat?.scenes ?? [])
    .filter((scene) => fieldId in scene.fields)
    .sort((a, b) => b.time_utc.localeCompare(a.time_utc))
}

// The newest scene of every site: the image the map shows on its surface heat layer.
export function latestHeatScenes(heat: HeatSummary | null): HeatScene[] {
  const bySite = new Map<string, HeatScene>()
  for (const scene of heat?.scenes ?? []) {
    const current = bySite.get(scene.site)
    if (!current || scene.time_utc > current.time_utc) bySite.set(scene.site, scene)
  }
  return [...bySite.values()]
}

// The colours of the heat images (pipelines/fields/heat_stress.py): blue is cool, red is hot.
export const HEAT_SCALE = 'linear-gradient(to right, #313695, #74add1, #e0f3f8, #fee090, #f46d43, #a50026)'

// "2023-07-30 20:08" -> "Jul 30, 2023"
export function sceneDate(scene: HeatScene, locale: string) {
  const date = new Date(`${scene.time_utc.slice(0, 10)}T00:00:00Z`)
  return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' })
}

// "13:20" -> "1:20 pm" in English; Polish keeps the 24-hour clock.
export function clockTime(time: string, locale: string) {
  if (locale === 'pl-PL') return time
  const [hour, minute] = time.split(':').map(Number)
  return `${((hour + 11) % 12) + 1}:${String(minute).padStart(2, '0')} ${hour < 12 ? 'am' : 'pm'}`
}

// The three views of a field from above (tiles in the field card, tabs of the popup).
export type ViewerTab = 'aerial' | 'greenness' | 'heat'

export const VIEWER_TAB_LABEL: Record<ViewerTab, string> = {
  aerial: 'Aerial photo',
  greenness: 'Greenness',
  heat: 'Surface heat',
}

// Labels of the popup's tabs. Same words in English; Polish gets one short word each so that all three tabs
// fit on a phone (the "(tab)" keys are resolved in lib/i18n.ts and lib/pl.ts).
export const VIEWER_TAB_SHORT: Record<ViewerTab, string> = {
  aerial: 'Aerial photo (tab)',
  greenness: 'Greenness (tab)',
  heat: 'Surface heat (tab)',
}

// The file is shared by all fields, so it is fetched once.
let heatCache: Promise<HeatSummary | null> | null = null

export function useHeatSummary(): HeatSummary | null {
  const [summary, setSummary] = useState<HeatSummary | null>(null)
  useEffect(() => {
    let cancelled = false
    heatCache ??= fetch(dataUrl('ecostress_summary.json'))
      .then((response) => (response.ok ? (response.json() as Promise<HeatSummary>) : null))
      .catch(() => null)
    void heatCache.then((loaded) => {
      if (!cancelled) setSummary(loaded)
    })
    return () => {
      cancelled = true
    }
  }, [])
  return summary
}

// Mean summer greenness around each site (pipelines/fields/greenness_map.py): one image per site for the map.
export type GreennessMap = {
  years: [number, number]
  colour_scale_ndvi: [number, number]
  palette: string[]
  sites: { site: string; image: string; bounds: ImageBounds }[]
}

let greennessCache: Promise<GreennessMap | null> | null = null

export function useGreennessMap(): GreennessMap | null {
  const [map, setMap] = useState<GreennessMap | null>(null)
  useEffect(() => {
    let cancelled = false
    greennessCache ??= fetch(dataUrl('ndvi_summer_map.json'))
      .then((response) => (response.ok ? (response.json() as Promise<GreennessMap>) : null))
      .catch(() => null)
    void greennessCache.then((loaded) => {
      if (!cancelled) setMap(loaded)
    })
    return () => {
      cancelled = true
    }
  }, [])
  return map
}
