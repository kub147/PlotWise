// "Region" view: the 46-county study area behind the demo fields.
// Left: county map with three layers and the field outlines of the demo counties. Right: what farmers grow
// on 31,660 fields, and the selected county (practice from workstream B, model from workstream D).
import type { LatLngBoundsExpression, LatLngTuple } from 'leaflet'
import { useMemo, useState } from 'react'
import { RegionMap } from '@/components/region/RegionMap'
import { Card, CardSection, SectionLabel } from '@/components/ui/card'
import { SegmentedControl } from '@/components/ui/segmented-control'
import type { FieldFeature } from '@/lib/data'
import {
  LAYER_INFO,
  ROTATION_CLASSES,
  ROTATION_CLASS_STYLE,
  countyModel,
  useCountyFields,
  useRegionData,
  type CountyCollection,
  type RegionData,
  type RegionLayer,
  type RotationClass,
} from '@/lib/region'
import type { Scenario } from '@/lib/results'
import { rotationLabel } from '@/lib/rotation'
import { formatNumber, formatUsd, haToAcres, mmToInches } from '@/lib/units'
import { useT } from '@/lib/i18n'

const LAYER_OPTIONS: { value: RegionLayer; label: string }[] = [
  { value: 'fallow', label: 'Fallow today' },
  { value: 'left', label: 'Fallow given up' },
  { value: 'model', label: 'Model' },
]

const SCENARIO_OPTIONS: { value: Scenario; label: string }[] = [
  { value: 'county_average', label: 'Average field' },
  { value: 'well_managed', label: 'Well-managed field' },
]

// Counties whose field outlines are in the repo (data/processed/county_fields.geojson).
const OUTLINE_COUNTIES = ['ks071', 'ks193', 'ks051']

const percent = (share: number) => `${formatNumber(share * 100, share > 0 && share < 0.1 ? 1 : 0)}%`

function countyBounds(counties: CountyCollection, countyId: string): LatLngBoundsExpression | null {
  const feature = counties.features.find((county) => county.properties.county_id === countyId)
  if (!feature) return null
  return feature.geometry.coordinates[0].map(([lon, lat]) => [lat, lon] as LatLngTuple)
}

// Horizontal bars of the rotation classes; every bar carries its own label and number.
function RotationShares({ shares }: { shares: Record<RotationClass, number> }) {
  const t = useT()
  return (
    <ul className="flex flex-col gap-2">
      {ROTATION_CLASSES.map((rotation) => {
        const share = shares[rotation] ?? 0
        const style = ROTATION_CLASS_STYLE[rotation]
        return (
          <li key={rotation}>
            <div className="flex items-baseline justify-between gap-3 text-[13px]">
              <span className="flex items-center gap-2">
                <span className="h-3 w-3 shrink-0 rounded-sm ring-1 ring-inset ring-input" style={{ background: style.color }} aria-hidden />
                {t(style.label)}
              </span>
              <span className="font-mono font-semibold">{percent(share)}</span>
            </div>
            <div className="mt-1 h-2 rounded-sm bg-muted" aria-hidden>
              <div className="h-2 rounded-sm" style={{ width: `${Math.min(100, share * 100)}%`, background: style.color }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[13px] text-muted-foreground">{label}</dt>
      <dd className="font-mono text-[17px] font-semibold">{value}</dd>
    </div>
  )
}

function RegionContent({ data, selectedField }: { data: RegionData; selectedField: FieldFeature }) {
  const t = useT()
  const fields = useCountyFields()
  const [layer, setLayer] = useState<RegionLayer>('fallow')
  const [scenario, setScenario] = useState<Scenario>('county_average')
  // Starts on the county of the field chosen on "My field" (field_id prefix, e.g. ks071).
  const [countyId, setCountyId] = useState(selectedField.properties.field_id.split('-')[0])
  const [focus, setFocus] = useState<{ bounds: LatLngBoundsExpression; nonce: number } | null>(null)

  const names = useMemo(
    () =>
      data.counties.features
        .map((county) => ({ id: county.properties.county_id, name: county.properties.name }))
        .sort((a, b) => a.name.localeCompare(b.name)),
    [data.counties],
  )

  const county = data.counties.features.find((feature) => feature.properties.county_id === countyId)?.properties
  const practice = data.rotations.counties[countyId]
  const result = data.results.counties[countyId]
  const model = countyModel(result, scenario)
  const info = LAYER_INFO[layer]

  const zoomTo = (id: string) => {
    setCountyId(id)
    const bounds = countyBounds(data.counties, id)
    if (bounds) setFocus({ bounds, nonce: Date.now() })
  }

  return (
    <div className="mx-auto grid max-w-[1680px] grid-cols-1 gap-4 p-4 lg:h-full lg:grid-cols-[minmax(0,1fr)_440px] lg:gap-5 lg:p-5">
      <div className="flex min-w-0 flex-col gap-3 lg:min-h-0">
        <header>
          <h1 className="text-[34px] font-semibold leading-tight">{t('Region')}</h1>
          <p className="mt-1 text-[15px] text-muted-foreground">
            {t('{counties} western Kansas counties · {fields} fields · {acres} million acres read from satellite crop maps, {years}', { counties: data.counties.features.length, fields: formatNumber(data.rotations.fields), acres: formatNumber(haToAcres(data.rotations.area_ha) / 1e6, 1), years: data.rotations.years })}
          </p>
        </header>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <SegmentedControl label={t('County map layer')} options={LAYER_OPTIONS.map((item) => ({ ...item, label: t(item.label) }))} value={layer} onValueChange={setLayer} />
          {layer === 'model' && (
            <SegmentedControl
              label={t('Yield level used by the model')}
              options={SCENARIO_OPTIONS.map((item) => ({ ...item, label: t(item.label) }))}
              value={scenario}
              onValueChange={setScenario}
            />
          )}
        </div>

        <div className="min-h-0 lg:min-h-[320px] lg:flex-1">
          <RegionMap
            counties={data.counties}
            results={data.results}
            fields={fields}
            layer={layer}
            scenario={scenario}
            selectedId={countyId}
            onSelect={setCountyId}
            focus={focus}
          />
        </div>

        <div className="pw-sheet rounded-3xl px-5 py-4">
          <h2 className="text-[15px] font-semibold">{t(info.title)}</h2>
          <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-[13px]">
            {info.legend.map((item) => (
              <li key={item.label} className="flex items-center gap-1.5">
                <span className="h-3 w-5 rounded-sm ring-1 ring-inset ring-input" style={{ background: item.color }} aria-hidden />
              {t(item.label)}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
            {t(info.source)}
            {layer === 'model' && ` ${t(data.results.caution)}`}
          </p>
          <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px]">
            <span className="text-muted-foreground">
              {fields ? t('Field outlines, coloured by rotation as in the rotation list, are drawn for three counties. Zoom to:') : t('Zoom to:')}
            </span>
            {OUTLINE_COUNTIES.map((id) => {
              const name = names.find((entry) => entry.id === id)?.name
              return name ? (
                <button
                  key={id}
                  type="button"
                  onClick={() => zoomTo(id)}
                  className="min-h-9 font-semibold text-primary underline underline-offset-4"
                >
                  {name}
                </button>
              ) : null
            })}
          </p>
        </div>
      </div>

      <div className="flex min-w-0 flex-col gap-4 lg:min-h-0 lg:overflow-y-auto lg:pr-1">
        <Card>
          <CardSection>
            <SectionLabel>{t('What farmers grow across the region')}</SectionLabel>
            <RotationShares shares={data.rotations.share_of_area} />
            <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
              {t('Share of the area of {count} fields, from the crop grown each year {years} (USDA Cropland Data Layer). These are fields of 100 acres or more with one clear crop sequence: a sample of clean fields, not all cropland.', { count: formatNumber(data.rotations.fields), years: data.rotations.years })}
            </p>
          </CardSection>
        </Card>

        <Card aria-live="polite">
          <CardSection>
            <label htmlFor="county-select" className="text-[15px] font-medium text-foreground">
              {t('County')}
            </label>
            <select
              id="county-select"
              value={countyId}
              onChange={(event) => zoomTo(event.target.value)}
              className="mt-2 block min-h-12 w-full rounded-2xl border-0 bg-foreground/[0.06] px-4 text-[17px] font-medium"
            >
              {names.map((entry) => (
                <option key={entry.id} value={entry.id}>
                  {entry.name} {t('County')}
                </option>
              ))}
            </select>
            <p className="mt-1 text-[13px] text-muted-foreground">{t('Or select a county on the map.')}</p>
          </CardSection>

          {county && (
            <CardSection>
              <SectionLabel>{t('Fallow')}</SectionLabel>
              <dl className="grid grid-cols-3 gap-3">
                <Stat label={t('In 2008')} value={percent(county.fallow_share_2008)} />
                <Stat label={t('Today')} value={percent(county.fallow_share_latest)} />
                {result && <Stat label={t('Rain a year')} value={`${formatNumber(mmToInches(result.precip_mm_per_year), 1)} in`} />}
              </dl>
              <p className="mt-2 text-[13px] text-muted-foreground">{t("Share of the county's cropland left fallow.")}</p>
            </CardSection>
          )}

          {practice && (
            <CardSection>
              <SectionLabel>{t('What farmers grow here')}</SectionLabel>
              {practice.fields > 0 ? (
                <>
                  <RotationShares
                    shares={Object.fromEntries(
                      ROTATION_CLASSES.map((rotation) => [rotation, practice.rotations[rotation]?.share_of_area ?? 0]),
                    ) as Record<RotationClass, number>}
                  />
                  <p className="mt-3 text-[13px] text-muted-foreground">
                    {t('{fields} fields, {acres} acres.', { fields: formatNumber(practice.fields), acres: formatNumber(haToAcres(practice.area_ha)) })}
                  </p>
                </>
              ) : (
                <p className="text-[15px]">{t('No field in this county passed the filter.')}</p>
              )}
            </CardSection>
          )}

          <CardSection>
            <SectionLabel>{t('What the model says')}</SectionLabel>
            <SegmentedControl
              label={t('Yield level used by the model')}
              options={SCENARIO_OPTIONS.map((item) => ({ ...item, label: t(item.label) }))}
              value={scenario}
              onValueChange={setScenario}
            />
            {model ? (
              <>
                <dl className="mt-3 grid grid-cols-2 gap-3">
                  <Stat label={t('Best rotation')} value={t(rotationLabel(model.best_rotation) ?? model.best_rotation)} />
                  <Stat
                    label={t('Sorghum in place of fallow')}
                    value={`${model.gain_replacing_fallow_usd_acre > 0 ? '+' : ''}${formatUsd(model.gain_replacing_fallow_usd_acre)} ${t('/acre')}`}
                  />
                </dl>
                {result?.practice?.most_common_of_three && (
                  <p className="mt-2 text-[15px] leading-snug">
                    {result.practice.most_common_of_three === model.best_rotation
                      ? t('This is also the rotation farmers here grow most often.')
                      : t('Farmers here most often grow {rotation}. Where the model and farmers disagree, trust local experience first: the model leaves out crop insurance, program payments and workload.', { rotation: t(rotationLabel(result.practice.most_common_of_three) ?? result.practice.most_common_of_three) })}
                  </p>
                )}
              </>
            ) : (
              <p className="mt-3 text-[15px]">{t('The model has no result for this county at this yield level.')}</p>
            )}
            <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
              {t('Sorghum in place of fallow: wheat – sorghum – fallow minus wheat – fallow, average per acre a year, 1996–2025. One point stands for the whole county, so read it as a direction, not a number for a field.')}
            </p>
          </CardSection>
        </Card>
      </div>
    </div>
  )
}

export function Region({ selected }: { selected: FieldFeature }) {
  const t = useT()
  const state = useRegionData()
  if (state.status === 'loading') return <p className="p-6 text-muted-foreground">{t('Loading the county map…')}</p>
  if (state.status === 'error') {
    return (
      <p role="alert" className="p-6">
        {t('The county data could not be loaded.')} {state.message}
      </p>
    )
  }
  return <RegionContent data={state.data} selectedField={selected} />
}
