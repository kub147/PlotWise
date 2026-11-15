// Popup with the three views of the selected field from above: the aerial photo (NAIP), field greenness over the
// years (Landsat NDVI) and surface heat (ECOSTRESS). It opens from the tiles in the field card and from the map's
// layer note, so nobody has to scroll the card to find the images.
// A native <dialog> opened with showModal(): the browser keeps focus inside, closes it on Escape and gives the focus
// back to the tile that opened it. On a phone it is a sheet that rises from the bottom.
import { X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { CropLegend } from '@/components/CropTile'
import { GreennessChart, type CropYear } from '@/components/field/GreennessChart'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { fieldShortName, type FieldFeature } from '@/lib/data'
import {
  imageUrl,
  VIEWER_TAB_SHORT,
  type HeatScene,
  type NdviState,
  type ViewerTab,
} from '@/lib/fieldMedia'
import { useDateLocale, useT, useTempUnit } from '@/lib/i18n'
import type { CropLetter } from '@/lib/rotation'
import { formatTemp } from '@/lib/units'

// "2023-07-30 20:08" -> "Jul 30, 2023"
function sceneDate(scene: HeatScene, locale: string) {
  const date = new Date(`${scene.time_utc.slice(0, 10)}T00:00:00Z`)
  return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' })
}

// "13:20" -> "1:20 pm" in English; Polish keeps the 24-hour clock.
function clockTime(time: string, locale: string) {
  if (locale === 'pl-PL') return time
  const [hour, minute] = time.split(':').map(Number)
  return `${((hour + 11) % 12) + 1}:${String(minute).padStart(2, '0')} ${hour < 12 ? 'am' : 'pm'}`
}

// The colours of the heat images (matplotlib RdYlBu, reversed): blue is cool, red is hot.
const HEAT_SCALE = 'linear-gradient(to right, #313695, #74add1, #e0f3f8, #ffffbf, #fdae61, #f46d43, #a50026)'

// Picture that fills the free height of the popup without being cropped; a click opens the file itself.
function LargeImage({ file, alt }: { file: string; alt: string }) {
  const t = useT()
  return (
    <a
      href={imageUrl(file)}
      target="_blank"
      rel="noreferrer"
      title={t('Open the full-size image in a new tab')}
      // Phone: the picture takes the full width of the sheet. Wide screen: it fits into the free height, uncropped.
      className="block shrink-0 overflow-hidden rounded-2xl bg-foreground/[0.05] lg:flex lg:min-h-0 lg:flex-1 lg:shrink lg:items-center lg:justify-center"
    >
      <img src={imageUrl(file)} alt={alt} className="block w-full lg:w-auto lg:max-h-full lg:max-w-full lg:object-contain" />
    </a>
  )
}

function AerialPanel({ field }: { field: FieldFeature }) {
  const t = useT()
  const p = field.properties
  return (
    <figure className="flex shrink-0 flex-col gap-3 lg:min-h-0 lg:flex-1 lg:shrink">
      <LargeImage file={`field_${p.field_id}_naip.png`} alt={t('Aerial photo of {field}', { field: fieldShortName(p) })} />
      <figcaption className="max-w-[75ch] text-[13px] leading-snug text-muted-foreground">
        {t('Aerial photo from the USDA NAIP program. The yellow line is the boundary of this field.')}
      </figcaption>
    </figure>
  )
}

function GreennessPanel({ field, ndvi, crops }: { field: FieldFeature; ndvi: NdviState; crops: CropYear[] }) {
  const t = useT()
  const p = field.properties
  const letters = (['W', 'S', 'C', 'F', 'O'] as CropLetter[]).filter((letter) => crops.some((crop) => crop.letter === letter))
  return (
    <div className="flex shrink-0 flex-col gap-3">
      <p className="max-w-[75ch] text-[15px] leading-snug">
        {t('How green the field was on every clear satellite pass. Peaks are growing crops; the low stretches are bare ground.')}
      </p>
      <GreennessChart fieldId={p.field_id} state={ndvi} threshold={p.ndvi_bare_threshold} crops={crops} wide />
      {letters.length > 0 && <CropLegend letters={letters} />}
    </div>
  )
}

// What stood on the ground at the date of the image: winter wheat is harvested in June, so from July it is stubble.
function cropAtScene(crop: string, scene: HeatScene, t: (text: string) => string) {
  const name = crop.split(' (')[0]
  const month = Number(scene.time_utc.slice(5, 7))
  if (name === 'winter wheat' && month >= 7) return t('wheat stubble after the June harvest')
  if (name === 'fallow') return t('field in fallow')
  return t(name)
}

function HeatPanel({ field, scenes }: { field: FieldFeature; scenes: HeatScene[] }) {
  const t = useT()
  const unit = useTempUnit()
  const temp = (celsius: number) => formatTemp(celsius, unit)
  const locale = useDateLocale()
  const fieldId = field.properties.field_id
  const [sceneId, setSceneId] = useState<string | null>(null)
  const scene = scenes.find((candidate) => candidate.scene === sceneId) ?? scenes[0]
  const onField = scene.fields[fieldId]
  const selectId = `heat-scene-${fieldId}`

  return (
    // Phone: image, scale and text stack and the sheet scrolls. Wide screen: image on the left fills the height.
    <div className="flex shrink-0 flex-col gap-5 lg:min-h-0 lg:flex-1 lg:shrink lg:flex-row">
      <figure className="flex shrink-0 flex-col gap-3 lg:min-h-0 lg:flex-1 lg:shrink">
        <LargeImage
          file={scene.image.split('/').pop() ?? scene.image}
          alt={t('Surface heat map of the area around Tribune on {date}; blue is cooler, red is hotter', { date: sceneDate(scene, locale) })}
        />
        {/* Colour scale of the image, with the two ends in degrees */}
        <figcaption className="flex items-center gap-3 text-[13px] text-muted-foreground">
          <span className="font-mono font-medium text-foreground">{temp(scene.colour_scale_c[0])}</span>
          <span aria-hidden className="h-2.5 flex-1 rounded-full" style={{ background: HEAT_SCALE }} />
          <span className="font-mono font-medium text-foreground">{temp(scene.colour_scale_c[1])}</span>
        </figcaption>
      </figure>

      <div className="shrink-0 lg:w-[340px]">
        <label htmlFor={selectId} className="text-[13px] font-semibold">
          {t('Heat image from')}
        </label>
        <select
          id={selectId}
          value={scene.scene}
          onChange={(event) => setSceneId(event.target.value)}
          className="mt-1 block min-h-11 w-full rounded-xl border border-input bg-card px-3 text-[15px]"
        >
          {scenes.map((option) => (
            <option key={option.scene} value={option.scene}>
              {t('{date}, around {time} local solar time', { date: sceneDate(option, locale), time: clockTime(option.local_solar_time, locale) })}
            </option>
          ))}
        </select>

        {onField && (
          <p className="mt-4 text-[15px] leading-snug">
            {t('At that moment the ground on this field was')}{' '}
            <span className="font-mono font-semibold">{temp(onField.lst_c)}</span>
            {t(' ({crop}).', { crop: cropAtScene(onField.crop, scene, t) })}
          </p>
        )}
        <p className="mt-4 text-[13px] text-muted-foreground">{t('Average ground temperature by land use in this image:')}</p>
        <ul className="mt-1.5 flex flex-col gap-1 text-[13px]">
          {Object.entries(scene.by_crop_class).map(([crop, value]) => (
            <li key={crop} className="flex justify-between gap-2">
              {/* The key can be long: "winter wheat (ripe in June, stubble from July)" -> what stands there at that date */}
              <span className="inline-block first-letter:uppercase">{cropAtScene(crop, scene, t)}</span>
              <span className="font-mono font-medium">{temp(value.mean_c)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-[13px] leading-snug text-muted-foreground">
          {t('On the map blue is cooler (about {low}) and red is hotter (about {high}); black outlines are the demo fields. This is the temperature of the ground surface, not of the air, at one moment in the day.', {
            low: temp(scene.colour_scale_c[0]),
            high: temp(scene.colour_scale_c[1]),
          })}
        </p>
      </div>
    </div>
  )
}

type FieldViewerProps = {
  // Which view is open; null when the popup is closed.
  tab: ViewerTab | null
  onTab: (tab: ViewerTab) => void
  onClose: () => void
  field: FieldFeature
  hasAerial: boolean
  ndvi: NdviState
  heatScenes: HeatScene[]
  crops: CropYear[]
}

export function FieldViewer({ tab, onTab, onClose, field, hasAerial, ndvi, heatScenes, crops }: FieldViewerProps) {
  const t = useT()
  const dialog = useRef<HTMLDialogElement>(null)
  // The view stays drawn while the popup fades out, so the last one is remembered after `tab` goes back to null.
  const [shown, setShown] = useState<ViewerTab>(tab ?? 'aerial')
  if (tab && tab !== shown) setShown(tab)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (tab && !element.open) element.showModal()
    if (!tab && element.open) element.close()
  }, [tab])

  // On a phone the page behind must not scroll under the sheet.
  useEffect(() => {
    if (!tab) return
    const root = document.documentElement
    const before = root.style.overflow
    root.style.overflow = 'hidden'
    return () => {
      root.style.overflow = before
    }
  }, [tab])

  const available: Record<ViewerTab, boolean> = {
    aerial: hasAerial,
    greenness: ndvi.status !== 'missing',
    heat: heatScenes.length > 0,
  }
  const tabs = (['aerial', 'greenness', 'heat'] as ViewerTab[]).filter((candidate) => available[candidate])
  const active = available[shown] ? shown : tabs[0]
  const p = field.properties

  return (
    <dialog
      ref={dialog}
      aria-labelledby="field-viewer-title"
      className="pw-dialog"
      onClose={onClose}
      // The dialog box is filled by its content, so a click that lands on the dialog itself is a click on the backdrop.
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className="flex h-full flex-col bg-card">
        <header className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-border px-5 py-4 lg:px-6">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[13px] font-medium text-muted-foreground">{fieldShortName(p)}</p>
            <h2 id="field-viewer-title" className="text-[19px] font-semibold leading-tight">
              {t('This field from above')}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('Close')}
            className="pw-press order-2 flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-foreground/[0.06] hover:bg-foreground/10 lg:order-3"
          >
            <X aria-hidden className="h-5 w-5" strokeWidth={2} />
          </button>
          {tabs.length > 1 && (
            <div className="order-3 w-full lg:order-2 lg:w-auto">
              {/* Phone: the tabs span the sheet; wide screen: they sit beside the title */}
              <SegmentedControl
                label={t('View')}
                options={tabs.map((value) => ({ value, label: t(VIEWER_TAB_SHORT[value]) }))}
                value={active}
                onValueChange={onTab}
                frameClassName="block lg:inline-block"
                className="min-w-full lg:min-w-0"
              />
            </div>
          )}
        </header>

        <div className="pw-scroll flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain px-5 py-5 lg:px-6">
          {active === 'aerial' && <AerialPanel field={field} />}
          {active === 'greenness' && <GreennessPanel field={field} ndvi={ndvi} crops={crops} />}
          {active === 'heat' && <HeatPanel key={p.field_id} field={field} scenes={heatScenes} />}
        </div>
      </div>
    </dialog>
  )
}
