// "My field" view. On a wide screen the map fills the whole screen, and the field list and the field card float over it
// as two panels (the list on the left as "glass", the card on the right). On a phone everything stacks.
// The views of the field from above (aerial photo, greenness, surface heat) open in a popup, from the card or the map.
import { useMemo, useState } from 'react'
import { FieldCard } from '@/components/FieldCard'
import { FieldList } from '@/components/FieldList'
import { FieldMap } from '@/components/FieldMap'
import { FieldViewer } from '@/components/field/FieldViewer'
import type { AppData, FieldFeature } from '@/lib/data'
import { heatScenesFor, useHeatSummary, useNdvi, type ViewerTab } from '@/lib/fieldMedia'
import { useT } from '@/lib/i18n'
import { toCropLetter } from '@/lib/rotation'

type MyFieldProps = {
  data: AppData
  selected: FieldFeature
  onSelect: (fieldId: string) => void
}

export function MyField({ data, selected, onSelect }: MyFieldProps) {
  const t = useT()
  const p = selected.properties
  // Which view of the popup is open; null = closed.
  const [viewer, setViewer] = useState<ViewerTab | null>(null)
  const hasAerial = data.manifest.naip.includes(p.field_id)
  const ndvi = useNdvi(p.field_id, data.manifest.ndvi.includes(p.field_id))
  const heat = useHeatSummary()
  const heatScenes = useMemo(() => heatScenesFor(heat, p.field_id), [heat, p.field_id])
  // Crop reported for each year (one letter per year), for the bands behind the greenness line.
  const crops = useMemo(
    () => [...p.crop_sequence].map((letter, i) => ({ year: p.crop_sequence_first_year + i, letter: toCropLetter(letter) })),
    [p.crop_sequence, p.crop_sequence_first_year],
  )
  // What the map can offer to open when one of its layers has nothing to draw.
  const viewerHas = { greenness: ndvi.status !== 'missing', heat: heatScenes.length > 0 }

  return (
    <div className="flex flex-col gap-4 p-4 lg:fixed lg:inset-0 lg:block lg:p-0">
      <h1 className="sr-only">{t('My field')}</h1>
      <div className="order-2 min-w-0 lg:absolute lg:inset-0">
        <FieldMap
          fields={data.fields}
          counties={data.counties}
          selected={selected}
          onSelect={onSelect}
          viewerHas={viewerHas}
          onOpenViewer={setViewer}
        />
      </div>
      <div className="pw-glass pw-scroll order-1 min-w-0 rounded-[28px] p-4 lg:absolute lg:bottom-4 lg:left-4 lg:top-[88px] lg:z-[1001] lg:w-[304px] lg:overflow-y-auto">
        <FieldList data={data} selectedId={p.field_id} onSelect={onSelect} />
      </div>
      {/* key: when another field is selected the card remounts and rises in softly (pw-rise) */}
      <div
        key={p.field_id}
        className="pw-rise pw-scroll order-3 min-w-0 lg:absolute lg:bottom-4 lg:right-4 lg:top-[88px] lg:z-[1001] lg:w-[380px] lg:overflow-y-auto xl:w-[420px] lg:rounded-[28px] lg:shadow-lift"
      >
        <FieldCard data={data} field={selected} ndvi={ndvi} heatScenes={heatScenes} onOpenViewer={setViewer} />
      </div>
      <FieldViewer
        tab={viewer}
        onTab={setViewer}
        onClose={() => setViewer(null)}
        field={selected}
        hasAerial={hasAerial}
        ndvi={ndvi}
        heatScenes={heatScenes}
        crops={crops}
      />
    </div>
  )
}
