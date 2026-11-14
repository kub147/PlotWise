// "Rotation replay" view: yield level switch, priority sliders, ranking, rotation card and yearly chart.
// The ranking is computed in the browser from the 0–1 scores written by the engine; the engine is not run here.
import { TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RankingList } from '@/components/replay/RankingList'
import { RotationCard } from '@/components/replay/RotationCard'
import { WeightSliders } from '@/components/replay/WeightSliders'
import { YearChart } from '@/components/replay/YearChart'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { useEvidence } from '@/lib/evidence'
import {
  EQUAL_WEIGHTS,
  hasScenario,
  rankRotations,
  scenarioView,
  useFieldResults,
  type RankingSensitivity,
  type Scenario,
  type Weights,
} from '@/lib/results'
import { rotationLabel } from '@/lib/rotation'
import { DEFAULT_FIELD_ID } from '@/lib/selection'

const SCENARIO_OPTIONS: { value: Scenario; label: string }[] = [
  { value: 'county_average', label: 'Average field in the county' },
  { value: 'well_managed', label: 'Well-managed field' },
]

const SCENARIO_TEXT: Record<Scenario, string> = {
  county_average:
    'Yields at the average of all dryland farms in the county (USDA NASS). The costs come from K-State budgets written for a well-managed field, so this level is hard on every crop and kind to fallow, the cheapest year.',
  well_managed:
    'Yields at the level the K-State budgets plan for, so costs and yields match. Pick this if your field usually does better than the county average.',
}

// Budget regions whose costs are proxies from wetter central Kansas (engine/README.md).
const PROXY_BUDGET_REGIONS = ['NC', 'SC']

// Sentence on how stable the ranking is, built from the field's data (ranking_sensitivity), not hard-coded.
function stabilitySentence(sensitivity: RankingSensitivity): string {
  const shares = Object.entries(sensitivity.share_of_wins)
    .filter(([, share]) => share > 0)
    .sort((a, b) => b[1] - a[1])
  const [first, second] = shares
  if (!first) return ''
  const label = (id: string) => rotationLabel(id) ?? id
  const percent = (share: number) => `${Math.round(share * 100)}%`
  if (sensitivity.stable || !second) {
    return `Across random priorities, ${label(first[0])} comes out on top about ${percent(first[1])} of the time. Different priorities can still change the order.`
  }
  return `It is a close call. Across random priorities, ${label(first[0])} comes out on top about ${percent(first[1])} of the time and ${label(second[0])} about ${percent(second[1])}. Your priorities decide.`
}

type ReplayProps = {
  data: AppData
  selected: FieldFeature
}

export function Replay({ data, selected }: ReplayProps) {
  const fieldId = selected.properties.field_id
  const state = useFieldResults(fieldId, data.manifest.results.includes(fieldId))
  const evidence = useEvidence()
  const [weights, setWeights] = useState<Weights>(EQUAL_WEIGHTS)
  const [chosenScenario, setScenario] = useState<Scenario>('county_average')
  // The chosen rotation is kept with its field: a new field goes back to the default choice.
  const [choice, setChoice] = useState<{ fieldId: string; rotationId: string } | null>(null)
  const rotationId = choice?.fieldId === fieldId ? choice.rotationId : null

  const results = state.status === 'ready' ? state.results : null
  // Older result files carry one yield level only; then the switch is hidden.
  const canSwitch = results !== null && hasScenario(results, 'well_managed')
  const scenario: Scenario = canSwitch ? chosenScenario : 'county_average'
  const view = useMemo(() => (results ? scenarioView(results, scenario) : null), [results, scenario])
  const ranked = useMemo(() => (view ? rankRotations(view.rotations, weights) : []), [view, weights])
  const allLose = ranked.every((entry) => entry.rotation.summary.mean < 0)

  // By default the field's current rotation is shown, or the first in the ranking when there is none.
  const shown =
    ranked.find((entry) => entry.rotation.id === rotationId) ??
    ranked.find((entry) => entry.rotation.is_current) ??
    ranked[0]

  return (
    <div className="mx-auto flex max-w-[1680px] flex-col gap-6 p-4 lg:p-6">
      <header>
        <h1 className="text-[34px] font-semibold leading-tight">Rotation replay</h1>
        <p className="mt-1 text-[15px] text-muted-foreground">
          {results
            ? `Every rotation replayed on ${fieldShortName(selected.properties)} through each year from ${results.period[0]} to ${results.period[1]}`
            : fieldShortName(selected.properties)}
        </p>
      </header>

      {/* Warning always visible at the top (spec 5.3) */}
      <p className="flex gap-3 rounded-3xl bg-warning px-5 py-4 text-[15px] leading-snug">
        <TriangleAlert aria-hidden className="mt-0.5 h-5 w-5 shrink-0 text-warning-border" />
        <span>
          <strong className="font-medium">Read this as a comparison, not as farm profit.</strong>{' '}
          {allLose ? 'Every rotation shows a loss on average because we' : 'The numbers are low because we'} count full
          costs including land rent, and leave out crop insurance and program payments.
        </span>
      </p>

      {canSwitch && (
        <section aria-labelledby="scenario-heading" className="pw-sheet rounded-3xl px-5 py-4">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <h2 id="scenario-heading" className="text-[15px] font-semibold">
              How does this field yield?
            </h2>
            <SegmentedControl
              options={SCENARIO_OPTIONS}
              label="Yield level used in the replay"
              value={scenario}
              onValueChange={setScenario}
            />
          </div>
          <p className="mt-2 max-w-[900px] text-[13px] leading-snug text-muted-foreground" aria-live="polite">
            {SCENARIO_TEXT[scenario]}
            {scenario === 'well_managed' &&
              PROXY_BUDGET_REGIONS.includes(results?.cost_region ?? '') &&
              ' For this county the budgets come from wetter central Kansas, so these numbers are probably optimistic.'}{' '}
            Neither level is a forecast.
          </p>
        </section>
      )}

      {state.status === 'loading' && <p className="text-muted-foreground">Loading the replay…</p>}
      {state.status === 'error' && <p role="alert">The replay could not be loaded. {state.message}</p>}
      {state.status === 'missing' && (
        <div className="pw-sheet rounded-[28px] p-6">
          <h2 className="text-[19px] font-semibold">The replay is not ready for this field yet</h2>
          <p className="mt-1 text-[15px] text-muted-foreground">
            The engine has not produced results for this field yet. Tribune 001 has the full replay.
          </p>
          <Link
            to={{ pathname: '/replay', search: `?field=${DEFAULT_FIELD_ID}` }}
            className="mt-2 inline-flex min-h-11 items-center text-[15px] font-semibold text-primary underline underline-offset-4"
          >
            Open the replay for Tribune 001
          </Link>
        </div>
      )}

      {results && view && shown && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:items-start xl:grid-cols-[280px_minmax(0,1fr)_420px]">
          {/* Three columns on a wide screen only; on a medium one the card drops below the ranking, on a phone one column */}
          <div className="min-w-0">
            <WeightSliders weights={weights} onChange={setWeights} />
          </div>

          <div className="flex min-w-0 flex-col gap-5">
            <section aria-labelledby="ranking-heading">
              <h2 id="ranking-heading" className="text-[19px] font-semibold">
                Rotations ranked by your priorities
              </h2>
              <p className="mb-3 mt-1 text-[13px] text-muted-foreground">
                Select a rotation to read why, the evidence and what to check.
                {results.current_rotation === null &&
                  ' This field has no fallow, which is not one of the modeled rotations, so none is marked as yours.'}
              </p>
              <RankingList ranked={ranked} selectedId={shown.rotation.id} onSelect={(id) => setChoice({ fieldId, rotationId: id })} />
              <p className="mt-3 text-[15px] leading-snug">{stabilitySentence(view.sensitivity)}</p>
            </section>

            <YearChart rotation={shown.rotation} site={results.site} />
          </div>

          <div className="min-w-0 lg:col-span-2 xl:col-span-1">
            <RotationCard
              rotation={shown.rotation}
              yearCount={shown.rotation.net_return_usd_acre.length}
              fieldId={fieldId}
              evidence={evidence}
            />
          </div>
        </div>
      )}
    </div>
  )
}
