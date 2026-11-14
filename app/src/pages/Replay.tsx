// Widok „Rotation replay": suwaki priorytetów, ranking, karta płodozmianu i wykres roczny.
// Ranking liczymy w przeglądarce z wyników 0–1 zapisanych przez silnik; silnika nie uruchamiamy.
import { TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RankingList } from '@/components/replay/RankingList'
import { RotationCard } from '@/components/replay/RotationCard'
import { WeightSliders } from '@/components/replay/WeightSliders'
import { YearChart } from '@/components/replay/YearChart'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { useEvidence } from '@/lib/evidence'
import { EQUAL_WEIGHTS, rankRotations, useFieldResults, type FieldResults, type Weights } from '@/lib/results'
import { rotationLabel } from '@/lib/rotation'
import { DEFAULT_FIELD_ID } from '@/lib/selection'

// Zdanie o stabilności rankingu, złożone z danych pola (ranking_sensitivity), nie wpisane na stałe.
function stabilitySentence(results: FieldResults): string {
  const shares = Object.entries(results.ranking_sensitivity.share_of_wins)
    .filter(([, share]) => share > 0)
    .sort((a, b) => b[1] - a[1])
  const [first, second] = shares
  if (!first) return ''
  const label = (id: string) => rotationLabel(id) ?? id
  const percent = (share: number) => `${Math.round(share * 100)}%`
  if (results.ranking_sensitivity.stable || !second) {
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
  // Wybór płodozmianu pamiętamy razem z polem: po zmianie pola wraca wybór domyślny.
  const [choice, setChoice] = useState<{ fieldId: string; rotationId: string } | null>(null)
  const rotationId = choice?.fieldId === fieldId ? choice.rotationId : null

  const results = state.status === 'ready' ? state.results : null
  const ranked = useMemo(() => (results ? rankRotations(results.rotations, weights) : []), [results, weights])

  // Domyślnie pokazujemy obecny płodozmian pola, a gdy go nie ma, pierwszy w rankingu.
  const shown =
    ranked.find((entry) => entry.rotation.id === rotationId) ??
    ranked.find((entry) => entry.rotation.is_current) ??
    ranked[0]

  return (
    <div className="mx-auto flex max-w-[1680px] flex-col gap-5 p-4 lg:p-6">
      <header>
        <h1 className="text-[28px] font-semibold leading-tight">Rotation replay</h1>
        <p className="mt-1 text-[15px] text-muted-foreground">
          {fieldShortName(selected.properties)}
          {results && ` · every rotation replayed through each year from ${results.period[0]} to ${results.period[1]}`}
        </p>
      </header>

      {/* Ostrzeżenie zawsze widoczne na górze (specyfikacja 5.3) */}
      <p className="flex gap-3 rounded-lg border border-warning-border bg-warning px-4 py-3 text-[15px] leading-snug">
        <TriangleAlert aria-hidden className="mt-0.5 h-5 w-5 shrink-0" />
        <span>
          <strong className="font-semibold">Read this as a comparison, not as farm profit.</strong> Every rotation shows
          a loss on average because we count full costs including land rent, and leave out crop insurance and program
          payments.
        </span>
      </p>

      {state.status === 'loading' && <p className="text-muted-foreground">Loading the replay…</p>}
      {state.status === 'error' && <p role="alert">The replay could not be loaded. {state.message}</p>}
      {state.status === 'missing' && (
        <div className="rounded-lg border border-border bg-card p-5">
          <h2 className="text-[19px] font-semibold">The replay is not ready for this field yet</h2>
          <p className="mt-1 text-[15px] text-muted-foreground">
            So far the replay has been run for the Tribune fields only.
          </p>
          <Link
            to={{ pathname: '/replay', search: `?field=${DEFAULT_FIELD_ID}` }}
            className="mt-2 inline-flex min-h-11 items-center text-[15px] font-semibold text-primary underline underline-offset-4"
          >
            Open the replay for Tribune 001
          </Link>
        </div>
      )}

      {results && shown && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[260px_minmax(0,1fr)] lg:items-start xl:grid-cols-[280px_minmax(0,1fr)_420px]">
          {/* Trzy kolumny dopiero na szerokim ekranie; na średnim karta schodzi pod ranking, na telefonie jedna kolumna */}
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
              <p className="mt-3 text-[15px] leading-snug">{stabilitySentence(results)}</p>
            </section>

            <YearChart rotation={shown.rotation} />
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
