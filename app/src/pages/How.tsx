// "How we know" view: how the replay was checked, where the data comes from, what we do not claim,
// and the full evidence register (E01…) read from crops-economics/reference/evidence.md.
import { ArrowDown, ArrowRight } from 'lucide-react'
import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card } from '@/components/ui/card'
import type { AppData } from '@/lib/data'
import { useEvidence, type EvidenceItem } from '@/lib/evidence'
import { imageUrl } from '@/lib/fieldMedia'
import { scenarioView, useFieldResults, type FieldResults } from '@/lib/results'
import { rotationLabel } from '@/lib/rotation'
import { formatUsd } from '@/lib/units'
import { cn } from '@/lib/utils'

// Pole przy stacji K-State w Tribune: na nim porównujemy kolejność płodozmianów z badaniem K-State.
const BENCHMARK_FIELD = 'ks071-001'
// Lata i kolejność z badania K-State (evidence.md, E07): W-S-F pierwszy, W-F drugi, W-C-F wśród najsłabszych.
const BENCHMARK_YEARS: [number, number] = [2008, 2015]
const KSTATE_ORDER = ['WSF', 'WF', 'WCF']

// Trzy kafle z raportu walidacji silnika (docs/engine-validation.md, sekcje 2 i 3). Liczby są przepisane z raportu.
const VALIDATION_TILES = [
  {
    title: 'Sorghum: about 60%',
    text: 'Modeled water use explains about 61% of the year-to-year swings in sorghum yield measured at the K-State trials in Tribune. It is 54% when each year is predicted without the model having seen it.',
  },
  {
    title: 'Wheat: about 45%',
    text: 'With hot days counted, the model explains about 45% of the swings in measured wheat yield. Predicting a year it has not seen, only about 13%. Treat any single wheat year as a rough estimate.',
  },
  {
    title: 'It finds the failure years',
    text: 'The trials lost the whole wheat crop in 2002 and 2013 and the whole sorghum crop in 2002 and 2012. Those are the two lowest years the model gives for each crop.',
  },
]

const SOURCE_GROUPS = [
  {
    title: 'Weather and water',
    items: ['gridMET', 'PRISM', 'NASA POWER', 'NASA GPM IMERG', 'NASA GRACE / GRACE-FO', 'NASA SMAP'],
  },
  {
    title: 'The field',
    items: ['USDA Cropland Data Layer', 'USDA soil survey (SSURGO)', 'Landsat', 'NASA ECOSTRESS', 'USDA NAIP aerial photos'],
  },
  {
    title: 'Crops and money',
    items: ['K-State field trials at Tribune', 'K-State farm budgets', 'USDA NASS prices and yields', 'FAO-56 crop water use'],
  },
]

const VIEWS = ['My field', 'What has changed', 'Rotation replay', 'This season', 'Region']

const NOT_CLAIMED = [
  'We do not say rain is declining. One rainfall record shows drying and the others do not.',
  'The dollar numbers are not farm profit. They count full costs with land rent and leave out crop insurance and program payments. Use them to compare rotations.',
  'Demo fields at the same site get almost the same numbers. They share the same weather grid cells and similar soils; what differs is their history.',
  'Wheat is modeled weakly. Winterkill, disease, hail and late freezes are not water effects, and the model does not see them.',
  'No rotation is “the best”. The ranking depends on your priorities, and differences of a few dollars per acre are inside the model’s error.',
]

// Usuwa znaczniki Markdown z tekstu źródła (*kursywa*, `kod`), żeby nie pokazywać gwiazdek.
const plain = (text: string) => text.replace(/[*`]/g, '')

// Czwarty kafel: kolejność płodozmianów w latach badania K-State, policzona z aktualnych wyników silnika.
function MoneyOrderTile({ results }: { results: FieldResults | null }) {
  if (!results) {
    return (
      <Card className="p-6">
        <h3 className="text-[19px] font-semibold leading-snug">Order of rotations by money</h3>
        <p className="mt-2 text-[15px] leading-snug text-muted-foreground">The replay for Tribune 001 is not loaded.</p>
      </Card>
    )
  }
  // Badanie K-State liczyło plony z doświadczeń, więc bierzemy scenariusz „well managed", jeśli jest w pliku.
  const hasWellManaged = results.yield_scenarios?.well_managed !== undefined
  const { rotations } = scenarioView(results, hasWellManaged ? 'well_managed' : 'county_average')
  const averages = KSTATE_ORDER.flatMap((id) => {
    const rotation = rotations.find((candidate) => candidate.id === id)
    if (!rotation) return []
    const years = rotation.net_return_usd_acre.filter(
      ([year]) => year >= BENCHMARK_YEARS[0] && year <= BENCHMARK_YEARS[1],
    )
    if (years.length === 0) return []
    return [{ id, mean: years.reduce((sum, [, value]) => sum + value, 0) / years.length }]
  })
  const ours = [...averages].sort((a, b) => b.mean - a.mean)
  const sameOrder = ours.length === KSTATE_ORDER.length && ours.every((entry, i) => entry.id === KSTATE_ORDER[i])
  const label = (id: string) => rotationLabel(id) ?? id

  return (
    <Card className="p-6">
      <h3 className="text-[19px] font-semibold leading-snug">
        {sameOrder ? 'Same money order as the K-State study' : 'Money order differs from the K-State study'}
      </h3>
      <p className="mt-2 text-[15px] leading-snug text-muted-foreground">
        In a K-State study at Tribune for {BENCHMARK_YEARS[0]}–{BENCHMARK_YEARS[1]}, {label('WSF')} earned the most,{' '}
        {label('WF')} came second and {label('WCF')} was among the lowest. The replay for the same years on Tribune 001
        {hasWellManaged ? ', at the well-managed yield level,' : ''} gives:
      </p>
      <ol className="mt-3 flex flex-col gap-1 text-[15px]">
        {ours.map((entry, i) => (
          <li key={entry.id} className="flex justify-between gap-3">
            <span>
              {i + 1}. {label(entry.id)}
            </span>
            <span className="font-semibold">{formatUsd(entry.mean)} per acre</span>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
        {sameOrder
          ? 'The order matches. The dollar amounts are not comparable: the study used its own prices and costs.'
          : 'The order does not match. Differences of a few dollars per acre are inside the model’s error, so read this as “close”, not as a new finding.'}
      </p>
    </Card>
  )
}

function EvidenceRow({ item, highlighted }: { item: EvidenceItem; highlighted: boolean }) {
  return (
    <li
      id={`evidence-${item.id}`}
      className={cn(
        'grid scroll-mt-24 gap-x-4 gap-y-1 rounded-2xl px-4 py-3 sm:grid-cols-[3.5rem_minmax(0,1fr)]',
        highlighted && 'pw-selected bg-card',
      )}
    >
      <span className="text-[15px] font-semibold">{item.id}</span>
      <div>
        <p className="text-[15px] leading-snug">{plain(item.finding)}</p>
        <p className="mt-1 text-[13px] leading-snug text-muted-foreground">{plain(item.source)}</p>
        <p className="mt-1 text-[13px] text-muted-foreground">How we have it: {plain(item.status)}</p>
      </div>
    </li>
  )
}

export function How({ data }: { data: AppData }) {
  const evidence = useEvidence()
  const [params] = useSearchParams()
  const wanted = params.get('evidence')
  const benchmark = useFieldResults(BENCHMARK_FIELD, data.manifest.results.includes(BENCHMARK_FIELD))
  const items = evidence
    ? Object.values(evidence.items).sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)))
    : []
  const hasWanted = wanted !== null && evidence?.items[wanted] !== undefined

  // Link z karty płodozmianu (#/how?evidence=E07) przewija do właściwego wiersza.
  useEffect(() => {
    if (!hasWanted || wanted === null) return
    document.getElementById(`evidence-${wanted}`)?.scrollIntoView({ block: 'center' })
  }, [hasWanted, wanted])

  return (
    <div className="mx-auto flex max-w-[1280px] flex-col gap-8 p-4 lg:p-6">
      <header>
        <h1 className="text-[34px] font-semibold leading-tight">How we know</h1>
        <p className="mt-1 max-w-[70ch] text-[15px] text-muted-foreground">
          The replay is a model. This page shows how far to trust it: what it was checked against, where the data
          comes from, and what we do not claim.
        </p>
      </header>

      <section aria-labelledby="checked-heading" className="flex flex-col gap-4">
        <h2 id="checked-heading" className="text-[24px] font-semibold leading-tight">
          Checked against 24 years of field trials
        </h2>
        <Card className="overflow-hidden p-4 lg:p-6">
          <a href={imageUrl('engine_validation.png')} target="_blank" rel="noreferrer" className="block">
            <img
              src={imageUrl('engine_validation.png')}
              alt="Charts comparing modeled yields with yields measured at the K-State Tribune trials for wheat and sorghum"
              loading="lazy"
              className="w-full rounded-2xl"
            />
          </a>
          <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
            Modeled yield against yield measured at the K-State Southwest Research-Extension Center in Tribune,
            1996–2020. From the engine’s validation report.
          </p>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2">
          {VALIDATION_TILES.map((tile) => (
            <Card key={tile.title} className="p-6">
              <h3 className="text-[19px] font-semibold leading-snug">{tile.title}</h3>
              <p className="mt-2 text-[15px] leading-snug text-muted-foreground">{tile.text}</p>
            </Card>
          ))}
          <MoneyOrderTile results={benchmark.status === 'ready' ? benchmark.results : null} />
        </div>
      </section>

      <section aria-labelledby="fusion-heading" className="flex flex-col gap-4">
        <h2 id="fusion-heading" className="text-[24px] font-semibold leading-tight">
          From satellites and trials to your field
        </h2>
        <div className="grid items-stretch gap-3 lg:grid-cols-[minmax(0,1.6fr)_auto_minmax(0,1fr)_auto_minmax(0,0.9fr)]">
          <Card className="flex flex-col gap-4 p-6">
            <h3 className="text-[15px] font-medium">Data</h3>
            {SOURCE_GROUPS.map((group) => (
              <div key={group.title}>
                <p className="text-[13px] text-muted-foreground">{group.title}</p>
                <ul className="mt-1.5 flex flex-wrap gap-1.5">
                  {group.items.map((item) => (
                    <li key={item} className="rounded-full bg-foreground/[0.06] px-3 py-1 text-[13px]">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </Card>

          <div className="flex items-center justify-center text-muted-foreground" aria-hidden>
            <ArrowRight className="hidden h-6 w-6 lg:block" />
            <ArrowDown className="h-6 w-6 lg:hidden" />
          </div>

          <Card className="flex flex-col justify-center gap-3 p-6">
            <h3 className="text-[15px] font-medium">The engine</h3>
            <ol className="flex flex-col gap-2 text-[15px] leading-snug">
              <li>1. Daily soil-water balance through every crop and fallow</li>
              <li>2. Yield from the water each crop used</li>
              <li>3. Yield × that year’s price − the K-State budget cost</li>
              <li>4. Scores for money, dry years, water and soil</li>
            </ol>
            <p className="text-[13px] leading-snug text-muted-foreground">
              Every rotation is started in every year, so each one gets the full run of good and bad years.
            </p>
          </Card>

          <div className="flex items-center justify-center text-muted-foreground" aria-hidden>
            <ArrowRight className="hidden h-6 w-6 lg:block" />
            <ArrowDown className="h-6 w-6 lg:hidden" />
          </div>

          <Card className="flex flex-col gap-3 p-6">
            <h3 className="text-[15px] font-medium">What you see</h3>
            <ul className="flex flex-col gap-1.5">
              {VIEWS.map((view) => (
                <li key={view} className="rounded-full bg-leaf-soft px-3 py-1.5 text-[13px] font-medium text-accent-foreground">
                  {view}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      <section aria-labelledby="not-claimed-heading" className="rounded-[28px] bg-warning p-6 lg:p-8">
        <h2 id="not-claimed-heading" className="text-[24px] font-semibold leading-tight">
          What we do not claim
        </h2>
        <ul className="mt-4 flex max-w-[80ch] list-disc flex-col gap-2.5 pl-5 text-[15px] leading-snug">
          {NOT_CLAIMED.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        {evidence?.insuranceSentence && (
          <p className="mt-4 max-w-[80ch] text-[15px] leading-snug">{evidence.insuranceSentence}</p>
        )}
      </section>

      <section aria-labelledby="evidence-heading" className="flex flex-col gap-4">
        <div>
          <h2 id="evidence-heading" className="text-[24px] font-semibold leading-tight">
            The evidence behind the cards
          </h2>
          <p className="mt-1 max-w-[70ch] text-[15px] text-muted-foreground">
            Every claim on a rotation card points to one of these entries.
          </p>
        </div>
        <Card className="p-2 lg:p-3">
          {evidence === null && <p className="p-4 text-muted-foreground">Loading the evidence register…</p>}
          {evidence !== null && items.length === 0 && (
            <p className="p-4 text-muted-foreground">The evidence register could not be loaded.</p>
          )}
          <ul className="flex flex-col">
            {items.map((item) => (
              <EvidenceRow key={item.id} item={item} highlighted={item.id === wanted} />
            ))}
          </ul>
        </Card>
      </section>
    </div>
  )
}
