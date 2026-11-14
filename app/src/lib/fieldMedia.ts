// Dane do karty pola: seria zieloności (NDVI z Landsata) i sceny temperatury powierzchni (ECOSTRESS).
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'

// Adres obrazka skopiowanego z docs/img przez sync-data.
export function imageUrl(fileName: string) {
  return `${import.meta.env.BASE_URL}img/${fileName}`
}

export type NdviPoint = { time: number; ndvi: number }

// Plik CSV ma kolumny: date,ndvi,sensor.
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
  // Serię pamiętamy razem z identyfikatorem pola, żeby po zmianie pola nie pokazać starej.
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
        // Brak pliku pokazujemy jako brak danych, nie zastępujemy go niczym.
        if (!cancelled) setLoaded({ fieldId, state: { status: 'missing' } })
      })
    return () => {
      cancelled = true
    }
  }, [fieldId, available])

  if (!available) return { status: 'missing' }
  return loaded?.fieldId === fieldId ? loaded.state : { status: 'loading' }
}

// Jedna scena ECOSTRESS: jedno popołudnie, temperatura powierzchni (nie powietrza) w °C.
export type HeatScene = {
  scene: string
  time_utc: string
  local_solar_time: string
  fields: Record<string, { lst_c: number; crop: string }>
  by_crop_class: Record<string, { mean_c: number; pixels: number }>
  image: string
  colour_scale_c: [number, number]
}

export type HeatSummary = { source: string; note: string; scenes: HeatScene[] }

// Plik jest wspólny dla wszystkich pól, więc pobieramy go raz.
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
