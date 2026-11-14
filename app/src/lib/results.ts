// Wyniki silnika (results/<field_id>.json) i ranking liczony w przeglądarce.
// Klucze potwierdzone w prawdziwych plikach; opisane są tylko te, których aplikacja używa.
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'

// Cztery kryteria, które liczy silnik (engine/scoring.py), w kolejności suwaków.
export const CRITERIA = ['income', 'dry_year_safety', 'water', 'soil'] as const
export type Criterion = (typeof CRITERIA)[number]
export type Weights = Record<Criterion, number>

export const EQUAL_WEIGHTS: Weights = { income: 50, dry_year_safety: 50, water: 50, soil: 50 }

export type RotationResult = {
  id: string
  name: string
  phases: string[]
  status: string
  is_current: boolean
  mean_yield_kg_ha: Record<string, number>
  // Pary [rok, USD/akr]; wartości są już w dolarach z 2025 r. na akr.
  net_return_usd_acre: [number, number][]
  summary: {
    mean: number
    worst: number
    worst_year: number
    share_of_years_with_loss: number
    mean_in_dry_years: number
  }
  indicators: {
    bare_days_per_year: number
    crops_per_year: number
    crop_water_share: number
  }
  scores: Record<Criterion, number>
  why: string
  benefits: string[]
  risks: string[]
  evidence: string[]
  gaps: string[]
  check_locally: string[]
}

export type FieldResults = {
  field_id: string
  period: [number, number]
  current_rotation: string | null
  dry_years: number[]
  rotations: RotationResult[]
  ranking_sensitivity: {
    weight_sets_tested: number
    share_of_wins: Record<string, number>
    most_often_first: string
    stable: boolean
  }
}

export type ResultsState =
  | { status: 'loading' }
  | { status: 'missing' }
  | { status: 'error'; message: string }
  | { status: 'ready'; results: FieldResults }

// Wczytuje wyniki jednego pola. `available` pochodzi z manifestu: bez wyników nie próbujemy pobierać.
export function useFieldResults(fieldId: string, available: boolean): ResultsState {
  // Wynik pamiętamy razem z identyfikatorem pola, żeby po zmianie pola nie pokazać starych liczb.
  const [loaded, setLoaded] = useState<{ fieldId: string; state: ResultsState } | null>(null)
  useEffect(() => {
    if (!available) return
    let cancelled = false
    fetch(dataUrl(`results/${fieldId}.json`))
      .then((response) => {
        if (!response.ok) throw new Error(`Could not load results (${response.status})`)
        return response.json() as Promise<FieldResults>
      })
      .then((results) => {
        if (!cancelled) setLoaded({ fieldId, state: { status: 'ready', results } })
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : String(error)
        if (!cancelled) setLoaded({ fieldId, state: { status: 'error', message } })
      })
    return () => {
      cancelled = true
    }
  }, [fieldId, available])

  if (!available) return { status: 'missing' }
  return loaded?.fieldId === fieldId ? loaded.state : { status: 'loading' }
}

// Dopasowanie płodozmianu do priorytetów: średnia ważona czterech wyników 0–1.
// Gdy wszystkie wagi są zerowe, traktujemy je jak równe (specyfikacja 5.3).
export function fitScore(scores: Record<Criterion, number>, weights: Weights): number {
  const total = CRITERIA.reduce((sum, criterion) => sum + weights[criterion], 0)
  if (total === 0) {
    return CRITERIA.reduce((sum, criterion) => sum + scores[criterion], 0) / CRITERIA.length
  }
  return CRITERIA.reduce((sum, criterion) => sum + weights[criterion] * scores[criterion], 0) / total
}

export type RankedRotation = { rotation: RotationResult; fit: number; place: number }

// Ranking od najlepszego dopasowania. Przy remisie zostaje kolejność z pliku.
export function rankRotations(rotations: RotationResult[], weights: Weights): RankedRotation[] {
  return rotations
    .map((rotation, index) => ({ rotation, fit: fitScore(rotation.scores, weights), index }))
    .sort((a, b) => b.fit - a.fit || a.index - b.index)
    .map(({ rotation, fit }, i) => ({ rotation, fit, place: i + 1 }))
}
