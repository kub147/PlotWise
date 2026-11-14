// Engine results (results/<field_id>.json) and the ranking computed in the browser.
// Keys confirmed in the real files; only the ones the app uses are typed.
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'

// The four criteria scored by the engine (engine/scoring.py), in slider order.
export const CRITERIA = ['income', 'dry_year_safety', 'water', 'soil'] as const
export type Criterion = (typeof CRITERIA)[number]
export type Weights = Record<Criterion, number>

// Starting weights, same ratio as engine/scoring.py DEFAULT_WEIGHTS (2:2:1:1). Water and soil both rise with how
// often a crop is grown (the two indicators correlate 0.95), so together they start at the weight of one money priority.
export const DEFAULT_WEIGHTS: Weights = { income: 50, dry_year_safety: 50, water: 25, soil: 25 }

export type RotationResult = {
  id: string
  name: string
  phases: string[]
  status: string
  is_current: boolean
  mean_yield_kg_ha: Record<string, number>
  // Pairs [year, USD/acre]; values are already in 2025 dollars per acre.
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

export type RankingSensitivity = {
  weight_sets_tested: number
  share_of_wins: Record<string, number>
  most_often_first: string
  stable: boolean
}

// Yield level the replay is shown at (engine/counties.py SCENARIOS).
// county_average: mean dryland yield of the county. well_managed: planning yield of the K-State budget whose costs are used.
export const SCENARIOS = ['county_average', 'well_managed'] as const
export type Scenario = (typeof SCENARIOS)[number]

// The numbers of one rotation that change with the yield scenario.
type ScenarioRotation = Pick<
  RotationResult,
  'id' | 'mean_yield_kg_ha' | 'net_return_usd_acre' | 'summary' | 'indicators' | 'scores'
>

export type FieldResults = {
  field_id: string
  site?: string
  cost_region?: string
  period: [number, number]
  current_rotation: string | null
  dry_years: number[]
  rotations: RotationResult[]
  ranking_sensitivity: RankingSensitivity
  // Older result files have no second scenario.
  yield_scenarios?: {
    well_managed?: {
      rotations: ScenarioRotation[]
      ranking_sensitivity: RankingSensitivity
    }
  }
}

export function hasScenario(results: FieldResults, scenario: Scenario): boolean {
  return scenario === 'county_average' || results.yield_scenarios?.well_managed !== undefined
}

// Rotations and ranking sensitivity at the chosen yield level.
// The texts (why, evidence, risks) stay the same; only the numbers are swapped in.
export function scenarioView(
  results: FieldResults,
  scenario: Scenario,
): { rotations: RotationResult[]; sensitivity: RankingSensitivity } {
  const other = scenario === 'well_managed' ? results.yield_scenarios?.well_managed : undefined
  if (!other) return { rotations: results.rotations, sensitivity: results.ranking_sensitivity }
  const byId = new Map(other.rotations.map((rotation) => [rotation.id, rotation]))
  return {
    rotations: results.rotations.map((rotation) => ({ ...rotation, ...byId.get(rotation.id) })),
    sensitivity: other.ranking_sensitivity,
  }
}

export type ResultsState =
  | { status: 'loading' }
  | { status: 'missing' }
  | { status: 'error'; message: string }
  | { status: 'ready'; results: FieldResults }

// Loads the results of one field. `available` comes from the manifest: without results we do not fetch.
export function useFieldResults(fieldId: string, available: boolean): ResultsState {
  // The result is kept with its field id so that old numbers never show after the field changes.
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

// Fit of a rotation to the priorities: weighted mean of the four 0–1 scores.
// When all weights are zero they count as equal (spec 5.3).
export function fitScore(scores: Record<Criterion, number>, weights: Weights): number {
  const total = CRITERIA.reduce((sum, criterion) => sum + weights[criterion], 0)
  if (total === 0) {
    return CRITERIA.reduce((sum, criterion) => sum + scores[criterion], 0) / CRITERIA.length
  }
  return CRITERIA.reduce((sum, criterion) => sum + weights[criterion] * scores[criterion], 0) / total
}

export type RankedRotation = { rotation: RotationResult; fit: number; place: number }

// Ranking from the best fit down. Fits are compared to four decimals and ties keep the order of the file,
// the same rule as engine/scoring.py rank, so rounding noise never reorders two equal rotations.
export function rankRotations(rotations: RotationResult[], weights: Weights): RankedRotation[] {
  const key = (fit: number) => Math.round(fit * 1e4)
  return rotations
    .map((rotation, index) => ({ rotation, fit: fitScore(rotation.scores, weights), index }))
    .sort((a, b) => key(b.fit) - key(a.fit) || a.index - b.index)
    .map(({ rotation, fit }, i) => ({ rotation, fit, place: i + 1 }))
}
