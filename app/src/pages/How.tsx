// "How we know" view: how the replay was checked, where the data comes from, what we do not claim,
// and the full evidence register (E01…) read from crops-economics/reference/evidence.md.
import { ArrowDown, ArrowRight } from 'lucide-react'
import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ValidationChart } from '@/components/how/ValidationChart'
import { Card } from '@/components/ui/card'
import { useJson } from '@/lib/climate'
import type { AppData } from '@/lib/data'
import { useEvidence, type EvidenceItem } from '@/lib/evidence'
import { imageUrl } from '@/lib/fieldMedia'
import { scenarioView, useFieldResults, type FieldResults } from '@/lib/results'
import { rotationLabel } from '@/lib/rotation'
import { formatUsd } from '@/lib/units'
import { useLang, useT } from '@/lib/i18n'
import { REFERENCE_SERIES, validationTiles, type Validation } from '@/lib/validation'
import { cn } from '@/lib/utils'

// Field next to the K-State station at Tribune: the rotation order is compared with the K-State study on it.
const BENCHMARK_FIELD = 'ks071-001'
// Years and order from the K-State study (evidence.md, E07): W-S-F first, W-F second, W-C-F among the lowest.
const BENCHMARK_YEARS: [number, number] = [2008, 2015]
const KSTATE_ORDER = ['WSF', 'WF', 'WCF']

// Three tiles from the engine validation report (docs/engine-validation.md, sections 2 and 3). The numbers are copied from the report.
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

// Strips Markdown marks from the source text (*italics*, `code`) so that no asterisks show.
const plain = (text: string) => text.replace(/[*`]/g, '')

// Fourth tile: the rotation order in the years of the K-State study, computed from the current engine results.
function MoneyOrderTile({ results }: { results: FieldResults | null }) {
  const t = useT()
  if (!results) {
    return (
      <Card className="p-6">
        <h3 className="text-[19px] font-semibold leading-snug">{t('Order of rotations by money')}</h3>
        <p className="mt-2 text-[15px] leading-snug text-muted-foreground">{t('The replay for Tribune 001 is not loaded.')}</p>
      </Card>
    )
  }
  // The K-State study used trial yields, so the "well managed" scenario is used when the file has it.
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
  const label = (id: string) => t(rotationLabel(id) ?? id)

  return (
    <Card className="p-6">
      <h3 className="text-[19px] font-semibold leading-snug">
        {sameOrder ? t('Same money order as the K-State study') : t('Money order differs from the K-State study')}
      </h3>
      <p className="mt-2 text-[15px] leading-snug text-muted-foreground">
        {t('In a K-State study at Tribune for {from}–{to}, {wsf} earned the most, {wf} came second and {wcf} was among the lowest. The replay for the same years on Tribune 001{scenario} gives:', { from: BENCHMARK_YEARS[0], to: BENCHMARK_YEARS[1], wsf: label('WSF'), wf: label('WF'), wcf: label('WCF'), scenario: hasWellManaged ? t(', at the well-managed yield level,') : '' })}
      </p>
      <ol className="mt-3 flex flex-col gap-1 text-[15px]">
        {ours.map((entry, i) => (
          <li key={entry.id} className="flex justify-between gap-3">
            <span>
              {i + 1}. {label(entry.id)}
            </span>
            <span className="font-semibold">{formatUsd(entry.mean)} {t('per acre')}</span>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
        {sameOrder
          ? t('The order matches. The dollar amounts are not comparable: the study used its own prices and costs.')
          : t('The order does not match. Differences of a few dollars per acre are inside the model’s error, so read this as “close”, not as a new finding.')}
      </p>
    </Card>
  )
}

function EvidenceRow({ item, highlighted }: { item: EvidenceItem; highlighted: boolean }) {
  const t = useT()
  const { lang } = useLang()
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
        <p className="text-[15px] leading-snug">{lang === 'pl' ? t(`Evidence ${item.id}`) : plain(item.finding)}</p>
        <p className="mt-1 text-[13px] leading-snug text-muted-foreground">{t(plain(item.source))}</p>
        <p className="mt-1 text-[13px] text-muted-foreground">{t('How we have it:')} {t(plain(item.status))}</p>
      </div>
    </li>
  )
}

export function How({ data }: { data: AppData }) {
  const t = useT()
  const evidence = useEvidence()
  const [params] = useSearchParams()
  const wanted = params.get('evidence')
  const benchmark = useFieldResults(BENCHMARK_FIELD, data.manifest.results.includes(BENCHMARK_FIELD))
  const items = evidence
    ? Object.values(evidence.items).sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)))
    : []
  const hasWanted = wanted !== null && evidence?.items[wanted] !== undefined
  const validationState = useJson<Validation>('validation.json')
  const validation = validationState.status === 'ready' ? validationState.data : null
  const charts = validation
    ? REFERENCE_SERIES.flatMap((id) => {
        const series = validation.series.find((candidate) => candidate.id === id)
        if (!series) return []
        const zeroYears = validation.failures.find((failure) => failure.series === id)?.measured_zero_years ?? []
        return [{ series, zeroYears }]
      })
    : []
  const tiles = validation ? validationTiles(validation, t) : VALIDATION_TILES

  // A link from a rotation card (#/how?evidence=E07) scrolls to the right row.
  useEffect(() => {
    if (!hasWanted || wanted === null) return
    document.getElementById(`evidence-${wanted}`)?.scrollIntoView({ block: 'center' })
  }, [hasWanted, wanted])

  return (
    <div className="mx-auto flex max-w-[1280px] flex-col gap-8 p-4 lg:p-6">
      <header>
        <h1 className="text-[34px] font-semibold leading-tight">{t('How we know')}</h1>
        <p className="mt-1 max-w-[70ch] text-[15px] text-muted-foreground">
          {t('The replay is a model. This page shows how far to trust it: what it was checked against, where the data comes from, and what we do not claim.')}
        </p>
      </header>

      <section aria-labelledby="checked-heading" className="flex flex-col gap-4">
        <h2 id="checked-heading" className="text-[24px] font-semibold leading-tight">
          {t('Checked against 24 years of field trials')}
        </h2>
        {validationState.status === 'loading' && <p className="text-muted-foreground">{t('Loading the validation...')}</p>}
        {charts.length > 0 && (
          <>
            <div className="grid gap-4 lg:grid-cols-2">
              {charts.map(({ series, zeroYears }) => (
                <ValidationChart key={series.id} series={series} zeroYears={zeroYears} />
              ))}
            </div>
            <p className="max-w-[80ch] text-[13px] leading-snug text-muted-foreground">
              {t("Measured at {site}. The engine was run there with the same gridded weather it uses for every field, not with the station's own rain gauge. Its water settings were fitted to measured soil water, not to these yields.", { site: validation?.site ?? '' })}
            </p>
          </>
        )}
        {validationState.status === 'missing' && (
          <Card className="overflow-hidden p-4 lg:p-6">
            <a href={imageUrl('engine_validation.png')} target="_blank" rel="noreferrer" className="block">
              <img
                src={imageUrl('engine_validation.png')}
                alt={t('Charts comparing modeled yields with yields measured at the K-State Tribune trials for wheat and sorghum')}
                loading="lazy"
                className="w-full rounded-2xl"
              />
            </a>
            <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
              {t('Modeled yield against yield measured at the K-State Southwest Research-Extension Center in Tribune, 1996–2020. From the engine’s validation report.')}
            </p>
          </Card>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          {tiles.map((tile) => (
            <Card key={tile.title} className="p-6">
              <h3 className="text-[19px] font-semibold leading-snug">{t(tile.title)}</h3>
              <p className="mt-2 text-[15px] leading-snug text-muted-foreground">{t(tile.text)}</p>
            </Card>
          ))}
          <MoneyOrderTile results={benchmark.status === 'ready' ? benchmark.results : null} />
        </div>
      </section>

      <section aria-labelledby="fusion-heading" className="flex flex-col gap-4">
        <h2 id="fusion-heading" className="text-[24px] font-semibold leading-tight">
          {t('From satellites and trials to your field')}
        </h2>
        <div className="grid items-stretch gap-3 lg:grid-cols-[minmax(0,1.6fr)_auto_minmax(0,1fr)_auto_minmax(0,0.9fr)]">
          <Card className="flex flex-col gap-4 p-6">
            <h3 className="text-[15px] font-medium">{t('Data')}</h3>
            {SOURCE_GROUPS.map((group) => (
              <div key={group.title}>
                <p className="text-[13px] text-muted-foreground">{t(group.title)}</p>
                <ul className="mt-1.5 flex flex-wrap gap-1.5">
                  {group.items.map((item) => (
                    <li key={item} className="rounded-full bg-foreground/[0.06] px-3 py-1 text-[13px]">
                      {t(item)}
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
            <h3 className="text-[15px] font-medium">{t('The engine')}</h3>
            <ol className="flex flex-col gap-2 text-[15px] leading-snug">
              <li>{t('1. Daily soil-water balance through every crop and fallow')}</li>
              <li>{t('2. Yield from the water each crop used')}</li>
              <li>{t('3. Yield × that year’s price − the K-State budget cost')}</li>
              <li>{t('4. Scores for money, dry years, water and soil')}</li>
            </ol>
            <p className="text-[13px] leading-snug text-muted-foreground">
              {t('Every rotation is started in every year, so each one gets the full run of good and bad years.')}
            </p>
          </Card>

          <div className="flex items-center justify-center text-muted-foreground" aria-hidden>
            <ArrowRight className="hidden h-6 w-6 lg:block" />
            <ArrowDown className="h-6 w-6 lg:hidden" />
          </div>

          <Card className="flex flex-col gap-3 p-6">
            <h3 className="text-[15px] font-medium">{t('What you see')}</h3>
            <ul className="flex flex-col gap-1.5">
              {VIEWS.map((view) => (
                <li key={view} className="rounded-full bg-leaf-soft px-3 py-1.5 text-[13px] font-medium text-accent-foreground">
                  {t(view)}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      <section aria-labelledby="not-claimed-heading" className="rounded-[28px] bg-warning p-6 lg:p-8">
        <h2 id="not-claimed-heading" className="text-[24px] font-semibold leading-tight">
          {t('What we do not claim')}
        </h2>
        <ul className="mt-4 flex max-w-[80ch] list-disc flex-col gap-2.5 pl-5 text-[15px] leading-snug">
          {NOT_CLAIMED.map((line) => (
            <li key={line}>{t(line)}</li>
          ))}
        </ul>
        {evidence?.insuranceSentence && (
          <p className="mt-4 max-w-[80ch] text-[15px] leading-snug">{t(evidence.insuranceSentence)}</p>
        )}
      </section>

      <section aria-labelledby="evidence-heading" className="flex flex-col gap-4">
        <div>
          <h2 id="evidence-heading" className="text-[24px] font-semibold leading-tight">
            {t('The evidence behind the cards')}
          </h2>
          <p className="mt-1 max-w-[70ch] text-[15px] text-muted-foreground">
            {t('Every claim on a rotation card points to one of these entries.')}
          </p>
        </div>
        <Card className="p-2 lg:p-3">
          {evidence === null && <p className="p-4 text-muted-foreground">{t('Loading the evidence register…')}</p>}
          {evidence !== null && items.length === 0 && (
            <p className="p-4 text-muted-foreground">{t('The evidence register could not be loaded.')}</p>
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
