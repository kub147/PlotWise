// Two images in the field card: aerial photo (NAIP) and surface temperature map (ECOSTRESS).
// When the repo has no image for a field we say so instead of showing a stand-in.
import { useState } from 'react'
import { imageUrl, type HeatScene, type HeatSummary } from '@/lib/fieldMedia'
import { useDateLocale, useT } from '@/lib/i18n'
import { cToF, formatNumber } from '@/lib/units'

function Missing({ children }: { children: string }) {
  return (
    <div className="flex aspect-square items-center justify-center rounded-2xl bg-foreground/[0.05] px-3 text-center text-[13px] text-muted-foreground">
      {children}
    </div>
  )
}

// Thumbnail linking to the full image in a new tab.
function Thumbnail({ file, alt }: { file: string; alt: string }) {
  return (
    <a href={imageUrl(file)} target="_blank" rel="noreferrer" className="pw-press block overflow-hidden rounded-2xl">
      <img src={imageUrl(file)} alt={alt} loading="lazy" className="aspect-square w-full object-cover" />
    </a>
  )
}

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

const fahrenheit = (celsius: number) => `${formatNumber(cToF(celsius))}°F`

type FieldPhotosProps = {
  fieldId: string
  fieldLabel: string
  hasAerial: boolean
  heat: HeatSummary | null
}

export function FieldPhotos({ fieldId, fieldLabel, hasAerial, heat }: FieldPhotosProps) {
  // Scenes that contain this field, newest first.
  const scenes = (heat?.scenes ?? [])
    .filter((scene) => fieldId in scene.fields)
    .sort((a, b) => b.time_utc.localeCompare(a.time_utc))
  const [sceneId, setSceneId] = useState<string | null>(null)
  const scene = scenes.find((candidate) => candidate.scene === sceneId) ?? scenes[0]
  const onField = scene?.fields[fieldId]
  const selectId = `heat-scene-${fieldId}`
  const t = useT()
  const locale = useDateLocale()

  return (
    <div>
      <div className="grid grid-cols-2 gap-3">
        <figure>
          {hasAerial ? (
            <Thumbnail file={`field_${fieldId}_naip.png`} alt={t('Aerial photo of {field}', { field: fieldLabel })} />
          ) : (
            <Missing>{t('No aerial photo for this field yet.')}</Missing>
          )}
          <figcaption className="mt-1.5 text-[13px] text-muted-foreground">{t('Aerial photo (USDA NAIP)')}</figcaption>
        </figure>
        <figure>
          {scene ? (
            <Thumbnail
              file={scene.image.split('/').pop() ?? scene.image}
              alt={t('Surface heat map of the area around Tribune on {date}; blue is cooler, red is hotter', { date: sceneDate(scene, locale) })}
            />
          ) : (
            <Missing>{t('No surface heat image for this field yet.')}</Missing>
          )}
          <figcaption className="mt-1.5 text-[13px] text-muted-foreground">{t('Surface heat (NASA ECOSTRESS)')}</figcaption>
        </figure>
      </div>

      {scene && onField && (
        <div className="mt-3">
          <label htmlFor={selectId} className="text-[13px] font-semibold">
            {t('Heat image from')}
          </label>
          <select
            id={selectId}
            value={scene.scene}
            onChange={(event) => setSceneId(event.target.value)}
            className="mt-1 block min-h-11 w-full rounded-md border border-input bg-card px-3 text-[15px]"
          >
            {scenes.map((option) => (
              <option key={option.scene} value={option.scene}>
                {t('{date}, around {time} sun time', { date: sceneDate(option, locale), time: clockTime(option.local_solar_time, locale) })}
              </option>
            ))}
          </select>

          <p className="mt-3 text-[15px] leading-snug">
            {t('At that moment the ground on this field was')}{' '}
            <span className="font-mono font-semibold">{fahrenheit(onField.lst_c)}</span>
            {t(', with {crop} on it.', { crop: t(onField.crop) })}
          </p>
          <p className="mt-2 text-[13px] text-muted-foreground">{t('Average for the whole area at that moment:')}</p>
          <ul className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-[13px]">
            {Object.entries(scene.by_crop_class).map(([crop, value]) => (
              <li key={crop} className="flex justify-between gap-2">
                {/* The key can be long: "winter wheat (ripe in June, stubble from July)" -> crop name only */}
                <span className="capitalize">{t(crop.split(' (')[0])}</span>
                <span className="font-mono font-medium">{fahrenheit(value.mean_c)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
            {t('On the map blue is cooler (about {low}) and red is hotter (about {high}); black outlines are the demo fields. This is the temperature of the ground surface, not of the air, at one moment in the day.', {
              low: fahrenheit(scene.colour_scale_c[0]),
              high: fahrenheit(scene.colour_scale_c[1]),
            })}
          </p>
        </div>
      )}
    </div>
  )
}
